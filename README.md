# Pulse

Pulse is an agentic AI social media manager built to protect the creator, not just the metric. Instead of optimising purely for vanity numbers, Pulse uses a pipeline of specialised AI agents to generate on-brand content, predict the best time to post, triage incoming comments, and automatically pause posts when audience sentiment turns negative.

The project was built as a full-stack hackathon prototype and is demo-ready out of the box with seeded data for a fictional fitness brand called FitVibe.

---

## Overview

Most social media tools treat content as a conversion funnel. Pulse treats it as a brand asset. Every piece of content passes through a guardrail that checks for voice drift and low-quality cliches before it ever reaches a human for approval. Comments are triaged automatically using a 2x2 risk matrix. If negative sentiment spikes, a circuit breaker pauses scheduled posts until a human reviews the situation.

The five agents are persona-named and run as nodes in a LangGraph pipeline:

| Agent | Role | What it does |
| --- | --- | --- |
| Scout | Trend Radar | Scans for trending topics and filters them by relevance to the brand's content pillars |
| Strategist | Peak-Time Prediction | Uses a heuristic engagement heatmap seeded with the brand's own historical data, scaffolded with a LinUCB contextual bandit |
| Copywriter | Content Generation | Generates a hook separately from the caption body, then produces 3 full variants using Gemini, Claude, or OpenAI with a template fallback |
| Guardrail | Quality Gate | Rejects drafts that drift too far from the brand voice centroid or score poorly on a slop rubric of cliches and filler phrases |
| Sentinel | Comment Triage | Classifies comments by sentiment and intent, routes them through a 2x2 risk matrix, generates auto-replies for safe buckets, and monitors for sentiment spikes |

---

## Tech Stack

### Backend

| Layer | Technology |
| --- | --- |
| API framework | FastAPI with async SQLAlchemy |
| Agent orchestration | LangGraph |
| Database | PostgreSQL 16 with the pgvector extension |
| Cache | Redis 7 |
| LLM providers | Google Gemini, Anthropic Claude, OpenAI (any one is sufficient) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, 384 dimensions) |
| Sentiment model | cardiffnlp/twitter-roberta-base-sentiment-latest via HuggingFace Transformers |
| Migrations | Alembic |

### Frontend

| Layer | Technology |
| --- | --- |
| Framework | Next.js 14 (App Router, TypeScript) |
| Styling | Vanilla CSS with a custom design system |
| State | React hooks, no external state library |
| Data fetching | Native fetch with a typed API client |

### Infrastructure

- Docker Compose manages PostgreSQL and Redis locally
- pgvector handles vector similarity search for brand voice retrieval

---

## Features

### Content Studio

- Fill in a topic, platform, and tone then trigger the full agent pipeline
- Watch a live pipeline trace showing each agent node, its input summary, duration, and the reasoning behind its decision
- Review 3 generated draft variants side by side with voice similarity scores, slop scores, and hook highlighting
- Approve or reject each variant; approved drafts move to the scheduler

### Dashboard

- Overview stats for total posts, drafts pending, scheduled posts, and engagement rate
- Engagement trend deltas sourced from Scout
- Trending topic cards with relevance explanations
- Agent status panel and circuit breaker status

### Schedule

- 7x24 engagement heatmap built from the brand's own historical data
- Top recommended posting slots with confidence scores
- Upcoming scheduled posts with platform and status

### Comment Triage

- 2x2 risk matrix grid (auto-reply, human review, log only, escalate)
- Sentiment badges and intent labels on each comment card
- Auto-reply previews for comments routed to the safe bucket
- Circuit breaker banner that activates when negative sentiment crosses the threshold

### Analytics

- Audience demographics including city distribution and gender split
- EQI-ranked post performance table showing which content drove quality engagement
- Platform-specific engagement breakdowns

### Brand Voice

- Structural profile derived from the brand's post history (average length, hashtag density, question frequency, CTA patterns)
- Tone radar chart across dimensions like educational, inspirational, and conversational
- Brand guidelines with temporal validity dates so outdated rules do not pollute generation

### Pipeline Trace

- Visual execution trace for every content generation or comment triage run
- Architecture overview showing all agent nodes and their connections
- Per-decision "why" annotations surfacing the reasoning from each agent

---

## Technical Workflow

### Content Generation Pipeline

