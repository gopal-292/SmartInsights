# SmartInsights – AI-Powered Business Analyzer

Final-year project matching the seminar tech stack:

| Layer | Technology (as in PPT) |
| --- | --- |
| Frontend | Next.js + TypeScript |
| Charts | Recharts |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL (Supabase hosting / local Docker) |
| ORM | SQLAlchemy |
| Authentication | Better Auth |
| Data Processing | Pandas |
| Machine Learning | Scikit-learn |
| RAG Orchestration | LangChain |
| Vector Database | pgVector |
| LLM API | OpenAI API |
| Reports | Jinja2 + WeasyPrint |

## Project structure

```
IV YEAR PW/
├── docker-compose.yml   # PostgreSQL + pgVector
├── backend/             # FastAPI, SQLAlchemy, Pandas, Scikit-learn, LangChain
├── frontend/            # Next.js + TypeScript + Recharts + Better Auth
└── README.md
```

## Quick start

### 1. Start PostgreSQL + pgVector

```bash
docker compose up -d
```

For Supabase cloud: paste your Supabase Postgres URI into `backend/.env` and `frontend/.env.local` as `DATABASE_URL`.

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate
.\.venv\Scripts\pip install -r requirements.txt

# Windows PDF reports (WeasyPrint)
winget install -e --id tschoonj.GTKForWindows

copy .env.example .env
# set OPENAI_API_KEY for LangChain + OpenAI RAG / LLM answers

uvicorn app.main:app --reload --port 8000
```

Or from repo root: `.\start-backend.ps1`

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Or: `.\start-frontend.ps1`

App: http://localhost:3000

### 4. Demo flow

1. Register with Better Auth (creates PostgreSQL auth tables + bridges to FastAPI user)
2. Save business profile
3. Upload sample files from `backend/sample_data/`
4. Upload `business_policy.txt` to index into **pgVector via LangChain**
5. Explore Dashboard, Forecast, Anomalies, Sentiment, Insights, Assistant, Report PDF

## Auth flow (PPT: Better Auth)

- Sign-up / sign-in run through **Better Auth** (`/api/auth/*`) on Next.js with PostgreSQL
- Frontend then calls FastAPI `POST /api/auth/bridge` to sync the SQLAlchemy user and receive an API JWT for analytics endpoints

## RAG / LLM (PPT: LangChain + pgVector + OpenAI)

- Document uploads are chunked and embedded with OpenAI embeddings into **pgVector**
- Assistant answers use LangChain + OpenAI grounded on retrieved chunks + analytics KPIs
- Without `OPENAI_API_KEY`, the system falls back to analytics + keyword RAG so demos still work offline

## Environment

**backend/.env**

```
DATABASE_URL=postgresql+psycopg2://smartinsights:smartinsights@localhost:5433/smartinsights
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
```

**frontend/.env.local**

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_URL=http://localhost:3000
DATABASE_URL=postgresql://smartinsights:smartinsights@localhost:5433/smartinsights
BETTER_AUTH_SECRET=change-me
BETTER_AUTH_URL=http://localhost:3000
```
