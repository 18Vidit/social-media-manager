# Pulse: Agentic AI Social Media Manager

> An AI powered social media manager that protects the creator, not just the metric.


## Quick Start

```bash
# 1. Start database
docker compose up -d

# 2. Start backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API key
uvicorn app.main:app --reload --port 8000

# 3. Start frontend
cd frontend
npm install && npm run dev

# 4. Seed demo data
curl -X POST http://localhost:8000/api/seed
# Or click "🌱 Seed Demo Data" on the dashboard
```

Open http://localhost:3000 to see the dashboard.

## 🤖 Agents

| Agent | Role | Key Feature |
|-------|------|-------------|
|  Scout | Trend Radar | Relevance-filtered trending topics |
|  Strategist | Peak-Time | LinUCB bandit with EQI reward |
|  Copywriter | Content Gen | Hook-then-caption split |
|  Guardrail | Quality Gate | Voice-drift + slop rubric dual check |
|  Sentinel | Comment Triage | 2×2 risk matrix routing |

## 📂 Structure

```
pulse/
├── backend/           # FastAPI + LangGraph agents
│   ├── app/
│   │   ├── agents/    # Scout, Strategist, Copywriter, Sentinel
│   │   ├── api/       # REST endpoints
│   │   ├── db/        # Models, seed data
│   │   ├── services/  # Voice engine, EQI, mock platform
│   │   └── main.py    # App entry point
│   └── requirements.txt
├── frontend/          # Next.js dashboard
│   └── src/
│       ├── app/       # Pages
│       ├── components/ # UI components
│       └── lib/       # API client
├── docker-compose.yml
├── ACTION_ITEMS.md    # What needs your input
└── REPORT.md          # Full build report
```

## 📖 Documentation

- [ACTION_ITEMS.md](ACTION_ITEMS.md) — API keys, Docker setup, running instructions
- [REPORT.md](REPORT.md) — Complete build report with PRD coverage matrix