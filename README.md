---
title: AI Paper Summarizer Pro
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# AI Paper Summarizer Pro

Research paper summarizer with AI (Gemini 2.5 Flash). PDF/TXT/URL input, Urdu/English support, structured research extraction (methodology, findings, gaps, citations), Q&A, comparison, PDF export, ArXiv search, thesis proposal generator.

## Quick Start

### Local
```bash
pip install -r requirements.txt
python run.py
# → http://localhost:8501
```

Or double-click `run.bat`.

### F5 in VS Code
Open `frontend/app.py` → `F5` (starts backend automatically via `__main__`)

## Project Structure
```
├── backend/       FastAPI API server (port 8001)
├── frontend/      Streamlit UI (port 8501)
├── flutter_app/   Flutter mobile app (source only)
├── run.py         Launcher (starts both services)
├── Dockerfile     Deploy to Hugging Face Spaces
└── requirements.txt
```

## Deploy (Free — Single Public URL)

### Option 1: Hugging Face Spaces (recommended)
1. Create account at https://huggingface.co
2. New Space → Docker → `https://github.com/YOUR_USER/ai-paper-summarizer`
3. Set secret: `GEMINI_API_KEY`
4. Deploy — gets URL like `https://YOUR_USER-ai-paper-summarizer.hf.space`

### Option 2: Streamlit Cloud + Render
1. **Frontend**: Push to GitHub → https://streamlit.io/cloud → Deploy `frontend/app.py`
2. **Backend**: https://render.com → New Web Service → `backend/` → Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. Set `GEMINI_API_KEY` and `API_URL` as secrets

## Env Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (hardcoded) | Google Gemini API key |
| `API_URL` | http://localhost:8001 | Backend URL |

## Features
- PDF/TXT/URL input (up to 50MB)
- English & Urdu summaries
- Structured research extraction (methodology, findings, gaps, strengths, weaknesses, future directions)
- Q&A with paper context ("Ask the Paper")
- Paper comparison
- PDF/Markdown/JSON/TXT export
- Reading time & complexity
- ArXiv paper search
- Thesis proposal generator
- Citation formatting (APA)
- History management
- Dark/Light mode
