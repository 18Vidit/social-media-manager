# Build Report: Pulse (Agentic AI Social Media Manager)

## What Was Built

### Full-Stack Application
A complete hackathon-ready prototype of **Pulse** — an agentic AI social media manager with persona-named agents (Scout, Strategist, Copywriter, Guardrail, Sentinel) orchestrated through a LangGraph-style pipeline.

---

## Backend (Python / FastAPI)

### Architecture
- **FastAPI** app with async SQLAlchemy + pgvector
- **PostgreSQL + pgvector** for brand voice memory (embeddings, centroid, structural profile)
- **5 Agent Nodes** implementing the full PRD pipeline

### Agents Built

| Agent | File | What It Does |
|-------|------|-------------|
| ** Scout** | `agents/scout.py` | Trend radar — periodic relevance-filtered scan, surfaces top 2-3 trends matching brand content pillars |
| ** Strategist** | `agents/strategist.py` | Peak-time prediction — heuristic heatmap + LinUCB contextual bandit with EQI reward signal |
| ** Copywriter** | `agents/copywriter.py` | Content generation — hook-then-caption split, 3 variants, LLM integration (Gemini/Claude/OpenAI with template fallback) |
| ** Guardrail** | (in `services/voice_engine.py`) | Dual check — embedding-centroid voice similarity + slop rubric cliché detection |
| ** Sentinel** | `agents/sentinel.py` | Comment triage — 2×2 risk matrix routing, sentiment classification, circuit breaker |

### Key Services
- **Voice Engine** (`services/voice_engine.py`): Brand voice analysis — embeddings, centroid computation, structural profile caching, slop rubric
- **EQI Service** (`services/eqi.py`): Engagement Quality Index — platform-specific weighted formula for the bandit reward signal
- **Mock Platform** (`services/mock_platform.py`): Instagram Graph API simulator for demo mode

### Database Schema
- `brands` — with pgvector centroid + cached structural profile
- `brand_guidelines` — with `valid_from`/`valid_to` temporal columns (the lightweight Graphiti alternative)
- `posts` — with pgvector embeddings, EQI scores, extracted hooks
- `generated_drafts` — with voice similarity, slop scores, explainability data, pipeline traces
- `scheduled_posts` — with circuit breaker pause flag
- `comments` — with sentiment, intent, risk matrix routing
- `auto_replies` — with risk matrix cell and explanation
- `engagement_metrics` — time-series for peak-time prediction

### API Endpoints (13 total)
- Brand CRUD + guideline management + bulk post ingestion
- Content generation (triggers full pipeline) + draft management (approve/reject)
- Peak-time prediction + upcoming posts
- Comment triage (2×2 view) + circuit breaker status
- Dashboard analytics + post performance + audience demographics
- Trend scanning

### Seed Data
- **Demo brand "FitVibe"**: fitness/wellness creator, 85K followers
- **20 realistic posts** across carousel, reel, text formats with engagement metrics
- **20+ comments** across all triage categories (FAQ, positive, collab, press, complaint, spam)
- **5 brand guidelines** with temporal validity
- **Engagement heatmap** with realistic Delhi/Mumbai audience patterns

---

## Frontend (Next.js / TypeScript)

### 7 Dashboard Pages

| Page | What It Shows |
|------|--------------|
| **Dashboard** | Overview stats, engagement trends, trending topics from Scout, agent status, circuit breaker, audience snapshot |
| **Content Studio** | Generate form → live pipeline trace → 3 variant cards with voice similarity, slop scores, hook highlighting, explainability, approve/reject |
| **Comment Triage** | 2×2 risk matrix grid, sentiment badges, auto-reply previews, circuit breaker banner |
| **Schedule** | Engagement heatmap (7×24 grid), top posting slots, LinUCB recommendation, upcoming posts |
| **Analytics** | Audience stats, city/gender distribution, EQI-ranked post performance table |
| **Brand Voice** | Structural profile, tone radar, guidelines with temporal validity |
| **Pipeline Trace** | Visual execution traces, architecture overview, §4 synthesis decisions |

### Design System
- **Premium dark mode** with cyan/teal accents matching the PPT aesthetic
- **Glassmorphism cards**, smooth animations, micro-interactions
- **Responsive layout** with sidebar navigation
- **Agent status indicators** with live pulse animations
- **Mock data fallback** — every page works even without the backend running

---

## PRD Coverage (Tier 1 features)

| Feature | Status | Notes |
|---------|--------|-------|
| LangGraph pipeline |  Built | Persona-named nodes, pipeline trace |
| Brand voice ingestion | Built | 20 sample posts, voice centroid + structural profile |
| Hook → Caption split | Built | Separate hook generator + caption generator |
| Widened guardrail | Built | Voice-drift (embedding) + slop rubric (cliché) |
| Human approval gate | Built | Approve/reject in Content Studio |
| Heuristic peak-time | Built | Engagement heatmap from brand's own data |
| Auto-reply (risk matrix) | Built | 2×2 grid with classification |
| Sentiment circuit breaker | Built | cardiffnlp model reference, rule-based fallback |
| Explainability panel | Built | Pipeline Trace page + per-variant "why" annotations |

### Tier 2 (demo-ready but not fully wired)
| Feature | Status |
|---------|--------|
| LinUCB bandit | Built + seeded | Scaffolded with synthetic data |
| EQI scoring | Built | Platform-specific weights |
| Trend radar | Built | Relevance-filtered scan |
| Voice-drift rejection loop (visual) | Built | Visible in pipeline trace |

---

## What You Need To Do (see ACTION_ITEMS.md)
1. Add at least ONE LLM API key (Gemini recommended — easiest)
2. Start Docker for PostgreSQL
3. Install Python dependencies + run backend
4. Run frontend
5. Seed demo data
6. Practice the demo flow

---

## Architecture Diagram (maps to your Mermaid diagrams)

```
Trigger (new_post / comment / scheduled_tick / trend_scan)
    │
    ├──── new_post_request ──►  Scout → Strategist → Copywriter → Guardrail → Approval Gate → Scheduler
    │
    ├──── comment_received ──►  Sentinel (Sentiment + Intent) → Risk Matrix → Auto-Reply / Escalate
    │
    └──── circuit_breaker  ──►  Sentiment Check → Pause Scheduled Posts → Alert Human
```

This maps directly to your architecture_diagram.mermaid and content_generation_subgraph.mermaid.
