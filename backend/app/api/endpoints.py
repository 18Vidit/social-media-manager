"""
Pulse — Schedule, Comments, and Analytics API
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import select, desc, func   
from typing import Optional, List
from datetime import datetime
import uuid

from app.db.database import get_db
from app.db.models import (
    Brand, Post, GeneratedDraft, ScheduledPost, 
    Comment, AutoReply, EngagementMetric
)
from app.agents.strategist import StrategistAgent, HeuristicHeatmap
from app.agents.sentinel import SentinelAgent
from app.agents.scout import ScoutAgent
from app.agents.graph import PulseGraph
from app.services.eqi import EQIService
from app.services.mock_platform import MockPlatformAPI
from app.db.seed_data import ENGAGEMENT_HEATMAP, DEMO_COMMENTS

# ──────────────────────────────────────────────
# Schedule Router
# ──────────────────────────────────────────────

schedule_router = APIRouter(prefix="/api/schedule", tags=["schedule"])


@schedule_router.get("/peak-times")
async def get_peak_times(brand_id: Optional[str] = None, platform: str = "instagram"):
    """Get recommended posting windows with heatmap data."""
    strategist = StrategistAgent()
    strategist.seed(ENGAGEMENT_HEATMAP)
    
    return {
        "top_slots": strategist.get_top_slots(n=5),
        "recommendation": strategist.get_recommendation(platform=platform),
        "heatmap": strategist.get_heatmap(),
    }


@schedule_router.get("/upcoming")
async def get_upcoming_posts(brand_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List upcoming scheduled posts."""
    query = select(ScheduledPost).where(
        ScheduledPost.status == "scheduled",
        ScheduledPost.scheduled_at >= datetime.utcnow(),
    ).order_by(ScheduledPost.scheduled_at)
    
    if brand_id:
        query = query.where(ScheduledPost.brand_id == brand_id)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # Load associated drafts
    response = []
    for post in posts:
        draft_result = await db.execute(
            select(GeneratedDraft).where(GeneratedDraft.id == post.draft_id)
        )
        draft = draft_result.scalar_one_or_none()
        
        response.append({
            "id": post.id,
            "brand_id": post.brand_id,
            "platform": post.platform,
            "scheduled_at": post.scheduled_at.isoformat(),
            "status": post.status,
            "paused_by_circuit_breaker": post.paused_by_circuit_breaker,
            "content_preview": draft.content[:200] if draft else None,
            "hook": draft.hook if draft else None,
        })
    
    return response


# ──────────────────────────────────────────────
# Comments Router
# ──────────────────────────────────────────────

comments_router = APIRouter(prefix="/api/comments", tags=["comments"])


