"""
Pulse — FastAPI Application Entry Point
An Agentic AI Social Media Manager
"""

from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Pulse — Agentic AI Social Media Manager",
    description="An AI-powered social media manager with persona-named agents: Scout, Strategist, Copywriter, Guardrail, and Sentinel.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.brands import router as brands_router
from app.api.content import router as content_router
from app.api.endpoints import schedule_router, comments_router, analytics_router, trends_router
from app.api.instagram import router as instagram_router

app.include_router(brands_router)
app.include_router(content_router)
app.include_router(schedule_router)
app.include_router(comments_router)
app.include_router(analytics_router)
app.include_router(trends_router)
app.include_router(instagram_router)


@app.get("/")
async def root():
    return {
        "name": "Pulse",
        "tagline": "An agentic AI social media manager that protects the creator, not just the metric.",
        "version": "1.0.0",
        "status": "running",
        "demo_mode": settings.demo_mode,
        "agents": {
            "scout": "🔍 Trend Radar — surfaces relevant trends",
            "strategist": "📊 Peak-Time Predictor — optimizes posting windows",
            "copywriter": "✍️ Content Generator — on-brand content with hook-then-caption split",
            "guardrail": "🛡️ Voice Drift + Slop Check — dual quality gate",
            "sentinel": "👁️ Comment Triage — 2×2 risk matrix routing",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/seed")
async def seed_demo_data():
    """Seed the database with demo brand data for hackathon demo."""
    # pyrefly: ignore [missing-import]
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.database import async_session
    from app.db.models import Brand, BrandGuideline, Post, Comment
    from app.db.seed_data import DEMO_BRAND, DEMO_GUIDELINES, DEMO_POSTS, DEMO_COMMENTS
    from app.services.voice_engine import VoiceEngine
    from app.services.eqi import EQIService
    from app.agents.sentinel import SentinelAgent
    # pyrefly: ignore [missing-import]
    from sqlalchemy import select
    import uuid
    from datetime import date
    
    async with async_session() as session:
        # Check if already seeded
        existing = await session.execute(select(Brand).where(Brand.id == DEMO_BRAND["id"]))
        if existing.scalar_one_or_none():
            return {"status": "already_seeded", "brand_id": DEMO_BRAND["id"]}
        
        # Create brand
        brand = Brand(
            id=DEMO_BRAND["id"],
            name=DEMO_BRAND["name"],
            handle=DEMO_BRAND["handle"],
            platform=DEMO_BRAND["platform"],
            description=DEMO_BRAND["description"],
            weekly_post_limit=DEMO_BRAND["weekly_post_limit"],
        )
        session.add(brand)
        
        # Add guidelines
        for gl_data in DEMO_GUIDELINES:
            gl = BrandGuideline(
                id=str(uuid.uuid4()),
                brand_id=DEMO_BRAND["id"],
                title=gl_data["title"],
                content=gl_data["content"],
                category=gl_data.get("category"),
                valid_from=date.fromisoformat(gl_data["valid_from"]),
            )
            session.add(gl)
        
        # Ingest posts with embeddings
        embeddings = []
        post_texts = []
        
        for post_data in DEMO_POSTS:
            embedding = VoiceEngine.compute_embedding(post_data["content"])
            eqi = EQIService.compute_eqi(
                likes=post_data["likes"],
                comments=post_data["comments_count"],
                shares=post_data["shares"],
                saves=post_data["saves"],
                impressions=post_data["impressions"],
                reach=post_data["reach"],
            )
            hook = post_data["content"].split("\n")[0].strip()
            
            post = Post(
                id=str(uuid.uuid4()),
                brand_id=DEMO_BRAND["id"],
                platform="instagram",
                content=post_data["content"],
                post_type=post_data["post_type"],
                embedding=embedding,
                likes=post_data["likes"],
                comments_count=post_data["comments_count"],
                shares=post_data["shares"],
                saves=post_data["saves"],
                impressions=post_data["impressions"],
                reach=post_data["reach"],
                eqi_score=eqi,
                hook_text=hook,
                posted_at=datetime.fromisoformat(post_data["posted_at"]),
            )
            session.add(post)
            embeddings.append(embedding)
            post_texts.append(post_data["content"])
        
        # Compute voice centroid and structural profile
        centroid = VoiceEngine.compute_centroid(embeddings)
        brand.voice_centroid = centroid
        
        profile = VoiceEngine.compute_structural_profile(post_texts)
        brand.avg_sentence_length = profile.get("avg_sentence_length")
        brand.emoji_frequency = profile.get("emoji_frequency")
        brand.emoji_placement = profile.get("emoji_placement")
        brand.hashtag_count_avg = profile.get("hashtag_count_avg")
        brand.hashtag_placement = profile.get("hashtag_placement")
        brand.avg_post_length = profile.get("avg_post_length")
        brand.tone_keywords = profile.get("tone_keywords")
        
        # Seed comments with triage
        sentinel = SentinelAgent()
        for c_data in DEMO_COMMENTS:
            triage = sentinel.triage_comment(
                text=c_data["content"],
                is_verified=c_data.get("is_verified", False),
            )
            
            comment = Comment(
                id=str(uuid.uuid4()),
                brand_id=DEMO_BRAND["id"],
                platform="instagram",
                author_username=c_data["author"],
                author_is_verified=c_data.get("is_verified", False),
                content=c_data["content"],
                is_dm=False,
                sentiment_score=triage["sentiment_score"],
                sentiment_label=triage["sentiment_label"],
                intent=triage["intent"],
                intent_confidence=triage["intent_confidence"],
                brand_risk=triage["brand_risk"],
                triage_action=triage["triage_action"],
            )
            session.add(comment)
        
        await session.commit()
    
    return {
        "status": "seeded",
        "brand_id": DEMO_BRAND["id"],
        "brand_name": DEMO_BRAND["name"],
        "posts_ingested": len(DEMO_POSTS),
        "guidelines_added": len(DEMO_GUIDELINES),
        "comments_triaged": len(DEMO_COMMENTS),
        "structural_profile": profile,
    }
