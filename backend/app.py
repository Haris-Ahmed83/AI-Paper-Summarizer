"""
AI Research Paper Summarizer v3.1
Backend - FastAPI + Groq/Grok REST API (no library)
Supports: PDF, TXT | Large files | Citations | Export
"""

import os, re, uuid, json, sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import PyPDF2
import requests as http_requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# ─── Config ───
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DB_PATH = BASE_DIR / "history.db"

# Groq keys (primary)
GROQ_KEYS = [k.strip() for k in (
    os.environ.get("GROQ_API_KEYS") or
    os.environ.get("GROQ_API_KEY") or
    ""
).split(",") if k.strip()]
for i in range(2, 10):
    k = os.environ.get(f"GROQ_API_KEY_{i}")
    if k: GROQ_KEYS.append(k.strip())

# Grok (xAI) keys (fallback)
GROK_KEYS = [k.strip() for k in (
    os.environ.get("GROK_API_KEYS") or
    os.environ.get("GROK_API_KEY") or
    ""
).split(",") if k.strip()]
for i in range(2, 10):
    k = os.environ.get(f"GROK_API_KEY_{i}")
    if k: GROK_KEYS.append(k.strip())

# Gemini keys (fallback)
GEMINI_KEYS = [k.strip() for k in (
    os.environ.get("GEMINI_API_KEYS") or
    os.environ.get("GEMINI_API_KEY") or
    ""
).split(",") if k.strip()]
for i in range(2, 10):
    k = os.environ.get(f"GEMINI_API_KEY_{i}")
    if k: GEMINI_KEYS.append(k.strip())

if not GROQ_KEYS and not GROK_KEYS:
    raise RuntimeError("At least one API key required: GROQ_API_KEY or GROK_API_KEY")