```
new_post_request
    |
    Scout
    Scans trending topics, filters by brand content pillars, returns top 2-3 matches
    |
    Strategist
    Reads engagement heatmap, applies LinUCB bandit to recommend posting time and platform
    |
    Copywriter
    Retrieves top-quartile hooks via pgvector similarity search
    Generates hook separately from caption body
    Produces 3 variants via LLM with voice examples as few-shot context
    |
    Guardrail
    Computes cosine similarity between each draft embedding and the brand voice centroid
    Runs slop rubric to flag cliche phrases
    Rejects drafts below threshold and retries (up to 2 retries)
    |
    Approval Gate
    Presents variants to human via Content Studio
    Awaits approve or reject action
    |
    Scheduler
    Stores approved draft with Strategist-recommended post time and platform
```

### Comment Triage Pipeline

```
comment_received (batch or real-time)
    |
    Sentiment Classifier
    cardiffnlp RoBERTa model classifies each comment as positive, neutral, or negative
    |
    Intent Classifier
    Rule-based and LLM classification into: FAQ, collab, press, complaint, spam, positive
    |
    Risk Matrix Router
    Maps (intent confidence, brand risk level) to one of four cells:
        auto-reply         low risk, high confidence FAQ or positive
        human review       medium risk or ambiguous intent
        log only           neutral, low engagement value
        escalate           high risk, verified account, or complaint
    |
    Auto-Reply Generator
    For auto-reply bucket only, generates on-brand reply using brand voice context
    |
    Circuit Breaker
    Monitors rolling negative sentiment ratio over a 30-minute window
    Triggers post pause if ratio exceeds the configured threshold
```

### Brand Voice Memory

Every brand stores a pgvector embedding centroid computed from its post history. When the Copywriter retrieves examples for few-shot generation, it uses cosine similarity against this centroid to surface the most on-brand posts from the top-quartile by EQI score. The Guardrail checks each generated draft against the same centroid to catch voice drift before the draft reaches the approval gate.

---

## Setup

### Prerequisites

- Docker Desktop (must be running)
- Python 3.11 or later
- Node.js 18 or later
- At least one LLM API key: Google Gemini (recommended), Anthropic Claude, or OpenAI

### 1. Start the database and cache

```bash
docker compose up -d
```

This starts PostgreSQL 16 with pgvector and Redis 7.

### 2. Configure the backend

```bash
cd backend
cp .env.example .env
```

Open `.env` and add at least one of the following:

```
GOOGLE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

If no key is provided the app falls back to template-based generation. The pipeline still runs and every page still works; content just will not use a real LLM.

### 3. Install backend dependencies and start the server

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### 4. Install frontend dependencies and start the dev server

```bash
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 5. Seed demo data

```bash
curl -X POST http://localhost:8000/api/seed
```

Or click "Seed Demo Data" on the dashboard. This loads the FitVibe brand with 20 posts, 20+ comments, 5 brand guidelines, and a full engagement heatmap.

---

## Project Structure

```
pulse/
├── backend/
│   ├── app/
│   │   ├── agents/          # Scout, Strategist, Copywriter, Sentinel, graph orchestration
│   │   ├── api/             # REST endpoints (13 routes across 4 routers)
│   │   ├── db/              # SQLAlchemy models, Alembic migrations, seed data
│   │   ├── models/          # Pydantic request and response schemas
│   │   ├── services/        # Voice engine, EQI scoring, mock Instagram platform
│   │   └── main.py          # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── app/             # Next.js app router, global CSS, layout
│       ├── components/
│       │   ├── pages/       # One component per dashboard page
│       │   └── ui/          # Shared UI primitives
│       └── lib/             # Typed API client
├── docker-compose.yml
├── SETUP.md                 # Detailed setup guide
└── REPORT.md                # Full build report with PRD coverage matrix
```

---

## API Reference

| Method | Path | Description |
| --- | --- | --- |
| GET | /health | Health check |
| POST | /api/seed | Seed demo data |
| GET | /api/dashboard/{brand_id} | Dashboard overview stats |
| POST | /api/content/generate | Trigger full agent pipeline |
| GET | /api/content/drafts/{brand_id} | List generated drafts |
| POST | /api/content/drafts/{draft_id}/approve | Approve a draft |
| POST | /api/content/drafts/{draft_id}/reject | Reject a draft |
| GET | /api/comments/triage/{brand_id} | Comment triage by risk matrix cell |
| GET | /api/comments/circuit-breaker/{brand_id} | Circuit breaker status |
| GET | /api/analytics/performance/{brand_id} | EQI-ranked post performance |
| GET | /api/analytics/audience/{brand_id} | Audience demographics |
| GET | /api/schedule/heatmap/{brand_id} | Engagement heatmap data |
| GET | /api/trends/{brand_id} | Scout trend recommendations |