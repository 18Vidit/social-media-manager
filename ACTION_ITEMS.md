# 📋 ACTION ITEMS — Things That Need Your Input

## 🔑 API Keys Required (Pick at least ONE for LLM-powered generation)

### Option 1: Google Gemini (Recommended — Easiest to get)
1. Go to https://aistudio.google.com/apikey
2. Create an API key
3. Add to `backend/.env`: `GOOGLE_API_KEY=your_key_here`

### Option 2: Anthropic Claude (Best for brand-voice writing quality)
1. Go to https://console.anthropic.com/
2. Create an API key
3. Add to `backend/.env`: `ANTHROPIC_API_KEY=your_key_here`

### Option 3: OpenAI (Fallback)
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Add to `backend/.env`: `OPENAI_API_KEY=your_key_here`

> **Without ANY API key**, the system still works — it uses template-based generation that mimics the pipeline flow. But for the real demo, you want at least Gemini.

---

## 🐳 Docker Required (for PostgreSQL + pgvector)

```bash
# Start the database
cd "social media manager"
docker compose up -d

# Verify it's running
docker compose ps
```

> If you don't have Docker, install from https://www.docker.com/products/docker-desktop/

---

## 🚀 How to Run

### Backend
```bash
cd "social media manager/backend"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and add your API key
cp .env.example .env
# Edit .env and add at least one API key

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd "social media manager/frontend"
npm run dev
```

### Seed Demo Data
Once backend is running, either:
- Click "🌱 Seed Demo Data" button on the dashboard, OR
- `curl -X POST http://localhost:8000/api/seed`

---

## 📝 Things I Couldn't Do Without You

1. **Test with real API keys** — I built the LLM integration but can't test actual API calls
2. **Docker validation** — Database creation needs Docker running
3. **End-to-end flow test** — Generate → Approve → Schedule needs backend + DB running
4. **Presentation fine-tuning** — The Pipeline Trace page has your §4 synthesis decisions hardcoded — review for accuracy

---

## 🎯 For the Demo (Priority Order)

1. Start Docker → Start Backend → Seed Data → Start Frontend
2. Dashboard tour (30 sec)
3. Content Studio: generate content live (60 sec) — **the hero moment**
4. Comment Triage: show 2×2 risk matrix (30 sec)
5. Schedule: show heatmap + LinUCB recommendation (20 sec)
6. Pipeline Trace: walk through the architecture (30 sec)
7. Brand Voice: show structural profile (20 sec)
