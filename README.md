# AI Recruitment Intelligence Platform

Full-stack recruitment intelligence system with:
- Resume parsing (skills, experience, education) using spaCy + keyword extraction
- Domain-wise employability probability from resume analysis
- Resume overview and downloadable analyzed report (TXT/JSON) in Resume Scanner
- Resume-to-job matching score
- Fake job detection using a trained ML model
- Enhanced JD analyzer insights (role family, seniority, required/preferred skills, JD quality)
- Hybrid fake-job scoring (ML + rule signals with risk drivers and confidence)
- ATS-style React dashboard for operational visibility
- Streamlit dashboard/workbench for local all-in-one usage

## Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: Flask REST API
- Local UI alternative: Streamlit
- ML: scikit-learn RandomForest classifier (trained artifact included)
- File parsing: PyPDF2, python-docx

## Project Structure

```text
.
|-- backend
|   |-- app.py
|   |-- streamlit_app.py
|   |-- requirements.txt
|   |-- Procfile
|   |-- .env.example
|   |-- ml
|   |   |-- feature_engineering.py
|   |   |-- train_fake_job_model.py
|   |   `-- fake_job_model.joblib
|   `-- services
|       |-- fake_job_detector.py
|       |-- file_extractors.py
|       |-- job_matching.py
|       |-- nlp_utils.py
|       `-- resume_parser.py
|-- frontend
|   |-- package.json
|   |-- vercel.json
|   |-- .env.example
|   `-- src
|       |-- App.jsx
|       |-- main.jsx
|       |-- index.css
|       |-- api/client.js
|       |-- components/*
|       `-- pages/*
|-- render.yaml
`-- README.md
```

## Backend Setup (Local)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python ml/train_fake_job_model.py
python app.py
```

Backend runs at: `http://localhost:5000`

## Streamlit Setup (Local)

Run the platform directly in Streamlit (no React dev server required):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python ml/train_fake_job_model.py
python -m streamlit run streamlit_app.py
```

Streamlit runs at: `http://localhost:8501`

Includes:
- Dashboard
- Resume Scanner (PDF/DOCX/TXT upload)
- Job Description Analyzer
- Fake Job Detection

## Frontend Setup (Local)

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs at: `http://localhost:5173`

Set `VITE_API_BASE_URL` in `frontend/.env` if backend URL changes.

## API Endpoints

- `GET /api/health`
- `POST /api/resume/parse` (multipart: `resume`)
  - Includes `domain_analysis` with strongest domain tendency, per-domain probability, and missing skills
- `POST /api/job/analyze` (json: `job_description`)
- `POST /api/job/match`
  - multipart: `resume`, `job_description`
  - or json: `job_description` + `resume_parsed` or `resume_text`
- `POST /api/fake-job/detect` (json: `job_url`, optional `job_text`)

## Fake Job ML Model

The fake job model uses engineered features including:
- Salary anomalies
- Missing company info
- Suspicious keywords
- Urgent language patterns
- Free email contact usage
- URL suspiciousness

Trained artifact file:
- `backend/ml/fake_job_model.joblib`

Retrain anytime:

```powershell
cd backend
python ml/train_fake_job_model.py
```

## Deployment

### Frontend -> Vercel

1. Import `frontend` as a Vercel project.
2. Build command: `npm run build`
3. Output directory: `dist`
4. Set env var: `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com`

### Backend -> Render

Use the included `render.yaml` (Blueprint deploy) or configure manually:
- Root Directory: `backend`
- Build Command:
  - `pip install -r requirements.txt && python -m spacy download en_core_web_sm && python ml/train_fake_job_model.py`
- Start Command:
  - `gunicorn app:app`
- Environment Variable:
  - `CORS_ORIGINS=https://<your-vercel-app>.vercel.app`

## Notes

- Resume parsing supports PDF, DOCX, and TXT uploads.
- Fake-job URL scraping may fail on heavily protected pages; submit fallback `job_text` when needed.
- Dashboard metrics persist in browser localStorage for quick ATS-style tracking.
