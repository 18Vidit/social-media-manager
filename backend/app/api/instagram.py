"""
Pulse — Instagram API Endpoints
Connect real Instagram accounts, sync real posts & comments, publish drafts, and send replies.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime
import uuid
import logging

from app.db.database import get_db
from app.db.models import Brand, Post, Comment, AutoReply, GeneratedDraft, ScheduledPost
from app.models.schemas import (
    InstagramConnectRequest,
    InstagramSyncRequest,
    InstagramPublishRequest,
    InstagramReplyRequest,
    InstagramStatusResponse,
)
from app.services.instagram_service import InstagramService
from app.services.voice_engine import VoiceEngine
from app.services.eqi import EQIService
from app.agents.sentinel import SentinelAgent

logger = logging.getLogger("pulse.instagram_api")

router = APIRouter(prefix="/api/instagram", tags=["instagram"])


@router.get("/status")
async def get_instagram_status(
    brand_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get current Instagram connection status and sync metrics."""
    # If no brand_id, fetch the first brand
    if brand_id:
        result = await db.execute(select(Brand).where(Brand.id == brand_id))
    else:
        result = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))
    
    brand = result.scalar_one_or_none()
    
    if not brand or not brand.is_instagram_connected or not brand.instagram_access_token:
        return InstagramStatusResponse(
            connected=False,
            synced_posts_count=0,
            synced_comments_count=0,
        )

    # Count synced posts and comments
    posts_res = await db.execute(
        select(func.count(Post.id)).where(Post.brand_id == brand.id)
    )
    posts_count = posts_res.scalar() or 0

    comments_res = await db.execute(
        select(func.count(Comment.id)).where(Comment.brand_id == brand.id)
    )
    comments_count = comments_res.scalar() or 0

    return InstagramStatusResponse(
        connected=True,
        account_id=brand.instagram_account_id,
        username=brand.handle.replace("@", "") if brand.handle else "instagram_user",
        name=brand.name,
        profile_picture_url=brand.instagram_profile_pic,
        followers_count=brand.instagram_followers_count or 0,
        media_count=posts_count,
        biography=brand.instagram_bio or brand.description or "",
        last_synced_at=brand.instagram_last_synced_at.isoformat() if brand.instagram_last_synced_at else None,
        synced_posts_count=posts_count,
        synced_comments_count=comments_count,
    )


@router.post("/connect")
async def connect_instagram(
    request: InstagramConnectRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Connect an Instagram account by verifying access token and discovering profile.
    Automatically seeds brand voice and posts if auto_sync is enabled.
    """
    token = request.access_token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Access token is required")

    # Step 1: Verify token with Meta Graph API
    discovery = await InstagramService.verify_token_and_get_account(
        access_token=token,
        account_id=request.account_id,
    )

    if not discovery.get("success"):
        err_detail = discovery.get("error", "Failed to verify Instagram access token with Meta API.")
        raise HTTPException(
            status_code=400,
            detail=f"Instagram connection failed: {err_detail}. Make sure your token has permissions: instagram_basic, pages_show_list, pages_read_engagement.",
        )

    account_id = discovery.get("account_id") or "me"
    username = discovery.get("username", "instagram_user")
    name = discovery.get("name", username)
    profile_pic = discovery.get("profile_picture_url")
    followers = discovery.get("followers_count", 0)
    bio = discovery.get("biography", "")

    # Step 2: Find or create Brand
    brand = None
    if request.brand_id:
        res = await db.execute(select(Brand).where(Brand.id == request.brand_id))
        brand = res.scalar_one_or_none()

    if not brand:
        # Check if a brand exists, otherwise create new
        res = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))
        brand = res.scalar_one_or_none()

    if not brand:
        brand = Brand(
            id=str(uuid.uuid4()),
            name=name,
            handle=f"@{username}",
            platform="instagram",
            description=bio or f"Official Instagram account of {name}",
        )
        db.add(brand)
    else:
        brand.name = name
        brand.handle = f"@{username}"
        brand.description = bio or brand.description

    # Update Instagram connection attributes
    brand.is_instagram_connected = True
    brand.instagram_account_id = str(account_id)
    brand.instagram_access_token = token
    brand.instagram_profile_pic = profile_pic
    brand.instagram_bio = bio
    brand.instagram_followers_count = followers
    brand.instagram_connected_at = datetime.utcnow()

    await db.flush()

    # Step 3: Trigger auto-sync if requested
    posts_synced = 0
    comments_synced = 0
    if request.auto_sync:
        sync_result = await _perform_instagram_sync(brand, db, limit=20)
        posts_synced = sync_result.get("posts_synced", 0)
        comments_synced = sync_result.get("comments_synced", 0)

    await db.commit()

    return {
        "status": "connected",
        "brand_id": brand.id,
        "account": {
            "id": brand.instagram_account_id,
            "username": username,
            "name": name,
            "profile_picture_url": profile_pic,
            "followers_count": followers,
            "biography": bio,
        },
        "posts_synced": posts_synced,
        "comments_synced": comments_synced,
    }


@router.post("/sync")
async def sync_instagram(
    request: InstagramSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Pull live posts and comments from connected Instagram account,
    compute embeddings, calculate EQI scores, update voice centroid & structural profile,
    and run Sentinel risk triage on audience comments.
    """
    if request.brand_id:
        res = await db.execute(select(Brand).where(Brand.id == request.brand_id))
    else:
        res = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))
    
    brand = res.scalar_one_or_none()
    if not brand or not brand.is_instagram_connected or not brand.instagram_access_token:
        raise HTTPException(
            status_code=400,
            detail="No connected Instagram account found. Please connect your Instagram account first.",
        )

    result = await _perform_instagram_sync(brand, db, limit=request.limit or 25)
    await db.commit()
    return result


