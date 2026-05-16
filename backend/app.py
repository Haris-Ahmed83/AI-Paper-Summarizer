"""
AI Research Paper Summarizer v3.1
Backend - FastAPI + Gemini REST API (no library)
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
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY environment variable not set")

GEMINI_MODEL = "gemini-2.5-flash"
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

# ─── Gemini REST API Call ───
def gemini_chat(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = http_requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        err = resp.text[:300]
        if "quota" in err.lower() or "429" in err:
            raise Exception("QUOTA_EXCEEDED")
        if "not supported" in err.lower() or "image" in err.lower():
            raise Exception("MODEL_ERROR")
        raise Exception(f"API error ({resp.status_code}): {err}")
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise Exception("Empty Gemini response")
    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

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
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
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
    patterns = [r'\[\d+(?:,\s*\d+)*\]', r'\([\w\s,.\-]+,?\s*\d{4}\)', r'(?:https?://\S+)']
    cites = []
    for p in patterns: cites.extend(re.findall(p, text))
    return list(set(cites))[:20]

def extract_title(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for l in lines:
        if 10 < len(l) < 200: return l[:150]
    return "Untitled Document"

def fetch_url_text(url: str) -> str:
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
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return json.loads(raw)

# ─── AI Summary ───
def generate_summary(text: str, lang: str = "english", stype: str = "detailed") -> dict:
    lang_inst = {"english":"Write in English.","urdu":"Write in Urdu (اردو). Use Nastaliq style.","both":"Write first in English, then full Urdu translation below."}.get(lang, "Write in English.")
    type_inst = {"brief":"Give a concise overview in 3-4 sentences covering the core contribution only.","detailed":"Extract in-depth research content. Cover objectives, methodology, findings with data/stats, gaps, conclusions, critical analysis, future work, and key terminology.","bullet":"Extract only the most important findings as short bullet points (max 10)."}.get(stype, "Extract in-depth research content.")

    chunks = chunk_text(text, CHUNK_SIZE)

    all_summaries, all_methodology, all_findings = [], [], []
    all_gaps, all_conclusions, all_terms, all_points = [], [], [], []
    all_strengths, all_weaknesses, all_future = [], [], []

    for idx, chunk in enumerate(chunks):
        prompt = f"""You are analyzing PART {idx+1}/{len(chunks)} of a research paper/article for an MPhil/PhD student.

{type_inst}
{lang_inst}

Extract ALL of the following from this portion (be specific, not vague):

1. SUMMARY — Coherent paragraph
2. METHODOLOGY — Design, sample, instruments, analysis methods
3. KEY FINDINGS — Specific results, numbers, statistics, evidence
4. RESEARCH GAPS — Limitations, what's missing
5. FUTURE DIRECTIONS — Authors' suggested future work
6. STRENGTHS — What makes this paper strong/rigorous
7. WEAKNESSES — Methodological flaws, clarity issues, biases
8. CONCLUSION — Authors' final takeaway
9. KEY TERMS — Important concepts with definitions
10. DIFFICULTY LEVEL — Is this paper "Beginner", "Intermediate", or "Advanced"?
11. KEY POINTS — 2-3 short takeaway bullets
12. CITATIONS — Extract references in APA format: "Author, A. (Year). Title of article. Journal Name, Volume(Issue), Pages. https://doi.org/xxx"

PARTIAL TEXT:
{chunk}

Return ONLY valid JSON:
{{"summary":"...", "methodology":"...", "key_findings":["..."], "research_gaps":["..."], "future_directions":["..."], "strengths":["..."], "weaknesses":["..."], "conclusion":"...", "difficulty_level":"...", "key_terms":["...: ..."], "key_points":["..."], "citations":["..."]}}"""
        try:
            raw = gemini_chat(prompt)
            data = parse_json_from_text(raw)
            all_summaries.append(data.get("summary", ""))
            if data.get("methodology"): all_methodology.append(data["methodology"])
            all_findings.extend(data.get("key_findings", []))
            all_gaps.extend(data.get("research_gaps", []))
            all_future.extend(data.get("future_directions", []))
            all_strengths.extend(data.get("strengths", []))
            all_weaknesses.extend(data.get("weaknesses", []))
            if data.get("conclusion"): all_conclusions.append(data["conclusion"])
            all_terms.extend(data.get("key_terms", []))
            all_points.extend(data.get("key_points", []))
        except Exception as e:
            if str(e) == "QUOTA_EXCEEDED": raise
            if str(e) == "MODEL_ERROR": raise
            continue

    # Merge chunks
    if len(chunks) > 1 and stype != "bullet":
        parts = "\n".join(f"Part {i+1}: {s}" for i, s in enumerate(all_summaries) if s)
        merge_prompt = f"""Merge these partial summaries into ONE complete research analysis for an MPhil student. Remove redundancy. Keep the most valuable content.

