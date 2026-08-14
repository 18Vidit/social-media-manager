"""
Pulse — Database Models
All tables for brand voice memory, content pipeline, comments, and analytics.
Uses pgvector for embedding storage per §7.4 of the PRD.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, Date,
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import enum

from app.db.database import Base
from app.config import settings


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class DraftStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class CommentIntent(str, enum.Enum):
    FAQ = "faq"
    SPAM = "spam"
    COLLABORATION = "collaboration"
    COMPLAINT = "complaint"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    PRESS = "press"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    HIGH = "high"


class TriageAction(str, enum.Enum):
    AUTO_REPLY = "auto_reply"
    HUMAN_REVIEW = "human_review"
    LOG_ONLY = "log_only"
    ESCALATE_IMMEDIATE = "escalate_immediate"


# ──────────────────────────────────────────────
# Brand & Voice Memory (§7.4)
# ──────────────────────────────────────────────

class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    handle: Mapped[Optional[str]] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50), default="instagram")
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Cached structural profile (§7.4c)
    avg_sentence_length: Mapped[Optional[float]] = mapped_column(Float)
    emoji_frequency: Mapped[Optional[float]] = mapped_column(Float)  # emojis per post
    emoji_placement: Mapped[Optional[str]] = mapped_column(String(50))  # start/end/inline/none
    hashtag_count_avg: Mapped[Optional[float]] = mapped_column(Float)
    hashtag_placement: Mapped[Optional[str]] = mapped_column(String(50))  # end/inline/none
    avg_post_length: Mapped[Optional[float]] = mapped_column(Float)  # chars
    tone_keywords: Mapped[Optional[dict]] = mapped_column(JSON)  # e.g., {"casual": 0.8, "professional": 0.2}
    
    # Voice centroid embedding (§7.4b)
    voice_centroid: Mapped[Optional[list]] = mapped_column(Vector(settings.embedding_dimension))
    
    # Posting limits (§6.8 sustainable cadence)
    weekly_post_limit: Mapped[int] = mapped_column(Integer, default=7)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guidelines: Mapped[List["BrandGuideline"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    posts: Mapped[List["Post"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    drafts: Mapped[List["GeneratedDraft"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    scheduled_posts: Mapped[List["ScheduledPost"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class BrandGuideline(Base):
    """Brand guidelines with temporal validity (§7.4d — the lightweight Graphiti alternative)."""
    __tablename__ = "brand_guidelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))  # tone, visual, topics, banned
    
    # Temporal validity (§4 decision — valid_from/valid_to instead of Graphiti)
    valid_from: Mapped[date] = mapped_column(Date, default=date.today)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # NULL = currently in force
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="guidelines")


# ──────────────────────────────────────────────
# Content (§7.5)
# ──────────────────────────────────────────────

class Post(Base):
    """Past posts used for few-shot retrieval and voice centroid computation."""
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[Optional[str]] = mapped_column(String(50))  # carousel, reel, story, text
    
    # Embedding for RAG retrieval (§7.4a)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(settings.embedding_dimension))
    
    # Engagement metrics for top-quartile filtering
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    
    # EQI score (§4 — computed, cached)
    eqi_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Hook extraction
    hook_text: Mapped[Optional[str]] = mapped_column(Text)  # first line / hook for hook-gen training
    
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="posts")
    engagement_metrics: Mapped[List["EngagementMetric"]] = relationship(back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_posts_brand_eqi", "brand_id", "eqi_score"),
    )


class GeneratedDraft(Base):
    """AI-generated content drafts awaiting human approval."""
    __tablename__ = "generated_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    
    # Content
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    hook: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[Optional[list]] = mapped_column(JSON)
    variant_index: Mapped[int] = mapped_column(Integer, default=0)  # 0, 1, 2 for the 3 variants
    
    # Quality scores
    voice_similarity: Mapped[Optional[float]] = mapped_column(Float)
    slop_score: Mapped[Optional[float]] = mapped_column(Float)  # lower = less slop
    predicted_engagement: Mapped[Optional[float]] = mapped_column(Float)
    
    # Explainability (§6.10)
    explanation: Mapped[Optional[dict]] = mapped_column(JSON)  
    # e.g. {"similar_posts": [...], "structural_match": 0.85, "why": "..."}
    
    # Pipeline trace
    pipeline_trace: Mapped[Optional[dict]] = mapped_column(JSON)
    # e.g. {"hook_model": "...", "caption_model": "...", "guardrail_passes": 1, "retry_reasons": [...]}
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default=DraftStatus.PENDING.value)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Recommended posting time from Strategist
    recommended_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    recommended_time_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="drafts")


class ScheduledPost(Base):
    """Approved posts scheduled for publishing."""
    __tablename__ = "scheduled_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    draft_id: Mapped[str] = mapped_column(ForeignKey("generated_drafts.id"), nullable=False)
    
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled, published, paused, cancelled
    
    # Paused by circuit breaker?
    paused_by_circuit_breaker: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="scheduled_posts")
    draft: Mapped["GeneratedDraft"] = relationship()


# ──────────────────────────────────────────────
# Comments & Triage (§7.8)
# ──────────────────────────────────────────────

class Comment(Base):
    """Ingested comments/DMs with classification and triage routing."""
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False)
    
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    post_id: Mapped[Optional[str]] = mapped_column(String(255))  # platform post ID
    
    author_username: Mapped[str] = mapped_column(String(255), nullable=False)
    author_is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_dm: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Classification (§7.8 — dedicated classifiers, not LLM)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20))  # positive/negative/neutral
    intent: Mapped[Optional[str]] = mapped_column(String(50))  # FAQ/spam/collab/complaint/positive/neutral
    
    # Risk matrix routing (§7.8)
    intent_confidence: Mapped[Optional[float]] = mapped_column(Float)
    brand_risk: Mapped[Optional[str]] = mapped_column(String(10))  # low/high
    triage_action: Mapped[Optional[str]] = mapped_column(String(30))
    
    # Resolution
    replied: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="comments")
    auto_replies: Mapped[List["AutoReply"]] = relationship(back_populates="comment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_comments_brand_sentiment", "brand_id", "sentiment_score"),
        Index("idx_comments_brand_triage", "brand_id", "triage_action"),
    )


class AutoReply(Base):
    """Generated auto-replies for comments/DMs."""
    __tablename__ = "auto_replies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    comment_id: Mapped[str] = mapped_column(ForeignKey("comments.id"), nullable=False)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Was this auto-sent or waiting for human approval?
    auto_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[Optional[bool]] = mapped_column(Boolean)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Explainability
    risk_matrix_cell: Mapped[Optional[str]] = mapped_column(String(50))  # e.g. "high_conf_low_risk"
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    comment: Mapped["Comment"] = relationship(back_populates="auto_replies")


# ──────────────────────────────────────────────
# Analytics & Engagement (§5.3, §7.6)
# ──────────────────────────────────────────────

class EngagementMetric(Base):
    """Time-series engagement data per post, used for EQI and peak-time prediction."""
    __tablename__ = "engagement_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), nullable=False)
    
    hour_of_day: Mapped[int] = mapped_column(Integer)  # 0-23
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Monday, 6=Sunday
    
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped["Post"] = relationship(back_populates="engagement_metrics")

    __table_args__ = (
        Index("idx_engagement_hour_day", "hour_of_day", "day_of_week"),
    )