async def _perform_instagram_sync(brand: Brand, db: AsyncSession, limit: int = 25) -> dict:
    """Internal helper to execute Instagram synchronization pipeline."""
    token = brand.instagram_access_token
    account_id = brand.instagram_account_id or "me"

    # 1. Fetch live media posts
    media_items = await InstagramService.fetch_media_posts(
        access_token=token,
        account_id=account_id,
        limit=limit,
    )

    posts_synced = 0
    all_post_texts = []
    all_embeddings = []
    saved_posts = []

    for item in media_items:
        caption = item.get("caption", "").strip()
        if not caption:
            # If image post has no caption, generate a brief placeholder
            caption = f"Instagram update from {brand.handle or 'account'}"

        post_id = item.get("id")
        media_type = (item.get("media_type") or "image").lower()
        media_url = item.get("media_url") or item.get("thumbnail_url")
        permalink = item.get("permalink")
        likes = item.get("like_count", 0)
        comments_count = item.get("comments_count", 0)
        
        # Parse timestamp
        raw_time = item.get("timestamp")
        posted_at = datetime.utcnow()
        if raw_time:
            try:
                posted_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                posted_at = datetime.utcnow()

        # Check if already exists in DB
        existing_res = await db.execute(
            select(Post).where(Post.brand_id == brand.id, Post.platform_post_id == post_id)
        )
        post = existing_res.scalar_one_or_none()

        embedding = VoiceEngine.compute_embedding(caption)
        eqi = EQIService.compute_eqi(
            likes=likes,
            comments=comments_count,
            shares=int(likes * 0.05),
            saves=int(likes * 0.08),
            impressions=max(likes * 10, 100),
            reach=max(likes * 8, 80),
            platform="instagram",
        )
        hook = caption.split("\n")[0].strip()

        if post:
            post.content = caption
            post.likes = likes
            post.comments_count = comments_count
            post.media_url = media_url
            post.permalink = permalink
            post.eqi_score = eqi
            post.embedding = embedding
            post.hook_text = hook
            post.posted_at = posted_at
        else:
            post = Post(
                id=str(uuid.uuid4()),
                brand_id=brand.id,
                platform="instagram",
                platform_post_id=post_id,
                media_url=media_url,
                permalink=permalink,
                content=caption,
                post_type=media_type,
                embedding=embedding,
                likes=likes,
                comments_count=comments_count,
                shares=int(likes * 0.05),
                saves=int(likes * 0.08),
                impressions=max(likes * 10, 100),
                reach=max(likes * 8, 80),
                eqi_score=eqi,
                hook_text=hook,
                posted_at=posted_at,
            )
            db.add(post)
            posts_synced += 1

        all_post_texts.append(caption)
        all_embeddings.append(embedding)
        saved_posts.append(post)

    # 2. Update brand voice centroid and structural profile DNA
    structural_profile = None
    if all_embeddings:
        centroid = VoiceEngine.compute_centroid(all_embeddings)
        brand.voice_centroid = centroid

    if all_post_texts:
        structural_profile = VoiceEngine.compute_structural_profile(all_post_texts)
        brand.avg_sentence_length = structural_profile.get("avg_sentence_length")
        brand.emoji_frequency = structural_profile.get("emoji_frequency")
        brand.emoji_placement = structural_profile.get("emoji_placement")
        brand.hashtag_count_avg = structural_profile.get("hashtag_count_avg")
        brand.hashtag_placement = structural_profile.get("hashtag_placement")
        brand.avg_post_length = structural_profile.get("avg_post_length")
        brand.tone_keywords = structural_profile.get("tone_keywords")

    # 3. Fetch comments on the top recent posts and run Sentinel AI Triage
    comments_synced = 0
    sentinel = SentinelAgent()

    for item in media_items[:5]:  # sync comments on the 5 most recent posts
        post_id = item.get("id")
        if not post_id:
            continue

        raw_comments = await InstagramService.fetch_media_comments(
            access_token=token,
            media_id=post_id,
            limit=15,
        )

        for c_item in raw_comments:
            c_text = c_item.get("text", "").strip()
            if not c_text:
                continue

            author = c_item.get("username") or c_item.get("from", {}).get("username", "user")
            
            # Run AI Sentinel triage
            triage = sentinel.triage_comment(
                text=c_text,
                is_verified=False,
            )

            # Check if comment already in DB
            c_query = await db.execute(
                select(Comment).where(
                    Comment.brand_id == brand.id,
                    Comment.post_id == post_id,
                    Comment.content == c_text,
                )
            )
            if not c_query.scalar_one_or_none():
                comment = Comment(
                    id=str(uuid.uuid4()),
                    brand_id=brand.id,
                    platform="instagram",
                    post_id=post_id,
                    author_username=author,
                    author_is_verified=False,
                    content=c_text,
                    is_dm=False,
                    sentiment_score=triage["sentiment_score"],
                    sentiment_label=triage["sentiment_label"],
                    intent=triage["intent"],
                    intent_confidence=triage["intent_confidence"],
                    brand_risk=triage["brand_risk"],
                    triage_action=triage["triage_action"],
                )
                db.add(comment)
                comments_synced += 1

    brand.instagram_last_synced_at = datetime.utcnow()
    await db.flush()

    return {
        "status": "synced",
        "posts_synced": posts_synced,
        "total_posts_processed": len(media_items),
        "comments_synced": comments_synced,
        "structural_profile": structural_profile,
        "last_synced_at": brand.instagram_last_synced_at.isoformat(),
    }


