# ProjectData – Data Science Copilot

> Turn raw CSVs into explainable insights, interactive visuals, and conversational answers.

![Status](https://img.shields.io/badge/status-active-success)
![Node](https://img.shields.io/badge/node-%5E18-339933)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-ISC-blue)

---

## Table of Contents
- [Highlights](#highlights)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Project Layout](#project-layout)
- [Environment Variables](#environment-variables)
- [Core Workflows](#core-workflows)
- [API Surface](#api-surface)
- [AI Question Answering](#ai-question-answering)
- [Analytics & Visualization Engines](#analytics--visualization-engines)
- [Quality & Testing](#quality--testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Highlights

- **End-to-end data workspace** – Upload, profile, clean, visualize, and export datasets in a single flow.
- **LLM-powered copilot** – LangGraph orchestrates Gemini, OpenAI, or GitHub Models to answer natural language questions about your data.
- **Opinionated defaults, flexible overrides** – Choose analysis modes (summary, trends, anomalies, correlations, insights) or jump straight into chat mode.
- **Production-ready backend** – Express 5 API with hardened CORS, Helmet, file validation, and Firebase hooks for persistence.
- **Python analytics engine** – Pandas pipelines, AutoViz, SweetViz, and LangGraph live alongside targeted validation and test suites.
- **Deploy-friendly tooling** – Cross-platform scripts (`start-dev.*`, `run-local.*`, `stop-servers.bat`) make it easy to spin up or tear down the stack.

---

## System Architecture

```
┌────────────┐       HTTPS        ┌──────────────┐      spawn / IPC      ┌────────────────────┐
│ React UI   │ ─────────────────▶ │ Express API  │ ─────────────────────▶ │ Python Analytics   │
│ (frontend) │                    │ (backend)    │                        │ LangGraph + Pandas │
└────────────┘                    └──────────────┘                        └────────┬──────────┘
                                                                                │
                                                                                ▼
                                                                     Managed LLM Providers
                                                            (Gemini ▸ Azure/OpenAI ▸ GitHub Models)
```

- Uploaded CSVs are stored under `backend/uploads/` and validated before processing.
- The backend orchestrates AutoViz/SweetViz generation and forwards chat prompts to the Python LangGraph engine.
- LangGraph builds a state graph: load → validate → profile → statistics → (optional) LLM answer → recommendations.
- Provider selection respects `LLM_PROVIDER` overrides and surfaces structured errors if the chosen model fails.

---

## Quick Start

### 1. Clone & bootstrap

```powershell
# choose a workspace directory first
git clone <repository-url>
cd ProjectData
```

### 2. Install dependencies

```powershell
# Backend (Node)
cd backend
npm install

# Python analytics
cd scripts
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt

deactivate
cd ../..

# Frontend (React)
cd frontend
npm install
cd ..
```

### 3. Configure environment

1. Copy `backend/.env` from `backend/.env.example` (create one if absent) and populate keys (see [Environment Variables](#environment-variables)).
2. Never commit real secrets—`.env` is already in `.gitignore`.

### 4. Run everything

**Windows (PowerShell):**
```powershell
# From project root
./start-dev.bat
```

**macOS / Linux:**
```bash
# From project root
chmod +x start-dev.sh
./start-dev.sh
```

Scripts start the backend API, launch the frontend, and ensure the Python environment is ready. Stop all services with `./stop-servers.bat` or `./stop-servers.sh`.

---

## Project Layout

```
ProjectData/
├─ backend/
│  ├─ server.js               # Express 5 API (upload, insights, LLM chat, viz routers)
│  ├─ config/
│  │  └─ firebase.js          # Firebase admin bootstrap (optional persistence)
│  ├─ scripts/
│  │  ├─ langgraph_analyzer.py # LangGraph state graph for analytics + chat
│  │  ├─ autoviz_generator.py  # AutoViz automation
│  │  ├─ sweetviz_generator.py # SweetViz automation
│  │  ├─ bloom_analyzer.py     # Legacy Bloom pipeline (optional)
│  │  └─ requirements.txt     # Python dependencies
│  └─ uploads/                # User CSV staging area (gitignored)
│
├─ frontend/
│  ├─ src/                    # React application
│  ├─ public/
│  └─ package.json
│
├─ data_cleaning.txt          # Research notes & backlog
├─ start-dev.*                # Cross-platform dev launcher scripts
├─ run-local.bat              # Backend-only quick start
└─ README.md
```

---

## Environment Variables

Create `backend/.env` with the variables that apply to your deployment:

| Variable | Required | Description |
| --- | --- | --- |
| `PORT` | No (default `5000`) | Express server port |
| `NODE_ENV` | No | `development` or `production` |
| `FRONTEND_URL` | No | Origin allowed by CORS (default `http://localhost:3000`) |
| `MONGODB_URI` | Optional | MongoDB connection string if you enable persistence |
| `PYTHON_PATH` | Optional | Absolute path to the Python interpreter used by analytics |
| `MAX_FILE_SIZE` | Optional | Upload limit in bytes (default 100 MB) |
| `UPLOAD_DIR` | Optional | Relative path to store uploaded files |
| `LLM_PROVIDER` | Optional | Force provider: `gemini`, `azure`, `openai`, or `github` |
| `LLM_MODEL` | Optional | Override model name for OpenAI/Azure/GitHub |
| `GEMINI_MODEL` | Optional | Override Gemini model (defaults to `gemini-1.5-flash`) |
| `GEMINI_API_KEY` | ✅ for Gemini | Google Generative AI key |
| `OPENAI_API_KEY` | ✅ for OpenAI | OpenAI platform key |
| `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_KEY` | ✅ for Azure | Azure OpenAI resource credentials |
| `GITHUB_TOKEN` | ✅ for GitHub Models | Personal access token with `models` scope |

> 💡 Tip: keep provider credentials mutually exclusive in local testing to avoid ambiguity. When `LLM_PROVIDER` is set, the system skips fallback logic and returns structured errors if the provider is unavailable.

---

## Core Workflows

1. **Upload & validate** – CSV constraints enforced (path safety, file size, row limits). Metadata includes missing values, duplicates, column types, and memory footprint.
2. **Profile** – Statistical summaries for numeric & categorical columns with configurable limits.
3. **Visualize** – AutoViz and SweetViz jobs produce assets under `backend/visualizations/` and expose them through `/api/visualizations`.
4. **AI analysis modes** – LangGraph modes (`summary`, `trends`, `insights`, `anomalies`, `correlations`) generate narrative insights and recommendations without LLM calls.
5. **Conversational chat** – `analysis_type=chat` hands off to `answer_question_with_llm`, optionally delivering deterministic, rule-based answers before hitting the LLM.

---

## API Surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Service heartbeat + uptime stats |
| `POST` | `/api/upload` | Multipart CSV upload |
| `POST` | `/api/analyze` | Mock statistical analysis (legacy path) |
| `POST` | `/api/visualize` | Sample visualisation payloads |
| `POST` | `/api/generate-autoviz` | Kick off AutoViz generation |
| `POST` | `/api/generate-sweetviz` | Kick off SweetViz generation |
| `POST` | `/api/generate-ai-insights` | Run LangGraph analysis in selected mode |
| `POST` | `/api/ask-question` | Conversational Q&A backed by LangGraph LLM node |
| `GET` | `/api/jobs` | Firestore job history (optional feature flag) |

All responses follow `{ success, message?, error?, data? }` and bubble up validation hints when requests are malformed.

---

## AI Question Answering

- **Rule-based guardrails** answer common queries (missing values, duplicate counts, column lists) instantly—no LLM token usage.
- **Provider priority** defaults to Gemini → Azure → OpenAI → GitHub Models when matching credentials are present.
- **Forced provider mode** (`LLM_PROVIDER`) suppresses fallback answers. If the provider fails, the API returns a structured message describing what went wrong so users can fix credentials without misinformation.
- **Context payload** includes dataset schema, statistics, and a 5-row preview to keep responses grounded.
- **Timeout protection**: backend enforces a 60 s deadline and returns HTTP 408 for runaway prompts.

---

## Analytics & Visualization Engines

| Engine | Where | Notes |
| --- | --- | --- |
| **LangGraph** | `backend/scripts/langgraph_analyzer.py` | Stateful analysis graph, chat mode, provider orchestration |
| **AutoViz** | `backend/scripts/autoviz_generator.py` | Automated chart packs (PNG/HTML) |
| **SweetViz** | `backend/scripts/sweetviz_generator.py` | Rich, shareable HTML EDA reports |
| **Bloom Analyzer** | `backend/scripts/bloom_analyzer.py` | Legacy experimental workflow (disabled by default) |

To run LangGraph manually:
```powershell
cd backend/scripts
./venv/Scripts/Activate.ps1
python langgraph_analyzer.py ../uploads/sample.csv summary
```

---

## Quality & Testing

- **Python validation**: `python -m pytest test_validation.py` (inside `backend/scripts/`, with venv active)
- **Linting (optional)**: integrate `ruff` or `flake8` for Python, and ESLint for the frontend (config scaffolding ready).
- **Smoke tests**: `curl http://localhost:5000/api/health` after boot, upload a sample CSV, then hit `/api/ask-question`.
- **CI suggestion**: add a workflow running `npm test` (frontend) and `pytest` (analytics) before deployments.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `Error: listen EADDRINUSE: :::5000` | Port already in use | `Stop-Process -Name node` (Windows) or `lsof -ti:5000 | xargs kill` (macOS/Linux) and retry |
| `MongooseError: Operation buffering timed out` | MongoDB not reachable | Start local MongoDB or update `MONGODB_URI` |
| `LLM provider failed` | Invalid or missing API key | Check `.env`, regenerate token, or switch provider | 
| Python script exits non-zero | venv inactive or deps missing | Reactivate venv and run `pip install -r requirements.txt` |
| Frontend throws `digital envelope routines` error | Node >=17 without OpenSSL flag | Install/use Node 18 LTS (`nvm use 18`) |

---

## Contributing

1. Fork the repository and create a feature branch.
2. Keep `.env` files and uploaded datasets out of git history.
3. Run the backend, Python analytics, and frontend locally before opening a pull request.
4. Document significant behavioural changes (especially LLM provider logic) in this README.

Maintained with ❤️ by Hasnain & collaborators. Reach out via issues for feature requests or bug reports.
