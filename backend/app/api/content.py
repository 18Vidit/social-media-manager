"""
Pulse — Content Generation API
Trigger the full generation pipeline and manage drafts.
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import date
import uuid

from app.db.database import get_db
from app.db.models import Brand, BrandGuideline, Post, GeneratedDraft, ScheduledPost
from app.models.schemas import (
    ContentGenerateRequest, DraftResponse, DraftApproval, DraftRejection
)
from app.agents.graph import PulseGraph
from app.services.eqi import EQIService
from app.db.seed_data import ENGAGEMENT_HEATMAP

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/generate")
async def generate_content(request: ContentGenerateRequest, db: AsyncSession = Depends(get_db)):
    """
    Trigger the full content generation pipeline (§7.5):
    Scout → Strategist → Copywriter → Guardrail → Rank+Explain
    
    Returns 3 variants with voice similarity scores, explanations, and recommended posting time.
    """
    # Load brand context
    brand_result = await db.execute(select(Brand).where(Brand.id == request.brand_id))
    brand = brand_result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get few-shot posts (top-quartile by EQI)
    posts_result = await db.execute(
        select(Post)
        .where(Post.brand_id == request.brand_id)
        .order_by(desc(Post.eqi_score))
    )
    all_posts = posts_result.scalars().all()
    
    # Filter to top quartile
    quartile_cutoff = max(1, len(all_posts) // 4)
    top_posts = all_posts[:quartile_cutoff] if all_posts else []
    
    few_shot_posts = [
        {
            "content": p.content,
            "hook_text": p.hook_text,
            "eqi_score": p.eqi_score,
            "post_type": p.post_type,
            "likes": p.likes,
            "comments_count": p.comments_count,
            "shares": p.shares,
            "saves": p.saves,
        }
        for p in top_posts
    ]
    
    # Get active guidelines
    today = date.today()
    guidelines_result = await db.execute(
        select(BrandGuideline)
        .where(
            BrandGuideline.brand_id == request.brand_id,
            BrandGuideline.valid_from <= today,
            (BrandGuideline.valid_to == None) | (BrandGuideline.valid_to >= today)
        )
    )
    guidelines = [g.content for g in guidelines_result.scalars().all()]
    
    # Build structural profile
    structural_profile = {}
    if brand.avg_sentence_length is not None:
        structural_profile = {
            "avg_sentence_length": brand.avg_sentence_length,
            "emoji_frequency": brand.emoji_frequency,
            "emoji_placement": brand.emoji_placement,
            "hashtag_count_avg": brand.hashtag_count_avg,
            "hashtag_placement": brand.hashtag_placement,
            "avg_post_length": brand.avg_post_length,
            "tone_keywords": brand.tone_keywords,
        }
    
    # Voice centroid
    voice_centroid = list(brand.voice_centroid) if brand.voice_centroid is not None else None
    
    # Run the pipeline
    result = await PulseGraph.run_content_generation(
        brand_id=request.brand_id,
        topic=request.topic,
        platform=request.platform,
        tone=request.tone,
        additional_context=request.additional_context,
        brand_name=brand.name,
        few_shot_posts=few_shot_posts,
        structural_profile=structural_profile,
        brand_guidelines=guidelines,
        voice_centroid=voice_centroid,
        engagement_data=ENGAGEMENT_HEATMAP,  # Use seeded data for demo
    )
    
    # Store drafts in DB
    drafts = []
    for i, variant in enumerate(result["variants"]):
        draft = GeneratedDraft(
            id=str(uuid.uuid4()),
            brand_id=request.brand_id,
            topic=request.topic,
            platform=request.platform,
            hook=variant["hook"],
            content=variant["content"],
            hashtags=variant["hashtags"],
            variant_index=i,
            voice_similarity=variant["voice_similarity"],
            slop_score=variant["slop_score"],
            predicted_engagement=variant.get("structural_match", 0) * 100,
            explanation=variant["explanation"],
            pipeline_trace=variant["pipeline_trace"],
            status="pending",
            recommended_time=result["recommended_time"].get("datetime") if isinstance(result.get("recommended_time"), dict) else None,
            recommended_time_reason=result["recommended_time"].get("reason") if isinstance(result.get("recommended_time"), dict) else None,
        )
        db.add(draft)
        drafts.append(draft)
    
    await db.flush()
    
    return {
        "status": "generated",
        "drafts": [
            {
                "id": d.id,
                "variant_index": d.variant_index,
                "hook": d.hook,
                "content": d.content,
                "hashtags": d.hashtags,
                "voice_similarity": d.voice_similarity,
                "slop_score": d.slop_score,
                "predicted_engagement": d.predicted_engagement,
                "explanation": d.explanation,
                "recommended_time": d.recommended_time.isoformat() if d.recommended_time else None,
                "recommended_time_reason": d.recommended_time_reason,
            }
            for d in drafts
        ],
        "recommended_time": {
            "datetime": result["recommended_time"].get("datetime").isoformat() if isinstance(result["recommended_time"].get("datetime"), object) and hasattr(result["recommended_time"].get("datetime"), 'isoformat') else str(result["recommended_time"].get("datetime", "")),
            "reason": result["recommended_time"].get("reason", ""),
            "method": result.get("recommendation_method", "heuristic"),
        },
        "trends": result.get("trends", []),
        "pipeline_trace": result.get("trace", []),
        "total_duration_ms": result.get("total_duration_ms", 0),
    }


@router.get("/drafts")
async def list_drafts(
    brand_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List generated drafts, optionally filtered."""
    query = select(GeneratedDraft).order_by(desc(GeneratedDraft.created_at))
    
    if brand_id:
        query = query.where(GeneratedDraft.brand_id == brand_id)
    if status:
        query = query.where(GeneratedDraft.status == status)
    
    result = await db.execute(query)
    drafts = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "brand_id": d.brand_id,
            "topic": d.topic,
            "platform": d.platform,
            "hook": d.hook,
            "content": d.content,
            "hashtags": d.hashtags,
            "variant_index": d.variant_index,
            "voice_similarity": d.voice_similarity,
            "slop_score": d.slop_score,
            "predicted_engagement": d.predicted_engagement,
            "explanation": d.explanation,
            "pipeline_trace": d.pipeline_trace,
            "status": d.status,
            "recommended_time": d.recommended_time.isoformat() if d.recommended_time else None,
            "recommended_time_reason": d.recommended_time_reason,
            "created_at": d.created_at.isoformat(),
        }
        for d in drafts
    ]


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: str, approval: DraftApproval, db: AsyncSession = Depends(get_db)):
    """Approve a draft and optionally schedule it."""
    result = await db.execute(select(GeneratedDraft).where(GeneratedDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    draft.status = "approved"
    
    # Schedule if time provided or use recommended time
    scheduled_time = approval.scheduled_time or draft.recommended_time
    
    if scheduled_time:
        scheduled = ScheduledPost(
            id=str(uuid.uuid4()),
            brand_id=draft.brand_id,
            draft_id=draft.id,
            platform=draft.platform,
            scheduled_at=scheduled_time,
            status="scheduled",
        )
        db.add(scheduled)
        await db.flush()
        
        return {
            "status": "approved_and_scheduled",
            "draft_id": draft.id,
            "scheduled_post_id": scheduled.id,
            "scheduled_at": scheduled_time.isoformat(),
        }
    
    return {"status": "approved", "draft_id": draft.id}


@router.post("/drafts/{draft_id}/reject")
async def reject_draft(draft_id: str, rejection: DraftRejection, db: AsyncSession = Depends(get_db)):
    """Reject a draft with feedback."""
    result = await db.execute(select(GeneratedDraft).where(GeneratedDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    draft.status = "rejected"
    draft.rejection_reason = rejection.reason
    
    return {"status": "rejected", "draft_id": draft.id, "reason": rejection.reason}
