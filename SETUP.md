# 🛠️ SETUP GUIDE — Pulse (Agentic AI Social Media Manager)

Welcome to the team! This guide walks you through getting the project running **from zero** on your machine. Estimated time: **~15 minutes** (mostly waiting for installs).

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone & Open](#2-clone--open)
3. [Environment Setup (API Keys)](#3-environment-setup-api-keys)
4. [Start the Database](#4-start-the-database)
5. [Run the Backend](#5-run-the-backend)
6. [Run the Frontend](#6-run-the-frontend)
7. [Seed Demo Data](#7-seed-demo-data)
8. [Verify Everything Works](#8-verify-everything-works)
9. [Project Structure](#9-project-structure)
10. [Who Owns What](#10-who-owns-what)
11. [Common Issues & Fixes](#11-common-issues--fixes)

---

## 1. Prerequisites

Install these **before** anything else. Check each one:

### Python 3.10+
```bash
python3 --version   # should print 3.10.x or higher
```
Download: https://www.python.org/downloads/

### Node.js 18+
```bash
node --version   # should print v18.x.x or higher
npm --version
```
Download: https://nodejs.org/ (pick the LTS version)

### Docker Desktop
```bash
docker --version   # should print Docker version 24+
docker compose version
```
Download: https://www.docker.com/products/docker-desktop/

> ⚠️ **Make sure Docker Desktop is actually running** (the whale icon in your menu bar / taskbar). Just installing it isn't enough.

### Git
```bash
git --version
```

---

## 2. Clone & Open

```bash
git clone <your-github-repo-url>
cd "social media manager"
```

> 📁 The project root contains `backend/`, `frontend/`, `docker-compose.yml`. All commands in this guide assume you're in the project root unless stated otherwise.

---

## 3. Environment Setup (API Keys)

The backend needs at least **one** LLM API key to generate content. Without it, the system still runs in template mode (pipeline still works, just no real LLM calls).

### Step 1 — Copy the env template

```bash
cp backend/.env.example backend/.env
```

### Step 2 — Add an API key

Open `backend/.env` in any text editor and fill in **at least one** of:

```env
# Option A: Google Gemini (recommended — free tier available)
GOOGLE_API_KEY=your_key_here

# Option B: Anthropic Claude (best quality for brand-voice writing)
ANTHROPIC_API_KEY=your_key_here

# Option C: OpenAI (GPT-4o)
OPENAI_API_KEY=your_key_here
```

**Getting a free Gemini key (fastest):**
1. Go to https://aistudio.google.com/apikey
2. Sign in with Google → "Create API key"
3. Copy and paste into `backend/.env`

> 💡 You can leave all three blank — the app will use template-based generation and every page still works. But for a real demo, add at least one.

### Step 3 — Frontend env (optional)

If your backend runs on a different port, create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
If you skip this, it defaults to `http://localhost:8000` automatically.

---

## 4. Start the Database

We use **PostgreSQL + pgvector** (for AI embeddings) and **Redis** via Docker.

```bash
# From the project root
docker compose up -d
```

This starts two containers in the background:
- `pulse_db` — PostgreSQL on port `5432`
- `pulse_redis` — Redis on port `6379`

**Verify both are healthy:**
```bash
docker compose ps
```

You should see `healthy` status for both services. If it shows `starting`, wait 10 seconds and run it again.

**To stop the database later:**
```bash
docker compose down
```

> ⚠️ The database data persists in a Docker volume (`pgdata`). To fully reset:
> ```bash
> docker compose down -v   # -v removes the volume too
> ```

---

## 5. Run the Backend

```bash
# 1. Go into the backend directory
cd backend

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
#    On Mac/Linux:
source venv/bin/activate
#    On Windows:
venv\Scripts\activate

# 4. Install dependencies (this takes 2-4 minutes the first time)
pip install -r requirements.txt

# 5. Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see output like:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it's alive:**
```bash
curl http://localhost:8000/health
# → {"status":"healthy","timestamp":"..."}
```

Or open http://localhost:8000 in your browser — you'll see the Pulse API root response.

**Interactive API docs** (very useful for testing endpoints):
- http://localhost:8000/docs — Swagger UI
- http://localhost:8000/redoc — ReDoc

> 📌 Keep this terminal open. The backend needs to be running while you use the frontend.

---

## 6. Run the Frontend

Open a **new terminal** (keep the backend running in the first one):

```bash
# From the project root
cd frontend

# Install Node dependencies (first time only, takes 1-2 min)
npm install

# Start the dev server
npm run dev
```

**You should see:**
```
▲ Next.js 16.x
  - Local:   http://localhost:3000
```

Open http://localhost:3000 in your browser.

---

## 7. Seed Demo Data

Once both backend and frontend are running, load the demo brand data:

**Option A — Click the button:**  
On the Dashboard, click **"🌱 Seed Demo Data"** in the top right.

**Option B — Terminal:**
```bash
curl -X POST http://localhost:8000/api/seed
```

This creates:
- **Brand:** FitVibe (fitness/wellness creator, 85K followers)
- **20 posts** with realistic engagement metrics (likes, shares, saves)
- **Brand guidelines** with temporal validity
- **20+ comments** already triaged by the Sentinel agent

You only need to do this **once**. Running it again will tell you it's already seeded.

---

## 8. Verify Everything Works

Run through this quick checklist:

| Check | Where | Expected |
|-------|-------|----------|
| Backend alive | http://localhost:8000/health | `{"status":"healthy"}` |
| Frontend loads | http://localhost:3000 | Dashboard renders |
| Sidebar status | Bottom-left of sidebar | "Backend: connected" |
| Seed data | Dashboard → Seed button | "Demo seeded! 20 posts..." toast |
| Generate content | Content Studio → enter topic → Generate | 3 variant cards appear |
| Comment triage | Comments page | 4-quadrant risk matrix with comments |
| Schedule | Schedule page | Heatmap + peak time recommendation |

---

## 9. Project Structure

```
social media manager/
│
├── backend/                    # Python / FastAPI
│   ├── app/
│   │   ├── agents/             # The 5 AI agents
│   │   │   ├── copywriter.py   # Content generation (hook→caption)
│   │   │   ├── strategist.py   # Peak-time prediction (LinUCB)
│   │   │   ├── sentinel.py     # Comment triage (risk matrix)
│   │   │   ├── scout.py        # Trend radar
│   │   │   └── graph.py        # Main LangGraph orchestration
│   │   │
│   │   ├── api/                # REST endpoints
│   │   │   ├── brands.py       # Brand CRUD + voice ingestion
│   │   │   ├── content.py      # Generate / approve / reject drafts
│   │   │   └── endpoints.py    # Schedule, comments, analytics, trends
│   │   │
│   │   ├── db/                 # Database layer
│   │   │   ├── models.py       # SQLAlchemy models (8 tables)
│   │   │   ├── database.py     # Async engine setup
│   │   │   └── seed_data.py    # Demo data (FitVibe brand)
│   │   │
│   │   ├── services/           # Shared business logic
│   │   │   ├── voice_engine.py # Voice fingerprinting + guardrail
│   │   │   ├── eqi.py          # Engagement Quality Index scoring
│   │   │   └── mock_platform.py# Fake Instagram API (demo mode)
│   │   │
│   │   ├── models/schemas.py   # Pydantic request/response schemas
│   │   ├── config.py           # App settings (reads .env)
│   │   └── main.py             # FastAPI app entry point
│   │
│   ├── .env.example            # Copy this to .env
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # Next.js / TypeScript
│   └── src/
│       ├── app/
│       │   ├── globals.css     # Design system (dark mode, colors)
│       │   ├── layout.tsx      # Root layout
│       │   └── page.tsx        # App shell with routing
│       │
│       ├── components/
│       │   ├── Sidebar.tsx     # Navigation + agent status
│       │   ├── ui/             # Shared UI components
│       │   └── pages/          # One file per page
│       │       ├── DashboardPage.tsx
│       │       ├── ContentStudioPage.tsx
│       │       ├── CommentsPage.tsx
│       │       ├── SchedulePage.tsx
│       │       ├── AnalyticsPage.tsx
│       │       ├── BrandVoicePage.tsx
│       │       └── PipelineTracePage.tsx
│       │
│       └── lib/api.ts          # Backend API client (all fetch calls here)
│
├── docker-compose.yml          # PostgreSQL + Redis
├── README.md                   # Quick start
├── SETUP.md                    # This file
├── ACTION_ITEMS.md             # Things that need human input
└── REPORT.md                   # Full build report + PRD coverage
```

---

## 10. Who Owns What

Suggested split for 3 people:

| Member | Area | Files |
|--------|------|-------|
| **Member 1** | Backend agents + pipeline | `backend/app/agents/` · `backend/app/services/` |
| **Member 2** | Backend API + DB | `backend/app/api/` · `backend/app/db/` |
| **Member 3** | Frontend | `frontend/src/` |

**Key flow to understand:**
```
POST /api/content/generate
    → brands.py loads brand context from DB
    → graph.py runs Scout → Strategist → Copywriter → Guardrail
    → Returns variants with pipeline_trace
    → Frontend renders in ContentStudioPage.tsx
```

---

## 11. Common Issues & Fixes

### ❌ `docker: command not found`
Docker isn't installed or isn't in your PATH. Re-install from https://www.docker.com/products/docker-desktop/ and restart your terminal.

### ❌ `Error: connection refused` on port 5432
The database container isn't running. Run:
```bash
docker compose up -d
docker compose ps   # check status
```
If status shows `Exited`, try:
```bash
docker compose logs db
```

### ❌ `ModuleNotFoundError: No module named 'fastapi'`
You're not in the virtual environment. Activate it:
```bash
source backend/venv/bin/activate   # Mac/Linux
backend\venv\Scripts\activate      # Windows
```

### ❌ `pip install` fails on `torch` (takes forever or errors)
PyTorch is large (~2GB). For faster install without CUDA:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### ❌ Frontend shows "Backend: offline" in sidebar
The backend isn't running. Start it (Step 5) and reload the page.

### ❌ Content generation returns "Generation failed"
- Check your `backend/.env` has a valid API key
- Check the backend terminal for the actual error message
- The app falls back to template mode — the pipeline still runs, just without real LLM calls

### ❌ `Port 3000 already in use`
Another process is on port 3000. Either kill it or run frontend on a different port:
```bash
npm run dev -- -p 3001
```
Then open http://localhost:3001.

### ❌ `Port 8000 already in use`
```bash
uvicorn app.main:app --reload --port 8001
```
And update `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### ❌ Seed data gives "already seeded" on a fresh setup
The database volume persisted from a previous run. Reset it:
```bash
docker compose down -v   # removes volumes
docker compose up -d     # fresh start
# then reseed from the UI or curl
```

---

## 💡 Tips for Development

- **Backend hot-reload**: The `--reload` flag restarts the server on every file save. You don't need to manually restart it.
- **Frontend hot-reload**: Next.js `dev` mode does the same — save a file, browser refreshes.
- **API exploration**: http://localhost:8000/docs is your best friend. Every endpoint is documented and you can test them directly from the browser.
- **Mock data**: Every frontend page has built-in mock data. If you're only working on the frontend, you don't even need the backend running.
- **Logs**: Backend logs print to the terminal running uvicorn. If something breaks, that's the first place to look.

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| Backend API Docs | http://localhost:8000/docs |
| Frontend App | http://localhost:3000 |
| Backend Health | http://localhost:8000/health |
| Seed Endpoint | POST http://localhost:8000/api/seed |

Happy hacking! 🚀
