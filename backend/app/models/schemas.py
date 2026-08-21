"""
Pulse — Pydantic Schemas for API request/response models.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ──────────────────────────────────────────────
# Brand
# ──────────────────────────────────────────────

class BrandCreate(BaseModel):
    name: str
    handle: Optional[str] = None
    platform: str = "instagram"
    description: Optional[str] = None
    weekly_post_limit: int = 7


class BrandGuidelineCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class StructuralProfile(BaseModel):
    avg_sentence_length: Optional[float] = None
    emoji_frequency: Optional[float] = None
    emoji_placement: Optional[str] = None
    hashtag_count_avg: Optional[float] = None
    hashtag_placement: Optional[str] = None
    avg_post_length: Optional[float] = None
    tone_keywords: Optional[dict] = None


class BrandResponse(BaseModel):
    id: str
    name: str
    handle: Optional[str]
    platform: str
    description: Optional[str]
    weekly_post_limit: int
    structural_profile: Optional[StructuralProfile] = None
    post_count: int = 0
    is_instagram_connected: bool = False
    instagram_account_id: Optional[str] = None
    instagram_profile_pic: Optional[str] = None
    instagram_bio: Optional[str] = None
    instagram_followers_count: Optional[int] = None
    instagram_connected_at: Optional[datetime] = None
    instagram_last_synced_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Instagram Integration
# ──────────────────────────────────────────────

class InstagramConnectRequest(BaseModel):
    brand_id: Optional[str] = None
    access_token: str
    account_id: Optional[str] = None  # Optional IG Business Account ID if already known
    auto_sync: bool = True

class InstagramSyncRequest(BaseModel):
    brand_id: Optional[str] = None
    limit: int = 25

class InstagramPublishRequest(BaseModel):
    brand_id: Optional[str] = None
    draft_id: Optional[str] = None
    caption: str
    image_url: Optional[str] = None

class InstagramReplyRequest(BaseModel):
    brand_id: Optional[str] = None
    comment_id: str
    message: str

class InstagramStatusResponse(BaseModel):
    connected: bool
    account_id: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    followers_count: Optional[int] = None
    media_count: Optional[int] = None
    biography: Optional[str] = None
    last_synced_at: Optional[str] = None
    synced_posts_count: int = 0
    synced_comments_count: int = 0


# ──────────────────────────────────────────────
# Content Generation
# ──────────────────────────────────────────────

class ContentGenerateRequest(BaseModel):
    brand_id: str
    topic: str
    platform: str = "instagram"
    tone: Optional[str] = None  # override tone
    additional_context: Optional[str] = None
    num_variants: int = 3


class DraftResponse(BaseModel):
    id: str
    brand_id: str
    topic: str
    platform: str
    hook: Optional[str]
    content: str
    hashtags: Optional[List[str]]
    variant_index: int
    voice_similarity: Optional[float]
    slop_score: Optional[float]
    predicted_engagement: Optional[float]
    explanation: Optional[dict]
    pipeline_trace: Optional[dict]
    status: str
    recommended_time: Optional[datetime]
    recommended_time_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DraftApproval(BaseModel):
    scheduled_time: Optional[datetime] = None  # if None, use recommended time


class DraftRejection(BaseModel):
    reason: str


# ──────────────────────────────────────────────
# Scheduling
# ──────────────────────────────────────────────

class PeakTimeResponse(BaseModel):
    hour: int
    day_of_week: int
    day_name: str
    score: float
    reason: str


class ScheduledPostResponse(BaseModel):
    id: str
    brand_id: str
    draft_id: str
    platform: str
    scheduled_at: datetime
    status: str
    paused_by_circuit_breaker: bool

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Comments & Triage
# ──────────────────────────────────────────────

class CommentResponse(BaseModel):
    id: str
    brand_id: str
    platform: str
    author_username: str
    author_is_verified: bool
    content: str
    is_dm: bool
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    intent: Optional[str]
    intent_confidence: Optional[float]
    brand_risk: Optional[str]
    triage_action: Optional[str]
    replied: bool
    escalated: bool
    received_at: datetime
    auto_reply: Optional[str] = None

    class Config:
        from_attributes = True


class CommentTriageView(BaseModel):
    high_conf_low_risk: List[CommentResponse] = []   # Auto-reply eligible
    high_conf_high_risk: List[CommentResponse] = []   # Human review + drafted reply
    low_conf_low_risk: List[CommentResponse] = []     # Log only
    low_conf_high_risk: List[CommentResponse] = []    # Escalate immediately


class ManualReplyRequest(BaseModel):
    content: str


# ──────────────────────────────────────────────
# Analytics
# ──────────────────────────────────────────────

class DashboardOverview(BaseModel):
    total_posts: int
    total_drafts_pending: int
    total_scheduled: int
    avg_eqi: float
    engagement_rate: float
    follower_growth_pct: float  # simulated
    comments_pending_review: int
    circuit_breaker_active: bool
    trend_deltas: List[dict]  # e.g. [{"metric": "saves", "change": "+40%", "context": "carousel posts"}]


class PostAnalytics(BaseModel):
    id: str
    content: str
    platform: str
    eqi_score: Optional[float]
    likes: int
    comments_count: int
    shares: int
    saves: int
    impressions: int
    reach: int
    posted_at: Optional[datetime]

    class Config:
        from_attributes = True


class EngagementHeatmapCell(BaseModel):
    hour: int
    day: int
    day_name: str
    engagement_score: float


# ──────────────────────────────────────────────
# Pipeline Trace (§6.10 Explainability)
# ──────────────────────────────────────────────

class PipelineNodeTrace(BaseModel):
    node_name: str          # e.g. "Scout", "Copywriter", "Guardrail"
    persona: str            # friendly name
    status: str             # completed, failed, retrying
    duration_ms: int
    input_summary: str
    output_summary: str
    details: Optional[dict] = None


class PipelineTraceResponse(BaseModel):
    trace_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    nodes: List[PipelineNodeTrace]
    total_duration_ms: int


# ──────────────────────────────────────────────
# Post Ingestion
# ──────────────────────────────────────────────

class PostIngest(BaseModel):
    content: str
    platform: str = "instagram"
    post_type: Optional[str] = None
    likes: int = 0
    comments_count: int = 0
    shares: int = 0
    saves: int = 0
    impressions: int = 0
    reach: int = 0
    posted_at: Optional[datetime] = None


class BulkIngestRequest(BaseModel):
    brand_id: str
    posts: List[PostIngest]
