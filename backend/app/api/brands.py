"""
Pulse — Brand Management API
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select, func
from typing import List
from datetime import date
import uuid

from app.db.database import get_db
from app.db.models import Brand, BrandGuideline, Post
from app.models.schemas import (
    BrandCreate, BrandResponse, BrandGuidelineCreate,
    StructuralProfile, PostIngest, BulkIngestRequest
)
from app.services.voice_engine import VoiceEngine
from app.services.eqi import EQIService

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.post("", response_model=BrandResponse)
async def create_brand(brand_data: BrandCreate, db: AsyncSession = Depends(get_db)):
    """Create a new brand profile."""
    brand = Brand(
        id=str(uuid.uuid4()),
        name=brand_data.name,
        handle=brand_data.handle,
        platform=brand_data.platform,
        description=brand_data.description,
        weekly_post_limit=brand_data.weekly_post_limit,
    )
    db.add(brand)
    await db.flush()
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        handle=brand.handle,
        platform=brand.platform,
        description=brand.description,
        weekly_post_limit=brand.weekly_post_limit,
        post_count=0,
        created_at=brand.created_at,
    )


@router.get("", response_model=List[BrandResponse])
async def list_brands(db: AsyncSession = Depends(get_db)):
    """List all brands."""
    result = await db.execute(select(Brand))
    brands = result.scalars().all()
    
    responses = []
    for brand in brands:
        post_count_result = await db.execute(
            select(func.count(Post.id)).where(Post.brand_id == brand.id)
        )
        post_count = post_count_result.scalar() or 0
        
        structural = None
        if brand.avg_sentence_length is not None:
            structural = StructuralProfile(
                avg_sentence_length=brand.avg_sentence_length,
                emoji_frequency=brand.emoji_frequency,
                emoji_placement=brand.emoji_placement,
                hashtag_count_avg=brand.hashtag_count_avg,
                hashtag_placement=brand.hashtag_placement,
                avg_post_length=brand.avg_post_length,
                tone_keywords=brand.tone_keywords,
            )
        
        responses.append(BrandResponse(
            id=brand.id,
            name=brand.name,
            handle=brand.handle,
            platform=brand.platform,
            description=brand.description,
            weekly_post_limit=brand.weekly_post_limit,
            structural_profile=structural,
            post_count=post_count,
            created_at=brand.created_at,
        ))
    
    return responses


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: str, db: AsyncSession = Depends(get_db)):
    """Get brand details including structural profile."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    post_count_result = await db.execute(
        select(func.count(Post.id)).where(Post.brand_id == brand_id)
    )
    post_count = post_count_result.scalar() or 0
    
    structural = None
    if brand.avg_sentence_length is not None:
        structural = StructuralProfile(
            avg_sentence_length=brand.avg_sentence_length,
            emoji_frequency=brand.emoji_frequency,
            emoji_placement=brand.emoji_placement,
            hashtag_count_avg=brand.hashtag_count_avg,
            hashtag_placement=brand.hashtag_placement,
            avg_post_length=brand.avg_post_length,
            tone_keywords=brand.tone_keywords,
        )
    
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        handle=brand.handle,
        platform=brand.platform,
        description=brand.description,
        weekly_post_limit=brand.weekly_post_limit,
        structural_profile=structural,
        post_count=post_count,
        created_at=brand.created_at,
    )


@router.post("/{brand_id}/guidelines")
async def add_guideline(brand_id: str, guideline: BrandGuidelineCreate, db: AsyncSession = Depends(get_db)):
    """Add a brand guideline with temporal validity."""
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    gl = BrandGuideline(
        id=str(uuid.uuid4()),
        brand_id=brand_id,
        title=guideline.title,
        content=guideline.content,
        category=guideline.category,
        valid_from=guideline.valid_from or date.today(),
        valid_to=guideline.valid_to,
    )
    db.add(gl)
    
    return {"status": "created", "id": gl.id}


@router.get("/{brand_id}/guidelines")
async def get_guidelines(brand_id: str, active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """Get brand guidelines, optionally filtered to currently active ones."""
    query = select(BrandGuideline).where(BrandGuideline.brand_id == brand_id)
    
    if active_only:
        today = date.today()
        query = query.where(
            BrandGuideline.valid_from <= today,
            (BrandGuideline.valid_to == None) | (BrandGuideline.valid_to >= today)
        )
    
    result = await db.execute(query)
    guidelines = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "title": g.title,
            "content": g.content,
            "category": g.category,
            "valid_from": g.valid_from.isoformat() if g.valid_from else None,
            "valid_to": g.valid_to.isoformat() if g.valid_to else None,
        }
        for g in guidelines
    ]


@router.post("/{brand_id}/ingest")
async def ingest_posts(brand_id: str, request: BulkIngestRequest, db: AsyncSession = Depends(get_db)):
    """
    Ingest sample posts and compute brand voice profile.
    This is the entry point for brand voice learning (§7.4).
    """
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Store posts and compute embeddings
    embeddings = []
    post_texts = []
    
    for post_data in request.posts:
        embedding = VoiceEngine.compute_embedding(post_data.content)
        eqi = EQIService.compute_eqi(
            likes=post_data.likes,
            comments=post_data.comments_count,
            shares=post_data.shares,
            saves=post_data.saves,
            impressions=post_data.impressions,
            reach=post_data.reach,
            platform=post_data.platform,
        )
        
        # Extract hook (first line)
        hook = post_data.content.split("\n")[0].strip()
        
        post = Post(
            id=str(uuid.uuid4()),
            brand_id=brand_id,
            platform=post_data.platform,
            content=post_data.content,
            post_type=post_data.post_type,
            embedding=embedding,
            likes=post_data.likes,
            comments_count=post_data.comments_count,
            shares=post_data.shares,
            saves=post_data.saves,
            impressions=post_data.impressions,
            reach=post_data.reach,
            eqi_score=eqi,
            hook_text=hook,
            posted_at=post_data.posted_at,
        )
        db.add(post)
        embeddings.append(embedding)
        post_texts.append(post_data.content)
    
    # Compute voice centroid
    centroid = VoiceEngine.compute_centroid(embeddings)
    brand.voice_centroid = centroid
    
    # Compute and cache structural profile
    profile = VoiceEngine.compute_structural_profile(post_texts)
    brand.avg_sentence_length = profile.get("avg_sentence_length")
    brand.emoji_frequency = profile.get("emoji_frequency")
    brand.emoji_placement = profile.get("emoji_placement")
    brand.hashtag_count_avg = profile.get("hashtag_count_avg")
    brand.hashtag_placement = profile.get("hashtag_placement")
    brand.avg_post_length = profile.get("avg_post_length")
    brand.tone_keywords = profile.get("tone_keywords")
    
    await db.flush()
    
    return {
        "status": "ingested",
        "posts_count": len(request.posts),
        "voice_centroid_computed": True,
        "structural_profile": profile,
    }
