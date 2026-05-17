"""
AI Research Paper Summarizer v3.1
Backend - FastAPI + Groq/Grok REST API (no library)
Supports: PDF, TXT | Large files | Citations | Export
"""

import os, re, uuid, json, sqlite3
from pathlib import Path
from datetime import datetime
from typing import List

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
init_db()

# ─── Multi-Provider AI Call (Groq + optional Grok) ───
PROVIDERS = []
for k in GROQ_KEYS:
    PROVIDERS.append({"type":"groq","key":k,"model":GROQ_MODEL})
for k in GROK_KEYS:
    PROVIDERS.append({"type":"grok","key":k,"model":GROK_MODEL})
if not PROVIDERS:
    raise RuntimeError("No API keys found. Set GROQ_API_KEY or GROK_API_KEY.")

# ─── AI Chat ───
def ai_chat(prompt: str, retry: int = 1) -> str:
    errors = {}
    for attempt in range(retry + 1):
        last_err = None
        for p in PROVIDERS:
            try:
                if p["type"] == "grok":
                    url = "https://api.x.ai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {p['key']}", "Content-Type": "application/json"}
                    payload = {"model": p["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
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
                    payload = {"model": p["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096}
                    resp = http_requests.post(url, json=payload, headers=headers, timeout=90)
                    if resp.status_code == 429:
                        last_err = f"groq_quota"; errors["groq"] = f"429"; continue
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
    # Fix missing spaces between camelCase words (PDF artifact)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(?<=[a-z])(?=\d)', ' ', text)
    text = re.sub(r'(?<=\d)(?=[A-Z])', ' ', text)
    text = re.sub(r'(?<=[a-z])([A-Z]{2,})', r' \1', text)
    # Fix ordinal suffixes merged: "21stCentury" → "21st Century"
    text = re.sub(r'(?<=\d)(st|nd|rd|th)(?=[A-Z])', r'\1 ', text)
    # Fix specific known PDF artifacts (exact strings only - no generic word splitting)
    text = re.sub(r'accessedon', 'accessed on', text)
    text = re.sub(r'Availableonline', 'Available online', text)
    text = re.sub(r'\be\s(\d+)', r'e\1', text)
    # Fix colon missing space: "Digital:Mobile" → "Digital: Mobile"
    text = re.sub(r'(?<=[a-zA-Z]):(?=[A-Z])', r': ', text)
    # Clean up double spaces
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
    return references[:20] if references else []

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
        cleaned = []
        for line in resp.strip().split("\n"):
            line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
            if line and len(line) > 30:
                cleaned.append(line)
        if len(cleaned) >= len(citations) // 2:
            return cleaned[:len(citations)]
    except:
        pass
    return citations

def extract_title(text: str) -> str:
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Skip lines with special symbols (authors)
        if any(c in line for c in ['∗', '†', '‡', '◇', '♡', '♥', '@']):
            continue
        # Skip email/URL lines
        if '.com' in line.lower() or '.edu' in line.lower():
            continue
        # Skip "Abstract" or metadata lines
        if line.lower().startswith('abstract'):
            continue
        if line.lower().startswith(('received:', 'accepted:', 'published:', 'copyright:', 'doi:', 'correspondence', 'submitted')):
            continue
        # Skip short lines
        if len(line) < 20:
            continue
        return line[:250]
    return "Untitled Document"

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

# ─── AI Summary ───
def generate_summary(text: str, lang: str = "english", stype: str = "detailed") -> dict:
    lang_inst = {"english":"Write in English.","urdu":"Write in Urdu (اردو). Use Nastaliq style.","both":"Write first in English, then full Urdu translation below."}.get(lang, "Write in English.")
    type_inst = {"brief":"Give a concise overview in 3-4 sentences covering the core contribution only.","detailed":"Extract in-depth research content. Cover objectives, methodology, findings with data/stats, gaps, conclusions, critical analysis, future work, and key terminology.","bullet":"Extract only the most important findings as short bullet points (max 10)."}.get(stype, "Extract in-depth research content.")

    # Truncate large PDFs to limit API calls - extract key sections
    if len(text) > 10000:
        intro = text[:3000]
        middle = text[3000:10000]
        text = intro + "\n\n" + middle

    chunks = chunk_text(text, CHUNK_SIZE)

    # Extract title from full text
    title = extract_title(text)

    # Process first chunk
    first_prompt = f"""You are an MPhil/PhD research assistant analyzing a research paper.

Paper Title: {title}
{type_inst}
{lang_inst}

Analyze the text below and provide a structured analysis with these sections:

## Summary
(A 3-5 sentence paragraph explaining the core content)

## Methodology
(Research design, methods, sample — or say "Not specified" if unclear)

## Key Findings
(- Key finding 1
- Key finding 2
- Key finding 3)

## Research Gaps
(- Gap 1
- Gap 2)

## Future Directions
(- Direction 1
- Direction 2)

## Strengths
(- Strength 1)

## Weaknesses
(- Weakness 1)

## Conclusion
(Lessons and implications)

## Difficulty
(Beginner, Intermediate, or Advanced)

## Key Points
(- Bullet 1
- Bullet 2)

TEXT:
{chunks[0]}"""

    all_data = {"summary":"","methodology":"","key_findings":[],"research_gaps":[],"future_directions":[],"strengths":[],"weaknesses":[],"conclusion":"","difficulty_level":"Intermediate","key_terms":[],"key_points":[],"citations":[]}

    for idx, chunk in enumerate(chunks):
        if idx == 0:
            prompt = first_prompt
        else:
            prompt = f"""Continue analyzing PART {idx+1}/{len(chunks)} of this research paper.

Provide structured analysis:

## Summary
## Methodology
## Key Findings
(- list items)
## Research Gaps
## Future Directions
## Strengths
## Weaknesses
## Conclusion
## Difficulty
(Beginner, Intermediate, or Advanced)
## Key Points

TEXT:
{chunk}"""

        try:
            raw = ai_chat(prompt)
            data = parse_json_from_text(raw)
            for k in all_data:
                if k == "summary":
                    all_data["summary"] += "\n" + data.get("summary", "")
                elif k == "methodology":
                    if data.get("methodology"): all_data["methodology"] = data["methodology"]
                elif k == "conclusion":
                    if data.get("conclusion"): all_data["conclusion"] = data["conclusion"]
                elif k == "difficulty_level":
                    if data.get("difficulty_level"): all_data["difficulty_level"] = data["difficulty_level"]
                elif isinstance(data.get(k), list):
                    all_data[k].extend(data.get(k, []))
        except Exception as e:
            if str(e).startswith("ALL_FAILED"): raise
            if str(e) == "QUOTA_EXCEEDED": raise
            if str(e) == "MODEL_ERROR": raise

    # Merge chunks for multi-chunk papers
    if len(chunks) > 1 and stype != "bullet":
        findings_str = "\n".join(f"- {f}" for f in all_data['key_findings'][:8]) if all_data['key_findings'] else "None"
        gaps_str = "\n".join(f"- {g}" for g in all_data['research_gaps'][:5]) if all_data['research_gaps'] else "None"
        future_str = "\n".join(f"- {f}" for f in all_data['future_directions'][:5]) if all_data['future_directions'] else "None"
        strengths_str = "\n".join(f"- {s}" for s in all_data['strengths'][:5]) if all_data['strengths'] else "None"
        weaknesses_str = "\n".join(f"- {w}" for w in all_data['weaknesses'][:5]) if all_data['weaknesses'] else "None"
        merge_prompt = f"""You are an MPhil/PhD research assistant. Merge these partial findings into ONE complete analysis for the paper "{title}". Remove redundancy. Keep the most valuable content.

Key Findings collected:
{findings_str}

Research Gaps collected:
{gaps_str}

Future Directions collected:
{future_str}

Strengths:
{strengths_str}

Weaknesses:
{weaknesses_str}

Methodology note: {all_data['methodology'][:500] if all_data['methodology'] else 'Not extracted'}

Provide the final merged analysis with these sections:

## Summary
## Methodology
## Key Findings
## Research Gaps
## Future Directions
## Strengths
## Weaknesses
## Conclusion
## Difficulty
(Beginner, Intermediate, or Advanced)
## Key Points"""
        try:
            raw = ai_chat(merge_prompt)
            merged = parse_json_from_text(raw)
            for k in all_data:
                if k == "citations": continue
                if isinstance(merged.get(k), str) and merged[k]:
                    all_data[k] = merged[k]
                elif isinstance(merged.get(k), list) and merged[k]:
                    all_data[k] = merged[k]
        except:
            pass

    # Final assembly
    all_data["title"] = title
    all_data["citations"] = clean_citations_with_ai(extract_citations(text))
    all_data["summary"] = all_data["summary"].strip() or title
    return all_data
@app.get("/health")
def health():
    return {"message": "AI Paper Summarizer Pro", "version": "3.1.0", "status": "running", "providers": len(PROVIDERS), "groq_keys": len(GROQ_KEYS), "grok_keys": len(GROK_KEYS)}

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
    record = {"id":fid,"filename":file.filename,"filesize":len(content),"filetype":ftype.upper(),"source_url":"","title":result["title"],"summary":result["summary"],"source_text":text,"methodology":result.get("methodology",""),"key_findings":jl(result.get("key_findings",[])),"research_gaps":jl(result.get("research_gaps",[])),"future_directions":jl(result.get("future_directions",[])),"strengths":jl(result.get("strengths",[])),"weaknesses":jl(result.get("weaknesses",[])),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":jl(result.get("key_terms",[])),"key_points":jl(result.get("key_points",[])),"citations":jl(result.get("citations",[])),"language":language,"summary_type":summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":datetime.utcnow().isoformat()}
    cols = "id,filename,filesize,filetype,source_url,title,summary,source_text,methodology,key_findings,research_gaps,future_directions,strengths,weaknesses,conclusion,difficulty_level,key_terms,key_points,citations,language,summary_type,word_count,processing_time,created_at"
    ph = ":id,:filename,:filesize,:filetype,:source_url,:title,:summary,:source_text,:methodology,:key_findings,:research_gaps,:future_directions,:strengths,:weaknesses,:conclusion,:difficulty_level,:key_terms,:key_points,:citations,:language,:summary_type,:word_count,:processing_time,:created_at"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"INSERT INTO summaries ({cols}) VALUES ({ph})", record)
    return {"id":fid,"filename":file.filename,"filesize":len(content),"filetype":ftype.upper(),"source_url":"","title":result["title"],"summary":result["summary"],"methodology":result.get("methodology",""),"key_findings":result.get("key_findings",[]),"research_gaps":result.get("research_gaps",[]),"future_directions":result.get("future_directions",[]),"strengths":result.get("strengths",[]),"weaknesses":result.get("weaknesses",[]),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":result.get("key_terms",[]),"key_points":result.get("key_points",[]),"citations":result.get("citations",[]),"language":language,"summary_type":summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":record["created_at"]}

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
    record = {"id":fid,"filename":fname,"filesize":len(text.encode("utf-8")),"filetype":"URL","source_url":body.url,"title":result["title"],"summary":result["summary"],"source_text":text,"methodology":result.get("methodology",""),"key_findings":jl(result.get("key_findings",[])),"research_gaps":jl(result.get("research_gaps",[])),"future_directions":jl(result.get("future_directions",[])),"strengths":jl(result.get("strengths",[])),"weaknesses":jl(result.get("weaknesses",[])),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":jl(result.get("key_terms",[])),"key_points":jl(result.get("key_points",[])),"citations":jl(result.get("citations",[])),"language":body.language,"summary_type":body.summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":datetime.utcnow().isoformat()}
    cols = "id,filename,filesize,filetype,source_url,title,summary,source_text,methodology,key_findings,research_gaps,future_directions,strengths,weaknesses,conclusion,difficulty_level,key_terms,key_points,citations,language,summary_type,word_count,processing_time,created_at"
    ph = ":id,:filename,:filesize,:filetype,:source_url,:title,:summary,:source_text,:methodology,:key_findings,:research_gaps,:future_directions,:strengths,:weaknesses,:conclusion,:difficulty_level,:key_terms,:key_points,:citations,:language,:summary_type,:word_count,:processing_time,:created_at"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"INSERT INTO summaries ({cols}) VALUES ({ph})", record)
    return {"id":fid,"filename":fname,"filesize":len(text.encode("utf-8")),"filetype":"URL","source_url":body.url,"title":result["title"],"summary":result["summary"],"methodology":result.get("methodology",""),"key_findings":result.get("key_findings",[]),"research_gaps":result.get("research_gaps",[]),"future_directions":result.get("future_directions",[]),"strengths":result.get("strengths",[]),"weaknesses":result.get("weaknesses",[]),"conclusion":result.get("conclusion",""),"difficulty_level":result.get("difficulty_level","Intermediate"),"key_terms":result.get("key_terms",[]),"key_points":result.get("key_points",[]),"citations":result.get("citations",[]),"language":body.language,"summary_type":body.summary_type,"word_count":len(result["summary"].split()),"processing_time":round(elapsed,2),"created_at":record["created_at"]}

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
    return {"id":r[0],"filename":r[1],"filesize":r[2],"filetype":r[3],"source_url":r[4] or "","title":r[5],"summary":r[6],"source_text":r[7] or "","methodology":r[8] or "","key_findings":j(r[9]),"research_gaps":j(r[10]),"future_directions":j(r[11]),"strengths":j(r[12]),"weaknesses":j(r[13]),"conclusion":r[14] or "","difficulty_level":r[15] or "Intermediate","key_terms":j(r[16]),"key_points":j(r[17]),"citations":j(r[18]),"language":r[19],"summary_type":r[20],"word_count":r[21],"processing_time":r[22],"created_at":r[23]}

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
    if fmt == "json":
        return JSONResponse({"title":title,"summary":summary,"methodology":methodology,"key_findings":key_findings,"research_gaps":research_gaps,"future_directions":future_directions,"strengths":strengths,"weaknesses":weaknesses,"conclusion":conclusion,"difficulty_level":difficulty_level,"key_terms":key_terms,"key_points":points,"citations":citations})
    text = f"{'='*60}\n{title}\n{'='*60}\n\nSUMMARY:\n{summary}\n"
    if methodology: text += f"\nMETHODOLOGY:\n{methodology}\n"
    if key_findings: text += "\nKEY FINDINGS:\n" + "\n".join(f"  * {f}" for f in key_findings)
    if strengths: text += "\nSTRENGTHS:\n" + "\n".join(f"  * {s}" for s in strengths)
    if weaknesses: text += "\nWEAKNESSES:\n" + "\n".join(f"  * {w}" for w in weaknesses)
    if research_gaps: text += "\nRESEARCH GAPS:\n" + "\n".join(f"  * {g}" for g in research_gaps)
    if future_directions: text += "\nFUTURE DIRECTIONS:\n" + "\n".join(f"  * {f}" for f in future_directions)
    if conclusion: text += f"\nCONCLUSION:\n{conclusion}\n"
    if key_terms: text += "\nKEY TERMS:\n" + "\n".join(f"  * {t}" for t in key_terms)
    if points: text += "\nKEY POINTS:\n" + "\n".join(f"  * {p}" for p in points)
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
        r = conn.execute("SELECT title, source_text, summary, key_findings, methodology FROM summaries WHERE id=?", (sid,)).fetchone()
    if not r: raise HTTPException(404, "Paper not found")
    title, paper_text = r[0], r[1] or ""
    summary, findings, methodology = r[2] or "", r[3] or "[]", r[4] or ""
    if not paper_text.strip():
        raise HTTPException(400, "No source text available for this paper")
    def j(v):
        try: return json.loads(v) if isinstance(v, str) else v
        except: return []
    findings_str = "\n".join(f"- {f}" for f in j(findings)[:5])
    context_words = paper_text.split()
    context = " ".join(context_words[-3000:]) if len(context_words) > 3000 else paper_text
    prompt = f"""You are analyzing the research paper "{title}" for an MPhil/PhD student.

Paper summary: {summary[:500]}
Key findings: {findings_str}
Methodology: {methodology[:300]}

Paper full text (last part):
{context}

Question: {body.question}

Answer based ONLY on the paper content above. Be specific, cite evidence, and give detailed academic analysis. If the paper doesn't contain the answer, say so."""
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
