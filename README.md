# AI Recruitment Intelligence Platform

AI-powered recruitment workspace with:
- Resume parsing and scoring
- Resume-to-job matching
- Fake job detection (Hugging Face + local ML fallback)
- Resume AI generation (LaTeX + DOCX)
- Resume scan history
- Supabase-backed auth and database

## Architecture

- Frontend: React + Vite + Tailwind (deploy on Cloudflare Pages)
- Backend: Flask API (deploy on Fly.io)
- Auth: Supabase Auth (JWT bearer tokens)
- Database: Supabase Postgres (with local JSON fallback)
- ML: Hugging Face inference API + local model fallback
- Job Data: Adzuna API + scraping fallback

## Project Structure

```text
.
|-- backend
|   |-- app.py
|   |-- auth.py
|   |-- database.py
|   |-- Dockerfile
|   |-- fly.toml
|   |-- requirements.txt
|   |-- .env.example
|   |-- services/
|   |   |-- fake_job_detector.py
|   |   |-- job_data_provider.py
|   |   |-- job_recommender.py
|   |   `-- ...
|   `-- supabase/
|       `-- schema.sql
|-- frontend
|   |-- package.json
|   |-- wrangler.toml
|   |-- .env.example
|   |-- public/_redirects
|   `-- src/
|       |-- auth/supabaseClient.js
|       |-- components/AuthGate.jsx
|       `-- ...
`-- README.md
```

## 1) Supabase Setup

1. Create a Supabase project.
2. Open SQL Editor and run:
   - `backend/supabase/schema.sql`
3. In Supabase Auth, enable Email/Password provider.
4. Collect:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

## 2) Backend Local Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Backend: `http://localhost:5000`

### Backend env vars

- `CORS_ORIGINS=http://localhost:5173`
- `DATABASE_BACKEND=auto` (`supabase`, `local`, or `auto`)
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `AUTH_MODE=auto` (`required`, `optional`, `off`, `auto`)
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`
- `JOB_REQUEST_TRUST_ENV=0` (set `1` only if your server must use system proxy env vars)
- `HF_API_TOKEN`
- `HF_FAKE_JOB_MODEL_ID`

Notes:
- If Supabase is missing/unavailable, database writes/reads fall back to local JSON storage.
- If Hugging Face is missing/unavailable, fake-job scoring uses local model only.
- If Adzuna is missing/unavailable, jobs fall back to scraping and local catalog.

## 3) Frontend Local Setup

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

### Frontend env vars

- `VITE_API_BASE_URL=http://localhost:5000`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

If Supabase env vars are present, users must sign in before using the app.

## 4) Deploy Frontend to Cloudflare Pages

Project settings:
- Framework preset: `Vite`
- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`

Set environment variables in Cloudflare Pages:
- `VITE_API_BASE_URL=https://<your-fly-backend-domain>`
- `VITE_SUPABASE_URL=<your-supabase-url>`
- `VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>`

Files already added:
- `frontend/wrangler.toml`
- `frontend/public/_redirects` (SPA routing)

## 5) Deploy Backend to Fly.io

1. Install Fly CLI and login.
2. From `backend` folder:

```powershell
flyctl launch --no-deploy
```

3. Set secrets:

```powershell
flyctl secrets set \
  CORS_ORIGINS=https://<your-cloudflare-domain> \
  SUPABASE_URL=<your-supabase-url> \
  SUPABASE_ANON_KEY=<your-supabase-anon-key> \
  SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key> \
  AUTH_MODE=auto \
  DATABASE_BACKEND=supabase \
  ADZUNA_APP_ID=<your-adzuna-id> \
  ADZUNA_APP_KEY=<your-adzuna-key> \
  HF_API_TOKEN=<your-hf-token> \
  HF_FAKE_JOB_MODEL_ID=<your-hf-model-id>
```

4. Deploy:

```powershell
flyctl deploy
```

Files already added:
- `backend/Dockerfile`
- `backend/fly.toml`
- `backend/.dockerignore`

## API Endpoints

- `GET /api/health`
- `POST /api/resume/parse`
- `GET /api/resume/history`
- `POST /api/job/analyze`
- `POST /api/job/match`
- `POST /api/jobs/recommend`
- `POST /api/fake-job/detect`
- `POST /api/resume-ai/generate`

## Optional Streamlit

```powershell
python -m streamlit run backend/streamlit_app.py
```

Streamlit is local utility UI and does not require frontend auth.