GROK_MODEL = os.environ.get("GROK_MODEL", "grok-3-mini")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_FILE_MB = int(os.environ.get("MAX_FILE_MB", "50"))
CHUNK_SIZE = 5000

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── FastAPI ───
app = FastAPI(title="AI Paper Summarizer Pro", version="3.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Database ───
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS summaries (
                id TEXT PRIMARY KEY, filename TEXT, filesize INTEGER, filetype TEXT,
                source_url TEXT DEFAULT '',
                title TEXT, summary TEXT, key_points TEXT DEFAULT '[]',
                citations TEXT DEFAULT '[]', source_text TEXT DEFAULT '',
                methodology TEXT DEFAULT '', key_findings TEXT DEFAULT '[]',
                research_gaps TEXT DEFAULT '[]', future_directions TEXT DEFAULT '[]',
                strengths TEXT DEFAULT '[]', weaknesses TEXT DEFAULT '[]',
                conclusion TEXT DEFAULT '', difficulty_level TEXT DEFAULT 'Intermediate',
                key_terms TEXT DEFAULT '[]',
                language TEXT, summary_type TEXT, word_count INTEGER,
                processing_time REAL, created_at TEXT
            );
        """)
        # Add columns for existing DBs
        for col in ["source_url","source_text","methodology","key_findings","research_gaps","future_directions","strengths","weaknesses","conclusion","difficulty_level","key_terms"]:
            try: conn.execute(f"ALTER TABLE summaries ADD COLUMN {col} TEXT DEFAULT ''")
            except: pass
        for col in ["research_objective","novelty","practical_implications","key_takeaways"]:
            try: conn.execute(f"ALTER TABLE summaries ADD COLUMN {col} TEXT DEFAULT ''")
            except: pass
init_db()

# ─── Multi-Provider AI Call (Groq + optional Grok) ───
PROVIDERS = []
GROQ_CLIENTS = []
for k in GROQ_KEYS:
    PROVIDERS.append({"type":"groq","key":k,"model":GROQ_MODEL})
    try:
        from groq import Groq
        GROQ_CLIENTS.append(Groq(api_key=k))
    except ImportError:
        pass
for k in GROK_KEYS:
    PROVIDERS.append({"type":"grok","key":k,"model":GROK_MODEL})
for k in GEMINI_KEYS:
    PROVIDERS.append({"type":"gemini","key":k,"model":"gemini-2.5-flash"})
if not PROVIDERS:
    raise RuntimeError("No API keys found. Set GROQ_API_KEY, GEMINI_API_KEY, or GROK_API_KEY.")

# ─── AI Chat (REST-based, multi-provider) ───
def ai_chat(prompt: str, retry: int = 1, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> str:
    errors = {}
    for attempt in range(retry + 1):
        last_err = None
        for p in PROVIDERS:
            try:
                if p["type"] == "grok":
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"}
                    msgs = []
                    if system_prompt:
                        msgs.append({"role": "system", "content": system_prompt})
                    msgs.append({"role": "user", "content": prompt})
                    payload = {"model": p["model"], "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}
                    resp = http_requests.post(url, json=payload, headers=headers, timeout=90)
                    if resp.status_code == 429:
                        last_err = f"grok_quota"; errors["grok"] = f"429"; continue
                    if resp.status_code != 200:
                        err = resp.text[:200]
                        if "quota" in err.lower() or "rate" in err.lower():
                            last_err = f"grok_quota"; errors["grok"] = err[:80]; continue
                        raise Exception(f"Grok err {resp.status_code}: {err}")
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise Exception("Empty Grok response")
                    return choices[0].get("message",{}).get("content","")

                elif p["type"] == "groq":
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"}
                    msgs = []
                    if system_prompt:
                        msgs.append({"role": "system", "content": system_prompt})
                    msgs.append({"role": "user", "content": prompt})
                    payload = {"model": p["model"], "messages": msgs, "max_tokens": max_tokens, "temperature": temperature}
                    resp = http_requests.post(url, json=payload, headers=headers, timeout=90)
                    if resp.status_code == 429:
                        last_err = f"groq_quota"; errors["groq"] = f"429"; continue
                    if resp.status_code == 413:
                        last_err = f"groq_too_large"; errors["groq"] = f"413"; continue
                    if resp.status_code != 200:
                        err = resp.text[:200]
                        if "quota" in err.lower() or "rate" in err.lower():
                            last_err = f"groq_quota"; errors["groq"] = err[:80]; continue
                        raise Exception(f"Groq err {resp.status_code}: {err}")
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise Exception("Empty Groq response")
                    return choices[0].get("message",{}).get("content","")

                elif p["type"] == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent?key={p['key']}"
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    resp = http_requests.post(url, json=payload, timeout=90)
                    if resp.status_code == 429:
                        last_err = f"gemini_quota"; errors["gemini"] = f"429"; continue
                    if resp.status_code != 200:
                        err = resp.text[:200]
                        if "quota" in err.lower():
                            last_err = f"gemini_quota"; errors["gemini"] = err[:80]; continue
                        raise Exception(f"Gemini err {resp.status_code}: {err}")
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise Exception("Empty Gemini response")
                    return candidates[0].get("content",{}).get("parts",[{}])[0].get("text","")

            except Exception as e:
                last_err = str(e)
                errors[p.get('type','?')] = str(e)[:80]
                continue
        if attempt < retry:
            import time
            time.sleep(30)
        else:
            err_msg = str(errors)
            raise Exception(f"ALL_FAILED: {err_msg}")

# ─── Models ───
class SummaryResponse(BaseModel):
    id: str; filename: str; filesize: int; filetype: str
    title: str; summary: str; methodology: str = ""
    key_findings: list = []; research_gaps: list = []
    future_directions: list = []; strengths: list = []
    weaknesses: list = []; conclusion: str = ""
    difficulty_level: str = "Intermediate"
    key_terms: list = []; key_points: list = []
    citations: list = []
    research_objective: str = ""; novelty: str = ""
    practical_implications: str = ""; key_takeaways: list = []
    language: str; summary_type: str; word_count: int
    processing_time: float; created_at: str
    source_url: str = ""

class HistoryItem(BaseModel):
    id: str; filename: str; title: str; filetype: str
    language: str; filesize: int; created_at: str
    source_url: str = ""

# ─── PDF Processing ───
def extract_text_pdf(path: str) -> str:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    text += page_text + "\n"
        if len(text.strip()) > 100:
            text = _clean_extracted_text(text)
            return text.strip()
    except Exception:
        pass
    # Fallback to PyPDF2
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        text = _clean_extracted_text(text)
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF extraction failed: {e}")

def _clean_extracted_text(text: str) -> str:
    """Universal text cleaner — fixes PDF extraction artifacts."""
    if not text: return text
    # Medical/tech terms
    terms = {
        r'\bm\s+[Hh]ealth\b': 'mHealth', r'\be\s+[Hh]ealth\b': 'eHealth',
        r'\btel\s*e\s*[Hh]ealth\b': 'Telehealth', r'\btel\s*e\s*[Mm]edicine\b': 'Telemedicine',
        r'\btel\s*e\s*[Cc]are\b': 'Telecare', r'\bai\s+[Pp]owered\b': 'AI-powered',
        r'\bml\s+[Mm]odel\b': 'ML model', r'\bnlp\s+[Tt]ask\b': 'NLP task',
        r'\bllm\s+[Mm]odel\b': 'LLM model', r'\bgpt\s*-\s*4\b': 'GPT-4',
        r'\bgpt\s*-\s*3\b': 'GPT-3', r'\bchat\s*gpt\b': 'ChatGPT',
        r'\bcovid\s*-\s*19\b': 'COVID-19',
    }
    for pat, repl in terms.items():
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    # Hyphen breaks
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Line breaks mid-sentence
    text = re.sub(r'(?<=[a-z])\n(?=[a-z])', ' ', text)
    # URL fixes
    text = re.sub(r'doi\.\s*org', 'doi.org', text, flags=re.IGNORECASE)
    text = re.sub(r'http\s*s\s*://', 'https://', text)
    # Common merged words
    text = re.sub(r'ac\s+cessed', 'accessed', text, flags=re.IGNORECASE)
    text = re.sub(r'avail\s+able', 'available', text, flags=re.IGNORECASE)
    text = re.sub(r'onl\s+ine', 'online', text, flags=re.IGNORECASE)
    text = re.sub(r'accessedon', 'accessed on', text)
    text = re.sub(r'Availableonline', 'Available online', text)
    # Fix colon spacing
    text = re.sub(r'(?<=[a-zA-Z]):(?=[A-Z])', r': ', text)
    # Multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    return text

def extract_text_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text(path: str, ftype: str) -> str:
    if ftype == "pdf": return extract_text_pdf(path)
    elif ftype == "txt": return extract_text_txt(path)
    raise ValueError(f"Unsupported file type: {ftype}")

def chunk_text(text: str, size: int = CHUNK_SIZE) -> list:
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

def extract_citations(text: str) -> list:
    """Extract references section from full text."""
    match = re.search(r'(?:^|\n)(References|Bibliography)(.*)', text, re.DOTALL | re.IGNORECASE)
    if not match:
        pattern = r'(?:https?://doi\.org/\S+|\(?\d{4}\)?\.\s+[A-Z][^.]*?Journal[^.]*\.)'
        matches = re.findall(pattern, text)
        return [m.strip() for m in matches[:10]] if matches else []

    refs_block = match.group(2).strip()
    # Stop at disclaimer/legal text
    refs_block = re.split(r'\n\s*(Disclaimer|Publisher|©|Conflict|Funding|Institutional Review|Data Availability)', refs_block)[0]

    # Split numbered references: "1." or "[1]" format
    parts = re.split(r'\n\s*(\d+)\.\s+', refs_block)
    if len(parts) < 3:
        parts = re.split(r'\n\s*\[\d+\]\s*', refs_block)
        if len(parts) < 2:
            return []

    references = []
    i = 1
    while i < len(parts) - 1:
        num = parts[i].strip()
        content = parts[i+1].strip()
        content = re.sub(r'\s+', ' ', content)
        if len(content) > 30 and re.search(r'\d{4}', content):
            # Strip raw URLs, link DOIs separately
            raw_doi = ""
            doi_m = re.search(r'(https?://doi\.org/\S+)', content)
            if doi_m:
                raw_doi = doi_m.group(1)
                content = re.sub(r'https?://doi\.org/\S+', '', content)
            content = re.sub(r'https?://\S+', '', content)
            content = re.sub(r'\s+', ' ', content).strip()
            content = re.sub(r'[,;:\s]+$', '', content)
            content = content.replace('[Cross Ref]', '[CrossRef]')
            content = content.replace('[Pub Med]', '[PubMed]')
            content = content.replace('[Pub Med Central]', '[PMC]')
            content = re.sub(r'(?<=[a-zA-Z])\.(?=[A-Z][a-z])', '. ', content)
            if raw_doi:
                content = re.sub(r'DOI[:\s]*$', '', content).strip()
                content += f' <a href="{raw_doi}" style="color:var(--accent);font-size:12px;text-decoration:none;white-space:nowrap;">[DOI]</a>'
            references.append(content)
        i += 2
    # Deduplicate by normalized content
    seen = {}
    deduped = []
    for ref in references:
        key = re.sub(r'<[^>]+>', '', ref).strip().lower()[:100]
        if key not in seen:
            seen[key] = True
            deduped.append(ref)
    return deduped[:20]

def extract_references_via_ai(text: str) -> list:
    """Extract references using AI from the last part of the paper."""
    last_chunk = text[-4000:] if len(text) > 4000 else text
    prompt = f"""Extract ALL academic references from the text below. Format each reference as a proper numbered academic citation. Include: Authors, Title, Journal/Conference, Year, DOI/URL if present. Return ONLY the numbered list. No commentary, no extra text. If a reference is incomplete, include what is available.

TEXT:
{last_chunk}"""
    try:
        raw = ai_chat(prompt, system_prompt="You are an academic reference extractor. Return ONLY a clean numbered list of references. No commentary. No extra text.", temperature=0.1)
        skip_phrases = ["here is","here are","the following","formatting","as requested","please note","i have","below is","list of","absolutely","certainly"]
        refs = []
        for line in raw.strip().split("\n"):
            line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
            if not line or len(line) < 40: continue
            if any(p in line.lower() for p in skip_phrases): continue
            refs.append(line)
        if refs:
            return refs[:20]
    except:
        pass
    return []

def clean_citations_with_ai(citations: list) -> list:
    """Use AI to clean and fix spacing in extracted references."""
    if not citations:
        return citations
    try:
        block = "\n".join(f"{i+1}. {r}" for i, r in enumerate(citations))
        prompt = f"""Fix spacing and formatting in these academic references. Fix merged words (e.g. "Healthand" → "Health and"), split joined words properly. Keep all content unchanged - only fix spacing. Return as a numbered list preserving the original numbering.

References:
{block}"""
        resp = ai_chat(prompt)
        skip_phrases = ["here is the list","here are the","formatting adjustments","as requested","please note","the following","certainly","absolutely","i'll","i have","sure","of course","let me","below is","above is"]
        cleaned = []
        for line in resp.strip().split("\n"):
            line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
            if not line or len(line) <= 30: continue
            if any(p in line.lower() for p in skip_phrases): continue
            cleaned.append(line)
        if len(cleaned) >= len(citations) // 2:
            return cleaned[:len(citations)]
    except:
        pass
    return citations

def extract_title(text: str) -> str:
    """3-layer title extraction — har PDF pe kaam karta hai."""
    chunk = text[:3000]
    # Layer 1: Regex patterns
    patterns = [
        r'^([A-Z][A-Z\s:,\-]{20,150}[A-Z])\n',
        r'^([A-Z][a-zA-Z\s:,\-]{20,150})\n',
    ]
    bad = ('received','accepted','published','copyright','editorial','doi','http','volume','journal','page','figure','table','note','keywords','introduction','background','email','correspondence','submitted','this special','this paper','this study','the paper','the study','the authors','in this','we present','we propose','following','based on','abstract')
    skip_chars = ['∗','†','‡','◇','♡','♥','@','.com','doi.org','http','©','ISSN','ISBN','[1]','[2]','[3]']
    for pat in patterns:
        m = re.search(pat, chunk, re.MULTILINE)
        if m:
            c = m.group(1).strip()
            if not any(w in c.lower() for w in bad) and not any(ch in c for ch in skip_chars) and len(c) > 20:
                return _clean_extracted_text(c)[:300]
    # Layer 2: AI extraction
    wrong = ['special issue','second edition','first edition','volume','journal of','proceedings of']
    for _ in range(2):
        try:
            raw = ai_chat(f"Extract the main paper title:\n\n{chunk}",
                          system_prompt="Extract the MAIN paper/article/editorial title only. NOT the journal name, NOT the special issue name, NOT section headings. The title is usually the longest prominent heading. Return ONLY the title, nothing else.",
                          temperature=0.0, max_tokens=80)
            title = raw.strip().strip("\"'")
            title = re.sub(r'\s+', ' ', title)
            if any(w in title.lower() for w in wrong):
                raw = ai_chat(f"The main article title only (not the special issue name):\n\n{chunk}",
                              system_prompt="Extract ONLY the editorial/article title. Ignore special issue names, journal names, and edition names.",
                              temperature=0.0, max_tokens=80)
                title = raw.strip().strip("\"'")
                title = re.sub(r'\s+', ' ', title)
            if len(title) > 15:
                return title[:300]
        except:
            pass
    return "Research Paper"

def extract_title_via_ai(text: str) -> str:
    """Direct AI title extraction (used as fallback)."""
    chunk = text[:3000]
    wrong = ['special issue','second edition','first edition','volume','journal of','proceedings of']
    for _ in range(2):
        try:
            raw = ai_chat(f"Extract the main paper title:\n\n{chunk}",
                          system_prompt="Extract the MAIN paper/article/editorial title only. NOT the journal name, NOT the special issue name, NOT section headings. Return ONLY the title.",
                          temperature=0.0, max_tokens=80)
            title = raw.strip().strip("\"'")
            title = re.sub(r'\s+', ' ', title)
            if any(w in title.lower() for w in wrong):
                raw = ai_chat(f"The main article title only:\n\n{chunk}",
                              system_prompt="Extract ONLY the editorial/article title. Ignore special issue names, journal names, and edition names.",
                              temperature=0.0, max_tokens=80)
                title = raw.strip().strip("\"'")
                title = re.sub(r'\s+', ' ', title)
            if len(title) > 15:
                return title[:300]
        except:
            pass
    return "Research Paper"

def fetch_url_text(url: str) -> str:
    blocked_domains = ["mdpi.com", "elsevier.com", "sciencedirect.com", "springer.com", "tandfonline.com", "wiley.com", "ieee.org", "acm.org", "nature.com"]
    for d in blocked_domains:
        if d in url.lower():
            raise Exception(f"BLOCKED_PUBLISHER: {d} blocks automated access. Download the paper and upload PDF directly.")
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    last_err = None
    for ua in user_agents:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        try:
            resp = http_requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            for tag in soup.find_all(["article", "main"]):
                text = tag.get_text(separator="\n")
                if len(text.strip()) > 200:
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    return "\n".join(lines)
            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception as e:
            last_err = e
            continue
    raise Exception(f"Failed to fetch URL after multiple attempts: {last_err}")

def parse_json_from_text(raw: str) -> dict:
    """Try JSON parse, fall back to section-header extraction."""
    # Direct JSON attempt - object
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except:
            pass
    # Try JSON array at top level
    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            arr = json.loads(cleaned)
            if isinstance(arr, list):
                return {"summary": arr[0] if arr else ""}
        except:
            pass
    # Section-header fallback: extract by headers
    result = {}
    sections = {
        "summary": r"##?\s*Summary\s*\n(.+?)(?=\n##|\Z)",
        "methodology": r"##?\s*Methodology\s*\n(.+?)(?=\n##|\Z)",
        "key_findings": r"##?\s*Key Findings?\s*\n(.+?)(?=\n##|\Z)",
        "research_gaps": r"##?\s*Research Gaps?\s*\n(.+?)(?=\n##|\Z)",
        "future_directions": r"##?\s*Future Directions?\s*\n(.+?)(?=\n##|\Z)",
        "strengths": r"##?\s*Strengths?\s*\n(.+?)(?=\n##|\Z)",
        "weaknesses": r"##?\s*Weaknesses?\s*\n(.+?)(?=\n##|\Z)",
        "conclusion": r"##?\s*Conclusion\s*\n(.+?)(?=\n##|\Z)",
        "difficulty_level": r"(?:Difficulty|Level)[:\s]+(Beginner|Intermediate|Advanced)",
        "key_points": r"##?\s*Key Points?\s*\n(.+?)(?=\n##|\Z)",
    }
    for key, pat in sections.items():
        m = re.search(pat, raw, re.DOTALL | re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Handle JSON array values like ["text"]
            if val.startswith('["') and val.endswith('"]'):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list) and parsed:
                        val = parsed[0] if isinstance(parsed[0], str) else str(parsed[0])
                except:
                    val = val.strip('["]')
            if key in ("key_findings", "research_gaps", "future_directions", "strengths", "weaknesses", "key_points"):
                result[key] = [x.strip().lstrip("-*") for x in val.split("\n") if x.strip() and len(x.strip()) > 5]
            elif key == "difficulty_level":
                result[key] = val
            else:
                result[key] = val
    return result

def parse_advanced_summary(raw: str) -> dict:
    """Extract sections from advanced prompt response using regex."""
    result = {}
    patterns = {
        "summary": r"## SUMMARY\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "key_takeaways": r"## KEY TAKEAWAYS\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "research_objective": r"## RESEARCH OBJECTIVE\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "methodology": r"## RESEARCH METHODOLOGY\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "key_findings": r"## KEY FINDINGS.*?\n(.*?)(?=\n## [A-Z]|\Z)",
        "novelty": r"(?:### |\*\*)?Novelty Assessment\s*\n(.*?)(?=\n## [A-Z]|\n###|\Z)",
        "research_gaps": r"## RESEARCH GAPS.*?\n(.*?)(?=\n## [A-Z]|\Z)",
        "future_directions": r"## FUTURE DIRECTIONS\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "practical_implications": r"## PRACTICAL IMPLICATIONS\s*\n(.*?)(?=\n## [A-Z]|\Z)",
        "conclusion": r"## CONCLUSION.*?\n(.*?)(?=\n## [A-Z]|\Z)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, raw, re.DOTALL | re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if key in ("key_takeaways", "key_findings", "research_gaps", "future_directions"):
                result[key] = [x.strip().lstrip("•-*✦▸123456789.").strip()
                               for x in val.split("\n")
                               if x.strip() and len(x.strip()) > 8]
            else:
                result[key] = val
    # Parse strengths & weaknesses from Critical Analysis section
    ca = re.search(r"## CRITICAL ANALYSIS\s*\n(.*?)(?=\n## [A-Z]|\Z)", raw, re.DOTALL | re.IGNORECASE)
    if ca:
        body = ca.group(1)
        s_m = re.search(r"(?:### |\*\*)?Strengths?\s*\n(.*?)(?=\n(?:### |\*\*)?(?:Weakness|Novelty)|\Z)", body, re.DOTALL | re.IGNORECASE)
        w_m = re.search(r"(?:### |\*\*)?Weaknesses?.*?\n(.*?)(?=\n(?:### |\*\*)?(?:Novelty)|\Z)", body, re.DOTALL | re.IGNORECASE)
        if s_m:
            result["strengths"] = [x.strip().lstrip("•-*✦").strip()
                                   for x in s_m.group(1).split("\n") if x.strip() and len(x.strip()) > 8]
        if w_m:
            result["weaknesses"] = [x.strip().lstrip("•-*✦").strip()
                                    for x in w_m.group(1).split("\n") if x.strip() and len(x.strip()) > 8]
    return result

# ─── AI Summary (Advanced) ───
def generate_summary(text: str, lang: str = "english", stype: str = "detailed") -> dict:
    lang_inst = {"english":"Respond in English only.","urdu":"اردو میں جواب دیں۔","both":"Respond in both English and Urdu."}.get(lang, "Respond in English only.")
    type_map = {
        "brief": "concise 3-4 paragraph overview covering the core contribution only",
        "detailed": "extremely detailed, PhD/MPhil level academic analysis with all structured sections",
        "bullet": "bullet points only, maximum 8 points"
    }
    depth = type_map.get(stype, "detailed academic analysis")

    # More text for better analysis — llama-3.3-70b has 128K context
    MAX_CHARS = 12000
    if len(text) > MAX_CHARS:
        intro = text[:4000]
        middle = text[4000:MAX_CHARS]
        text = intro + "\n\n" + middle

    title = extract_title(text)
    if title == "Research Paper" or len(title) > 150 or '[' in title or title.startswith(("This ","The ")):
        ai_title = extract_title_via_ai(text)
        if ai_title != "Research Paper": title = ai_title

    if stype == "bullet":
        corpus = text[:8000]
        prompt = f"""## Paper: {title}
{depth}.
{lang_inst}

Use ONLY the text below. Be specific with numbers, datasets, models.

TEXT:
{corpus}"""
        raw = ai_chat(prompt, system_prompt="You are an expert academic analyst. Extract bullet points only.")
        return {"title": title, "summary": raw, "methodology": "", "key_findings": [],
                "research_gaps": [], "future_directions": [], "strengths": [],
                "weaknesses": [], "conclusion": "", "difficulty_level": "Intermediate",
                "key_terms": [], "key_points": [], "citations": [],
                "research_objective": "", "novelty": "", "practical_implications": "",
                "key_takeaways": []}

    corpus = text[:MAX_CHARS]
    prompt = f"""You are an expert academic research analyst with PhD-level expertise. Analyze the following research paper and provide a {depth}. {lang_inst}

STRICT RULES:
- Extract information ONLY from the provided text. Do NOT hallucinate.
- Be specific with numbers, datasets, models, percentages where mentioned.
- Use academic tone. Never start with "I" or "The paper says".
- Provide concrete, cited evidence for each claim.

Provide your analysis in this EXACT structure:

## SUMMARY
Write a comprehensive 150-200 word paragraph covering: what this paper is about, its core contribution, and why it matters academically.

## KEY TAKEAWAYS
List 5-7 specific, detailed bullet points. Each must be 1-2 sentences with specific details from the paper.

## RESEARCH OBJECTIVE
What specific problem does this paper solve? What gap does it address? (2-3 sentences)

## RESEARCH METHODOLOGY
Describe in detail: study design/approach, datasets used (names and sizes), models/tools/frameworks, evaluation metrics, sample sizes or language coverage if applicable.

## KEY FINDINGS & RESULTS
List 4-6 numbered findings with specific statistics, percentages, or quantitative results where available.

## CRITICAL ANALYSIS
### Strengths (2-3 points)
- What does this paper do exceptionally well?

### Weaknesses / Limitations (2-3 points)
- What are the methodological gaps or limitations?

### Novelty Assessment
- What is genuinely new about this research? (1-2 sentences)

## RESEARCH GAPS IDENTIFIED
List 2-3 specific gaps this paper itself acknowledges OR that you identify from the methodology.

## FUTURE DIRECTIONS
List 3-4 specific, actionable future research directions based on the paper's findings.

## PRACTICAL IMPLICATIONS
Who benefits from this research and how? (researchers, practitioners, policymakers, students)

## CONCLUSION & IMPLICATIONS
Write a 100-150 word paragraph synthesizing the paper's contribution to the field.

---
PAPER TITLE: {title}

PAPER TEXT:
{corpus}"""

    try:
        raw = ai_chat(prompt, system_prompt="You are an expert academic research analyst. Provide precise, detailed, PhD-level analysis. Never hallucinate. Extract only from provided text.")
    except Exception as e:
        raise

    data = parse_advanced_summary(raw)
    data["title"] = title
    data["citations"] = extract_references_via_ai(text) or clean_citations_with_ai(extract_citations(text))
    data["summary"] = data.get("summary", "").strip() or title
    data["methodology"] = data.get("methodology", "")
    data["conclusion"] = data.get("conclusion", "")
    data["difficulty_level"] = "Intermediate"
    data["key_terms"] = []
    data["key_points"] = data.get("key_takeaways", [])
    data["key_findings"] = data.get("key_findings", [])
    data["research_gaps"] = data.get("research_gaps", [])
    data["future_directions"] = data.get("future_directions", [])
    data["strengths"] = data.get("strengths", [])
    data["weaknesses"] = data.get("weaknesses", [])
    data["research_objective"] = data.get("research_objective", "")
    data["novelty"] = data.get("novelty", "")
    data["practical_implications"] = data.get("practical_implications", "")
    data["key_takeaways"] = data.get("key_takeaways", [])
    return data
@app.get("/health")
def health():
    return {"message": "AI Paper Summarizer Pro", "version": "3.1.0", "status": "running", "providers": len(PROVIDERS), "groq_keys": len(GROQ_KEYS), "grok_keys": len(GROK_KEYS), "gemini_keys": len(GEMINI_KEYS)}

@app.get("/debug")
def debug():
    return {
        "total_providers": len(PROVIDERS),
        "grok_keys": len(GROK_KEYS),
        "groq_keys": len(GROQ_KEYS),
        "provider_list": [f"{p['type']}_{i}" for i, p in enumerate(PROVIDERS)],
    }

@app.post("/summarize", response_model=SummaryResponse)
async def summarize(file: UploadFile = File(...), language: str = Form("english"), summary_type: str = Form("detailed")):
    start = datetime.utcnow()
    fname = file.filename.lower()
    ftype = "pdf" if fname.endswith(".pdf") else "txt" if fname.endswith(".txt") else None
    if not ftype: raise HTTPException(400, "Only PDF and TXT files supported")
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_MB: raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Max: {MAX_FILE_MB}MB")
    fid = str(uuid.uuid4())[:8]
    path = UPLOAD_DIR / f"{fid}_{file.filename}"
    with open(path, "wb") as f: f.write(content)
    try: text = extract_text(str(path), ftype)
    except Exception as e: raise HTTPException(400, f"Extraction failed: {e}")
    if len(text.strip()) < 50:
        raise HTTPException(400, f"Very little text extracted ({len(text.strip())} chars). The PDF may be scanned/image-based. Try a text-based PDF.")
    if not text.strip(): raise HTTPException(400, "No text could be extracted")
    try: result = generate_summary(text, language, summary_type)
    except HTTPException: raise
    except Exception as e:
        err = str(e)
        if err.startswith("ALL_FAILED"): raise HTTPException(429, f"All providers failed: {err}")
        if "QUOTA" in err: raise HTTPException(429, "AI API quota exceeded. Wait 1 min or change API key.")
        if "MODEL" in err: raise HTTPException(400, "Model error. Try again or use a different file.")
        raise HTTPException(500, f"AI error: {err}")
    elapsed = (datetime.utcnow() - start).total_seconds()
    def jl(v): return json.dumps(v) if isinstance(v, list) else v
    record = {"id":fid,"filename":file.filename,"filesize":len(content),"filetype":ftype.upper(),"source_url":"","title":result["title"],"summary":result["summary"],"source_text":text,"methodology":result.get("methodology",""),"key_findings":jl(result.get("key_findings",[])),"research_gaps":jl(result.get("research_gaps",[])),"future_directions":jl(result.get("future_directions",[])),"strengths":jl(result.get("strengths",[])),"weaknesses":jl(result.get("weaknesses",[])),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":jl(result.get("key_terms",[])),"key_points":jl(result.get("key_points",[])),"citations":jl(result.get("citations",[])),"research_objective":result.get("research_objective",""),"novelty":result.get("novelty",""),"practical_implications":result.get("practical_implications",""),"key_takeaways":jl(result.get("key_takeaways",[])),"language":language,"summary_type":summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":datetime.utcnow().isoformat()}
    cols = "id,filename,filesize,filetype,source_url,title,summary,source_text,methodology,key_findings,research_gaps,future_directions,strengths,weaknesses,conclusion,difficulty_level,key_terms,key_points,citations,research_objective,novelty,practical_implications,key_takeaways,language,summary_type,word_count,processing_time,created_at"
    ph = ":id,:filename,:filesize,:filetype,:source_url,:title,:summary,:source_text,:methodology,:key_findings,:research_gaps,:future_directions,:strengths,:weaknesses,:conclusion,:difficulty_level,:key_terms,:key_points,:citations,:research_objective,:novelty,:practical_implications,:key_takeaways,:language,:summary_type,:word_count,:processing_time,:created_at"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"INSERT INTO summaries ({cols}) VALUES ({ph})", record)
    return {"id":fid,"filename":file.filename,"filesize":len(content),"filetype":ftype.upper(),"source_url":"","title":result["title"],"summary":result["summary"],"methodology":result.get("methodology",""),"key_findings":result.get("key_findings",[]),"research_gaps":result.get("research_gaps",[]),"future_directions":result.get("future_directions",[]),"strengths":result.get("strengths",[]),"weaknesses":result.get("weaknesses",[]),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":result.get("key_terms",[]),"key_points":result.get("key_points",[]),"citations":result.get("citations",[]),"research_objective":result.get("research_objective",""),"novelty":result.get("novelty",""),"practical_implications":result.get("practical_implications",""),"key_takeaways":result.get("key_takeaways",[]),"language":language,"summary_type":summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":record["created_at"]}

class URLInput(BaseModel):
    url: str
    language: str = "english"
    summary_type: str = "detailed"

@app.post("/summarize-url", response_model=SummaryResponse)
async def summarize_url(body: URLInput):
    start = datetime.utcnow()
    if not body.url.strip():
        raise HTTPException(400, "URL is required")
    try:
        text = fetch_url_text(body.url)
    except Exception as e:
        raise HTTPException(400, f"Failed to fetch URL: {e}")
    if not text.strip():
        raise HTTPException(400, "No readable content found at this URL")
    try:
        result = generate_summary(text, body.language, body.summary_type)
    except HTTPException: raise
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "AI API quota exceeded")
        if "MODEL" in err: raise HTTPException(400, "Model error")
        raise HTTPException(500, f"AI error: {err}")
    elapsed = (datetime.utcnow() - start).total_seconds()
    fid = str(uuid.uuid4())[:8]
    fname = body.url.split("/")[-1][:50] or "webpage"
    def jl(v): return json.dumps(v) if isinstance(v, list) else v
    record = {"id":fid,"filename":fname,"filesize":len(text.encode("utf-8")),"filetype":"URL","source_url":body.url,"title":result["title"],"summary":result["summary"],"source_text":text,"methodology":result.get("methodology",""),"key_findings":jl(result.get("key_findings",[])),"research_gaps":jl(result.get("research_gaps",[])),"future_directions":jl(result.get("future_directions",[])),"strengths":jl(result.get("strengths",[])),"weaknesses":jl(result.get("weaknesses",[])),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":jl(result.get("key_terms",[])),"key_points":jl(result.get("key_points",[])),"citations":jl(result.get("citations",[])),"research_objective":result.get("research_objective",""),"novelty":result.get("novelty",""),"practical_implications":result.get("practical_implications",""),"key_takeaways":jl(result.get("key_takeaways",[])),"language":body.language,"summary_type":body.summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":datetime.utcnow().isoformat()}
    cols = "id,filename,filesize,filetype,source_url,title,summary,source_text,methodology,key_findings,research_gaps,future_directions,strengths,weaknesses,conclusion,difficulty_level,key_terms,key_points,citations,research_objective,novelty,practical_implications,key_takeaways,language,summary_type,word_count,processing_time,created_at"
    ph = ":id,:filename,:filesize,:filetype,:source_url,:title,:summary,:source_text,:methodology,:key_findings,:research_gaps,:future_directions,:strengths,:weaknesses,:conclusion,:difficulty_level,:key_terms,:key_points,:citations,:research_objective,:novelty,:practical_implications,:key_takeaways,:language,:summary_type,:word_count,:processing_time,:created_at"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"INSERT INTO summaries ({cols}) VALUES ({ph})", record)
    return {"id":fid,"filename":fname,"filesize":len(text.encode("utf-8")),"filetype":"URL","source_url":body.url,"title":result["title"],"summary":result["summary"],"methodology":result.get("methodology",""),"key_findings":result.get("key_findings",[]),"research_gaps":result.get("research_gaps",[]),"future_directions":result.get("future_directions",[]),"strengths":result.get("strengths",[]),"weaknesses":result.get("weaknesses",[]),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":result.get("key_terms",[]),"key_points":result.get("key_points",[]),"citations":result.get("citations",[]),"research_objective":result.get("research_objective",""),"novelty":result.get("novelty",""),"practical_implications":result.get("practical_implications",""),"key_takeaways":result.get("key_takeaways",[]),"language":body.language,"summary_type":body.summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":record["created_at"]}

@app.get("/history", response_model=List[HistoryItem])
def history():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT id,filename,title,filetype,language,filesize,created_at,source_url FROM summaries ORDER BY created_at DESC LIMIT 100").fetchall()
    return [{"id":r[0],"filename":r[1],"title":r[2],"filetype":r[3],"language":r[4],"filesize":r[5],"created_at":r[6],"source_url":r[7] or ""} for r in rows]

@app.get("/summary/{sid}")
def get(sid: str):
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("SELECT * FROM summaries WHERE id=?", (sid,)).fetchone()
    if not r: raise HTTPException(404, "Not found")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    return {"id":r[0],"filename":r[1],"filesize":r[2],"filetype":r[3],"source_url":r[4] or "","title":r[5],"summary":r[6],"source_text":r[7] or "","methodology":r[8] or "","key_findings":j(r[9]),"research_gaps":j(r[10]),"future_directions":j(r[11]),"strengths":j(r[12]),"weaknesses":j(r[13]),"conclusion":r[14] or "","difficulty_level":r[15] or "Intermediate","key_terms":j(r[16]),"key_points":j(r[17]),"citations":j(r[18]),"language":r[19],"summary_type":r[20],"word_count":r[21],"processing_time":r[22],"created_at":r[23],"research_objective":r[24] if len(r)>24 and r[24] else "","novelty":r[25] if len(r)>25 and r[25] else "","practical_implications":r[26] if len(r)>26 and r[26] else "","key_takeaways":j(r[27]) if len(r)>27 else []}

@app.delete("/summary/{sid}")
def delete(sid: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM summaries WHERE id=?", (sid,))
    return {"message": "Deleted"}

@app.get("/export/{sid}")
def export(sid: str, fmt: str = "txt"):
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("SELECT * FROM summaries WHERE id=?", (sid,)).fetchone()
    if not r: raise HTTPException(404, "Not found")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    title=r[5]; summary=r[6]; methodology=r[8] or ""
    key_findings=j(r[9]); research_gaps=j(r[10])
    future_directions=j(r[11]); strengths=j(r[12]); weaknesses=j(r[13])
    conclusion=r[14] or ""; difficulty_level=r[15] or "Intermediate"
    key_terms=j(r[16]); points=j(r[17]); citations=j(r[18])
    research_objective=r[24] if len(r)>24 and r[24] else ""
    novelty=r[25] if len(r)>25 and r[25] else ""
    practical_implications=r[26] if len(r)>26 and r[26] else ""
    key_takeaways=j(r[27]) if len(r)>27 else []
    if fmt == "json":
        return JSONResponse({"title":title,"summary":summary,"methodology":methodology,"key_findings":key_findings,"research_gaps":research_gaps,"future_directions":future_directions,"strengths":strengths,"weaknesses":weaknesses,"conclusion":conclusion,"difficulty_level":difficulty_level,"key_terms":key_terms,"key_points":key_takeaways or points,"citations":citations,"research_objective":research_objective,"novelty":novelty,"practical_implications":practical_implications,"key_takeaways":key_takeaways})
    text = f"{'='*60}\n{title}\n{'='*60}\n\nSUMMARY:\n{summary}\n"
    if research_objective: text += f"\nRESEARCH OBJECTIVE:\n{research_objective}\n"
    if methodology: text += f"\nMETHODOLOGY:\n{methodology}\n"
    if key_findings: text += "\nKEY FINDINGS:\n" + "\n".join(f"  * {f}" for f in key_findings)
    if key_takeaways: text += "\nKEY TAKEAWAYS:\n" + "\n".join(f"  * {p}" for p in key_takeaways)
    elif points: text += "\nKEY TAKEAWAYS:\n" + "\n".join(f"  * {p}" for p in points)
    if strengths: text += "\nSTRENGTHS:\n" + "\n".join(f"  * {s}" for s in strengths)
    if weaknesses: text += "\nWEAKNESSES:\n" + "\n".join(f"  * {w}" for w in weaknesses)
    if novelty: text += f"\nNOVELTY:\n{novelty}\n"
    if research_gaps: text += "\nRESEARCH GAPS:\n" + "\n".join(f"  * {g}" for g in research_gaps)
    if future_directions: text += "\nFUTURE DIRECTIONS:\n" + "\n".join(f"  * {f}" for f in future_directions)
    if practical_implications: text += f"\nPRACTICAL IMPLICATIONS:\n{practical_implications}\n"
    if conclusion: text += f"\nCONCLUSION:\n{conclusion}\n"
    if key_terms: text += "\nKEY TERMS:\n" + "\n".join(f"  * {t}" for t in key_terms)
    if citations: text += "\nCITATIONS:\n" + "\n".join(f"  [{i+1}] {c}" for i, c in enumerate(citations[:10]))
    out_path = OUTPUT_DIR / f"{sid}.txt"
    out_path.write_text(text, encoding="utf-8")
    return FileResponse(str(out_path), filename=f"{sid}.txt", media_type="text/plain")

# ─── Ask Paper Q&A ───
class AskInput(BaseModel):
    question: str

@app.post("/ask/{sid}")
def ask_paper(sid: str, body: AskInput):
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("""SELECT title, source_text, summary, methodology,
            key_findings, research_gaps, future_directions,
            strengths, weaknesses, conclusion, citations, key_terms
            FROM summaries WHERE id=?""", (sid,)).fetchone()
    if not r: raise HTTPException(404, "Paper not found")
    title, paper_text = r[0], r[1] or ""
    summary, methodology = r[2] or "", r[3] or ""
    if not paper_text.strip() and not summary.strip():
        raise HTTPException(400, "No content available for this paper")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    ctx = {
        "title": title,
        "summary": summary,
        "methodology": methodology,
        "key_findings": j(r[4]) if len(r) > 4 else [],
        "research_gaps": j(r[5]) if len(r) > 5 else [],
        "future_directions": j(r[6]) if len(r) > 6 else [],
        "strengths": j(r[7]) if len(r) > 7 else [],
        "weaknesses": j(r[8]) if len(r) > 8 else [],
        "conclusion": r[9] if len(r) > 9 and r[9] else "",
        "citations": j(r[10]) if len(r) > 10 else [],
        "key_terms": j(r[11]) if len(r) > 11 else [],
    }
    def fmt_list(items, label):
        if not items: return ""
        lines = "\n".join(f"  • {x}" for x in items[:12])
        return f"\n{label}:\n{lines}"
    kb = f"""## Paper: {title}

## Summary
{ctx['summary']}

## Methodology
{ctx['methodology']}
{fmt_list(ctx['key_findings'], '## Key Findings')}
{fmt_list(ctx['research_gaps'], '## Research Gaps')}
{fmt_list(ctx['future_directions'], '## Future Directions')}
{fmt_list(ctx['strengths'], '## Strengths')}
{fmt_list(ctx['weaknesses'], '## Weaknesses')}

## Conclusion
{ctx['conclusion']}
{fmt_list(ctx['key_terms'][:20], '## Key Terms')}"""
    if ctx["citations"]:
        cit_lines = "\n".join(f"  [{i+1}] {c[:200]}" for i, c in enumerate(ctx["citations"][:15]))
        kb += f"\n\n## References\n{cit_lines}"
    if paper_text.strip():
        words = paper_text.split()
        tail = " ".join(words[-2000:]) if len(words) > 2000 else paper_text
        kb += f"\n\n## Paper Excerpt\n{tail[:5000]}"
    prompt = f"""You are an MPhil/PhD research assistant answering questions about the paper below.

Use ONLY the provided paper content. Be thorough, precise, and cite which section your answer comes from. If the paper doesn't contain enough information, clearly state what is missing.

{body.question}

---

Paper Knowledge Base:
{kb}"""
    try:
        raw = ai_chat(prompt)
        return {"answer": raw, "question": body.question}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "AI API quota exceeded")
        raise HTTPException(500, f"AI error: {err}")

class CompareInput(BaseModel):
    sid1: str
    sid2: str

@app.post("/compare")
def compare_papers(body: CompareInput):
    with sqlite3.connect(DB_PATH) as conn:
        r1 = conn.execute("SELECT title,summary,methodology,key_findings,strengths,weaknesses,conclusion FROM summaries WHERE id=?", (body.sid1,)).fetchone()
        r2 = conn.execute("SELECT title,summary,methodology,key_findings,strengths,weaknesses,conclusion FROM summaries WHERE id=?", (body.sid2,)).fetchone()
    if not r1 or not r2: raise HTTPException(404, "One or both papers not found")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    p1 = {"title":r1[0],"summary":r1[1],"methodology":r1[2] or "","key_findings":j(r1[3]),"strengths":j(r1[4]),"weaknesses":j(r1[5]),"conclusion":r1[6] or ""}
    p2 = {"title":r2[0],"summary":r2[1],"methodology":r2[2] or "","key_findings":j(r2[3]),"strengths":j(r2[4]),"weaknesses":j(r2[5]),"conclusion":r2[6] or ""}
    prompt = f"""Compare these two research papers for an MPhil student:

PAPER 1: {json.dumps(p1, indent=2)}

PAPER 2: {json.dumps(p2, indent=2)}

Analyze:
1. How are their research objectives different?
2. Which has stronger methodology?
3. Which has more significant findings?
4. Strengths and weaknesses of each
5. Which paper is more valuable for research and why?

Be specific and objective."""
    try:
        raw = ai_chat(prompt)
        return {"comparison": raw, "paper1": p1, "paper2": p2}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "AI API quota exceeded")
        raise HTTPException(500, f"AI error: {err}")

# ─── ArXiv Search ───
class ArXivInput(BaseModel):
    query: str
    max_results: int = 5

@app.post("/arxiv-search")
def arxiv_search(body: ArXivInput):
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{body.query}&start=0&max_results={body.max_results}"
        r = http_requests.get(url, timeout=30)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ") if entry.find("atom:title", ns) is not None else ""
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ") if entry.find("atom:summary", ns) is not None else ""
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)] if entry.findall("atom:author", ns) else []
            link = entry.find("atom:id", ns).text.strip() if entry.find("atom:id", ns) is not None else ""
            published = entry.find("atom:published", ns).text[:10] if entry.find("atom:published", ns) is not None else ""
            papers.append({"title": title[:200], "summary": summary[:300], "authors": authors, "link": link, "published": published})
        return {"results": papers}
    except Exception as e:
        raise HTTPException(500, f"ArXiv search failed: {e}")

# ─── Thesis Proposal Generator ───
class ProposalInput(BaseModel):
    sid: str

@app.post("/generate-proposal")
def generate_proposal(body: ProposalInput):
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("SELECT title,summary,methodology,key_findings,research_gaps,future_directions FROM summaries WHERE id=?", (body.sid,)).fetchone()
    if not r: raise HTTPException(404, "Paper not found")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    paper = {"title":r[0],"summary":r[1],"methodology":r[2] or "","key_findings":j(r[3]),"research_gaps":j(r[4]),"future_directions":j(r[5])}
    prompt = f"""Based on this research paper, generate a thesis proposal draft for an MPhil student:

PAPER: {json.dumps(paper, indent=2)}

Create:
1. **Problem Statement** — What gap does this paper reveal?
2. **Research Questions** — 3-5 questions derived from the gaps
3. **Proposed Methodology** — What methods could address the questions?
4. **Expected Contributions** — What new knowledge would this add?
5. **Significance** — Why does this matter?

Make it specific to this paper's domain. Write in formal academic English."""
    try:
        raw = ai_chat(prompt)
        return {"proposal": raw, "paper_title": r[0]}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "AI API quota exceeded")
        raise HTTPException(500, f"AI error: {err}")

# ─── ArXiv Search ───
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