@router.post("/disconnect")
async def disconnect_instagram(
    brand_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Instagram account and clear stored token."""
    if brand_id:
        res = await db.execute(select(Brand).where(Brand.id == brand_id))
    else:
        res = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))

    brand = res.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    brand.is_instagram_connected = False
    brand.instagram_access_token = None
    await db.commit()

    return {"status": "disconnected", "brand_id": brand.id}


@router.post("/publish")
async def publish_to_instagram(
    request: InstagramPublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """Publish a draft directly to Instagram using the Meta Graph API."""
    if request.brand_id:
        res = await db.execute(select(Brand).where(Brand.id == request.brand_id))
    else:
        res = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))

    brand = res.scalar_one_or_none()
    if not brand or not brand.is_instagram_connected or not brand.instagram_access_token:
        raise HTTPException(
            status_code=400,
            detail="Instagram account is not connected. Please connect Instagram in settings.",
        )

    # Perform publishing via Instagram Graph API
    result = await InstagramService.publish_media(
        access_token=brand.instagram_access_token,
        account_id=brand.instagram_account_id or "me",
        caption=request.caption,
        image_url=request.image_url,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=f"Instagram publish failed: {result.get('error')}",
        )

    # Update draft status if draft_id was provided
    if request.draft_id:
        draft_res = await db.execute(
            select(GeneratedDraft).where(GeneratedDraft.id == request.draft_id)
        )
        draft = draft_res.scalar_one_or_none()
        if draft:
            draft.status = "published"
            
            # Also record in scheduled_posts as published
            scheduled = ScheduledPost(
                id=str(uuid.uuid4()),
                brand_id=brand.id,
                draft_id=draft.id,
                platform="instagram",
                scheduled_at=datetime.utcnow(),
                published_at=datetime.utcnow(),
                status="published",
            )
            db.add(scheduled)

    await db.commit()

    return {
        "status": "published",
        "post_id": result.get("post_id"),
        "permalink": result.get("permalink"),
        "published_at": result.get("published_at"),
    }


@router.post("/reply-comment")
async def reply_comment(
    request: InstagramReplyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reply directly to an Instagram comment."""
    if request.brand_id:
        res = await db.execute(select(Brand).where(Brand.id == request.brand_id))
    else:
        res = await db.execute(select(Brand).order_by(Brand.created_at.desc()).limit(1))

    brand = res.scalar_one_or_none()
    if not brand or not brand.is_instagram_connected or not brand.instagram_access_token:
        raise HTTPException(status_code=400, detail="Instagram account not connected")

    result = await InstagramService.reply_to_comment(
        access_token=brand.instagram_access_token,
        comment_id=request.comment_id,
        message=request.message,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send Instagram reply: {result.get('error')}",
        )

    # Update comment in DB if found
    c_res = await db.execute(
        select(Comment).where(Comment.id == request.comment_id)
    )
    comment = c_res.scalar_one_or_none()
    if comment:
        comment.replied = True
        auto_reply = AutoReply(
            id=str(uuid.uuid4()),
            comment_id=comment.id,
            content=request.message,
            auto_sent=True,
            approved=True,
            sent_at=datetime.utcnow(),
            explanation="Direct reply sent via Instagram API integration",
        )
        db.add(auto_reply)

    await db.commit()

    return {"status": "reply_sent", "reply_id": result.get("reply_id")}