{lang_inst}

Parts:
{parts}

Extracted elements to incorporate:
Methodology: {chr(10).join(f'- {m}' for m in all_methodology[-3:]) if all_methodology else 'N/A'}
Findings: {chr(10).join(f'- {f}' for f in all_findings[:8]) if all_findings else 'N/A'}
Gaps: {chr(10).join(f'- {g}' for g in all_gaps[:5]) if all_gaps else 'N/A'}
Future work: {chr(10).join(f'- {f}' for f in all_future[:5]) if all_future else 'N/A'}
Strengths: {chr(10).join(f'- {s}' for s in all_strengths[:5]) if all_strengths else 'N/A'}
Weaknesses: {chr(10).join(f'- {w}' for w in all_weaknesses[:5]) if all_weaknesses else 'N/A'}
Conclusions: {chr(10).join(f'- {c}' for c in all_conclusions[-2:]) if all_conclusions else 'N/A'}

Return ONLY valid JSON:
{{"title":"...", "summary":"...", "methodology":"...", "key_findings":["..."], "research_gaps":["..."], "future_directions":["..."], "strengths":["..."], "weaknesses":["..."], "conclusion":"...", "difficulty_level":"...", "key_terms":["...: ..."], "key_points":["..."], "citations":["..."]}}"""
        try:
            raw = gemini_chat(merge_prompt)
            merged = parse_json_from_text(raw)
            return {
                "title": merged.get("title", "Merged Document"),
                "summary": merged.get("summary", "\n\n".join(all_summaries)),
                "methodology": merged.get("methodology", "; ".join(all_methodology[-2:])),
                "key_findings": merged.get("key_findings", all_findings[:8]),
                "research_gaps": merged.get("research_gaps", all_gaps[:5]),
                "future_directions": merged.get("future_directions", all_future[:5]),
                "strengths": merged.get("strengths", all_strengths[:5]),
                "weaknesses": merged.get("weaknesses", all_weaknesses[:5]),
                "conclusion": merged.get("conclusion", "; ".join(all_conclusions[-2:])),
                "difficulty_level": merged.get("difficulty_level", "Intermediate"),
                "key_terms": merged.get("key_terms", all_terms[:8]),
                "key_points": merged.get("key_points", all_points[:8]),
                "citations": extract_citations(text),
            }
        except:
            pass

    return {
        "title": extract_title(text),
        "summary": "\n\n".join(all_summaries) if all_summaries else text[:500],
        "methodology": "; ".join(all_methodology[-2:]),
        "key_findings": all_findings[:8],
        "research_gaps": all_gaps[:5],
        "future_directions": all_future[:5],
        "strengths": all_strengths[:5],
        "weaknesses": all_weaknesses[:5],
        "conclusion": "; ".join(all_conclusions[-2:]),
        "difficulty_level": "Intermediate",
        "key_terms": all_terms[:8],
        "key_points": all_points[:8],
        "citations": extract_citations(text),
    }

# ─── API Routes ───
@app.get("/health")
def health():
    return {"message": "AI Paper Summarizer Pro", "version": "3.1.0", "status": "running"}

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
    if not text.strip(): raise HTTPException(400, "No text could be extracted")
    try: result = generate_summary(text, language, summary_type)
    except HTTPException: raise
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "Gemini API quota exceeded. Wait 1 min or change API key.")
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
        if "QUOTA" in err: raise HTTPException(429, "Gemini API quota exceeded")
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
        r = conn.execute("SELECT title, source_text FROM summaries WHERE id=?", (sid,)).fetchone()
    if not r: raise HTTPException(404, "Paper not found")
    title, paper_text = r[0], r[1] or ""
    if not paper_text.strip():
        raise HTTPException(400, "No source text available for this paper")
    # Take last ~4000 words for context
    words = paper_text.split()
    context = " ".join(words[-4000:]) if len(words) > 4000 else paper_text
    prompt = f"""You are analyzing the research paper "{title}".

Paper content:
{context}

Question: {body.question}

Answer based ONLY on the paper content above. Be specific and cite evidence. If the paper doesn't contain the answer, say so."""
    try:
        raw = gemini_chat(prompt)
        return {"answer": raw, "question": body.question}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "Gemini API quota exceeded")
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
        raw = gemini_chat(prompt)
        return {"comparison": raw, "paper1": p1, "paper2": p2}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "Gemini API quota exceeded")
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
        raw = gemini_chat(prompt)
        return {"proposal": raw, "paper_title": r[0]}
    except Exception as e:
        err = str(e)
        if "QUOTA" in err: raise HTTPException(429, "Gemini API quota exceeded")
        raise HTTPException(500, f"AI error: {err}")

# ─── ArXiv Search ───
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