@comments_router.get("")
async def list_comments(
    brand_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all comments with classification."""
    query = select(Comment).order_by(desc(Comment.received_at))
    if brand_id:
        query = query.where(Comment.brand_id == brand_id)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "brand_id": c.brand_id,
            "platform": c.platform,
            "author_username": c.author_username,
            "author_is_verified": c.author_is_verified,
            "content": c.content,
            "is_dm": c.is_dm,
            "sentiment_score": c.sentiment_score,
            "sentiment_label": c.sentiment_label,
            "intent": c.intent,
            "intent_confidence": c.intent_confidence,
            "brand_risk": c.brand_risk,
            "triage_action": c.triage_action,
            "replied": c.replied,
            "escalated": c.escalated,
            "received_at": c.received_at.isoformat(),
        }
        for c in comments
    ]


@comments_router.get("/triage")
async def get_triage_view(brand_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Get comments organized by risk matrix quadrant.
    This is the 2×2 grid view from §7.8.
    """
    # Run triage on seeded comments if no DB comments exist
    query = select(Comment)
    if brand_id:
        query = query.where(Comment.brand_id == brand_id)
    
    result = await db.execute(query)
    db_comments = result.scalars().all()
    
    if not db_comments:
        # Use demo comments
        comments_for_triage = [
            {
                "content": c["content"],
                "author_username": c["author"],
                "is_verified": c.get("is_verified", False),
            }
            for c in DEMO_COMMENTS
        ]
    else:
        comments_for_triage = [
            {
                "content": c.content,
                "author_username": c.author_username,
                "is_verified": c.author_is_verified,
                "id": c.id,
            }
            for c in db_comments
        ]
    
    triage_result = await PulseGraph.run_comment_triage(comments_for_triage)
    
    return triage_result


@comments_router.get("/circuit-breaker")
async def check_circuit_breaker(brand_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Check the sentiment circuit breaker status (§6.9)."""
    sentinel = SentinelAgent()
    
    # Get recent sentiment scores
    query = select(Comment.sentiment_score).order_by(desc(Comment.received_at)).limit(20)
    if brand_id:
        query = query.where(Comment.brand_id == brand_id)
    
    result = await db.execute(query)
    sentiments = [r[0] for r in result.all() if r[0] is not None]
    
    # If no DB data, use demo data
    if not sentiments:
        sentiments = [c.get("sentiment", 0) for c in DEMO_COMMENTS]
    
    return sentinel.check_circuit_breaker(sentiments)


# ──────────────────────────────────────────────
# Analytics Router
# ──────────────────────────────────────────────

analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("/dashboard")
async def get_dashboard(brand_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Dashboard overview with engagement metrics, trend deltas, and agent status.
    This is the main landing page data source (§6.2).
    """
    # Get mock account insights
    account = MockPlatformAPI.get_account_insights()
    
    # Count items
    posts_count_result = await db.execute(select(func.count(Post.id)))
    total_posts = posts_count_result.scalar() or 0
    
    drafts_pending_result = await db.execute(
        select(func.count(GeneratedDraft.id)).where(GeneratedDraft.status == "pending")
    )
    pending_drafts = drafts_pending_result.scalar() or 0
    
    scheduled_result = await db.execute(
        select(func.count(ScheduledPost.id)).where(ScheduledPost.status == "scheduled")
    )
    total_scheduled = scheduled_result.scalar() or 0
    
    comments_pending = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.triage_action.in_(["human_review", "escalate_immediate"]),
            Comment.replied == False,
        )
    )
    comments_pending_count = comments_pending.scalar() or 0
    
    # Compute average EQI
    avg_eqi_result = await db.execute(
        select(func.avg(Post.eqi_score)).where(Post.eqi_score != None)
    )
    avg_eqi = avg_eqi_result.scalar() or 0
    
    # Trend deltas (mock but realistic)
    trend_deltas = [
        {"metric": "saves", "change": "+42%", "context": "on carousel posts this week", "direction": "up"},
        {"metric": "shares", "change": "+28%", "context": "on reel content", "direction": "up"},
        {"metric": "comments", "change": "-5%", "context": "overall, but quality is up", "direction": "down"},
        {"metric": "reach", "change": "+15%", "context": "vs last week", "direction": "up"},
    ]
    
    # Circuit breaker status
    sentinel = SentinelAgent()
    cb_status = sentinel.check_circuit_breaker([0.2, 0.5, -0.1, 0.3, 0.6, 0.1, -0.2, 0.4, 0.7, 0.3])
    
    return {
        "overview": {
            "total_posts": total_posts,
            "drafts_pending": pending_drafts,
            "total_scheduled": total_scheduled,
            "avg_eqi": round(avg_eqi, 1) if avg_eqi else 0,
            "engagement_rate": round(account["accounts_engaged_7d"] / max(account["followers_count"], 1) * 100, 1),
            "follower_growth_pct": round(account["followers_delta_7d"] / max(account["followers_count"], 1) * 100, 2),
            "comments_pending_review": comments_pending_count,
            "circuit_breaker_active": cb_status["triggered"],
        },
        "account_insights": account,
        "trend_deltas": trend_deltas,
        "agent_status": {
            "scout": {"status": "active", "last_scan": "2 hours ago", "trends_found": 3},
            "strategist": {"status": "active", "method": "linucb_bandit", "next_recommendation": "ready"},
            "copywriter": {"status": "idle", "drafts_pending": pending_drafts},
            "guardrail": {"status": "active", "checks_today": 12, "rejections_today": 1},
            "sentinel": {"status": "active", "comments_triaged_today": 45, "auto_replies_sent": 8},
        },
    }


@analytics_router.get("/posts")
async def get_post_analytics(
    brand_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get per-post analytics with EQI scores."""
    query = select(Post).order_by(desc(Post.posted_at)).limit(limit)
    if brand_id:
        query = query.where(Post.brand_id == brand_id)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "content": p.content[:200],
            "full_content": p.content,
            "platform": p.platform,
            "post_type": p.post_type,
            "eqi_score": p.eqi_score,
            "eqi_tier": EQIService.get_engagement_tier(p.eqi_score) if p.eqi_score else "unknown",
            "likes": p.likes,
            "comments_count": p.comments_count,
            "shares": p.shares,
            "saves": p.saves,
            "impressions": p.impressions,
            "reach": p.reach,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "hook": p.hook_text,
        }
        for p in posts
    ]


@analytics_router.get("/audience")
async def get_audience_analytics():
    """Get audience demographics and insights (§6.2)."""
    account = MockPlatformAPI.get_account_insights()
    return {
        "demographics": account["demographics"],
        "followers_count": account["followers_count"],
        "followers_delta_7d": account["followers_delta_7d"],
        "accounts_reached_7d": account["accounts_reached_7d"],
        "accounts_engaged_7d": account["accounts_engaged_7d"],
    }


@analytics_router.get("/engagement-heatmap")
async def get_engagement_heatmap():
    """Get engagement heatmap data for schedule visualization."""
    return {
        "heatmap": ENGAGEMENT_HEATMAP,
        "peak_hours": [
            {"hour": 7, "label": "7 AM", "score": 0.55},
            {"hour": 12, "label": "12 PM", "score": 0.60},
            {"hour": 19, "label": "7 PM", "score": 0.85},
            {"hour": 20, "label": "8 PM", "score": 0.90},
            {"hour": 21, "label": "9 PM", "score": 0.75},
        ],
    }


# ──────────────────────────────────────────────
# Trends Router
# ──────────────────────────────────────────────

trends_router = APIRouter(prefix="/api/trends", tags=["trends"])


@trends_router.get("")
async def get_trends(platform: str = "instagram"):
    """Get trending topics filtered by brand relevance (§6.4)."""
    trends = ScoutAgent.scan_trends(platform=platform)
    return {
        "trends": trends,
        "last_scan": datetime.utcnow().isoformat(),
        "method": "periodic_relevance_filtered",
    }
