"""
ScholarAI — PhD Research Assistant
Professional Streamlit UI
"""

import os, json, requests, streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8001")

st.set_page_config(page_title="ScholarAI", page_icon="", layout="wide", initial_sidebar_state="expanded")

for k, v in {"current": None, "history": [], "theme": "dark"}.items():
    if k not in st.session_state: st.session_state[k] = v

THEME = st.session_state.theme
IS_DARK = THEME == "dark"

# ─── Professional Design System CSS ───
DARK_VARS = """
    --bg: #0a0b0e;
    --bg-card: #141518;
    --bg-sidebar: #0d0e11;
    --bg-elevated: #1a1b1e;
    --text: #e8e8ed;
    --text-secondary: #8e8e93;
    --text-muted: #636366;
    --border: rgba(255,255,255,0.06);
    --border-light: rgba(255,255,255,0.08);
    --accent: #5e5ce6;
    --accent-hover: #4b49d4;
    --accent-soft: rgba(94,92,230,0.12);
    --accent-glow: rgba(94,92,230,0.15);
    --success: #34c759;
    --warning: #ff9f0a;
    --danger: #ff453a;
    --radius: 10px;
    --radius-sm: 6px;
    --radius-lg: 14px;
    --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.4);
"""
LIGHT_VARS = """
    --bg: #f5f5f7;
    --bg-card: #ffffff;
    --bg-sidebar: #ffffff;
    --bg-elevated: #fafafa;
    --text: #1d1d1f;
    --text-secondary: #86868b;
    --text-muted: #aeaeb2;
    --border: rgba(0,0,0,0.06);
    --border-light: rgba(0,0,0,0.08);
    --accent: #5e5ce6;
    --accent-hover: #4b49d4;
    --accent-soft: rgba(94,92,230,0.08);
    --accent-glow: rgba(94,92,230,0.1);
    --success: #34c759;
    --warning: #ff9f0a;
    --danger: #ff453a;
    --radius: 10px;
    --radius-sm: 6px;
    --radius-lg: 14px;
    --shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.06);
"""

CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root { THEME_VARS }

* { font-family: 'Inter', -apple-system, sans-serif; box-sizing: border-box; }
body, .stApp { background: var(--bg); color: var(--text); }

#MainMenu, header[data-testid="stHeader"], div[data-testid="stToolbar"], .stAppDeployButton,
.st-emotion-cache-1aezhbc, .st-emotion-cache-1t41k4p { display: none !important; }
section[data-testid="stSidebar"] > div { padding: 0 !important; }
.st-emotion-cache-1dp5vir, .st-emotion-cache-1gv3huu { display: none !important; }

.block-container { max-width: 100% !important; padding: 0 !important; }
.main .block-container { padding: 0 !important; }

.app-layout { display: flex; min-height: 100vh; }
.sidebar { width: 240px; min-width: 240px; background: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 0; position: fixed; top: 0; left: 0; height: 100vh; z-index: 100; }
.main-area { flex: 1; margin-left: 240px; min-height: 100vh; }

.sb-brand { padding: 24px 20px 16px; }
.sb-brand h1 { font-size: 18px; font-weight: 700; color: var(--text); margin: 0; letter-spacing: -0.3px; }
.sb-brand p { font-size: 11px; color: var(--text-muted); margin: 2px 0 0; }
.sb-btn { margin: 4px 14px 16px; }
.sb-btn button { background: var(--accent) !important; color: white !important; border: none !important; border-radius: var(--radius) !important; padding: 10px 16px !important; font-size: 13px !important; font-weight: 500 !important; display: flex !important; align-items: center !important; justify-content: center !important; gap: 8px !important; width: 100% !important; box-shadow: 0 2px 12px rgba(94,92,230,0.3) !important; }
.sb-btn button:hover { background: var(--accent-hover) !important; }
.sb-nav { padding: 0 10px; flex: 1; }
.sb-nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 14px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; color: var(--text-muted); cursor: pointer; transition: all 0.15s; margin: 1px 0; position: relative; }
.sb-nav-item:hover { color: var(--text); background: var(--accent-soft); }
.sb-nav-item.active { color: var(--text); background: var(--accent-soft); }
.sb-nav-item.active::before { content: ''; position: absolute; left: -10px; top: 50%; transform: translateY(-50%); width: 3px; height: 20px; background: var(--accent); border-radius: 2px; }
.sb-nav-item svg { width: 18px; height: 18px; flex-shrink: 0; }
.sb-user { padding: 16px 20px; border-top: 1px solid var(--border); display: flex; align-items: center; gap: 10px; }
.sb-avatar { width: 32px; height: 32px; border-radius: 8px; background: var(--accent-soft); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; color: var(--accent); flex-shrink: 0; }
.sb-user-info p { margin: 0; line-height: 1.3; }
.sb-user-info .name { font-size: 13px; font-weight: 500; color: var(--text); }
.sb-user-info .plan { font-size: 11px; color: var(--text-muted); }

.topbar { display: flex; align-items: center; justify-content: space-between; padding: 14px 32px; background: var(--bg-card); border-bottom: 1px solid var(--border); }
.topbar h2 { font-size: 15px; font-weight: 600; color: var(--text); margin: 0; display: flex; align-items: center; gap: 10px; }
.topbar .badge { font-size: 10px; font-weight: 500; color: var(--text-muted); background: var(--bg-elevated); padding: 2px 10px; border-radius: 20px; border: 1px solid var(--border); }
.topbar-right { display: flex; align-items: center; gap: 8px; }
.tb-btn { width: 34px; height: 34px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: transparent; color: var(--text-secondary); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s; }
.tb-btn:hover { background: var(--accent-soft); color: var(--accent); border-color: var(--accent); }

.content { padding: 28px 32px; }
.hero { margin-bottom: 28px; }
.hero h1 { font-size: 26px; font-weight: 700; color: var(--text); margin: 0; letter-spacing: -0.5px; }
.hero p { font-size: 14px; color: var(--text-secondary); margin: 6px 0 0; max-width: 520px; line-height: 1.5; }

.upload-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 32px; display: flex; gap: 32px; margin-bottom: 32px; }
.upload-left { flex: 1; display: flex; flex-direction: column; align-items: center; text-align: center; padding: 12px 0; }
.upload-icon { width: 48px; height: 48px; border-radius: 50%; background: var(--accent-soft); display: flex; align-items: center; justify-content: center; margin-bottom: 12px; color: var(--accent); }
.upload-left h3 { font-size: 15px; font-weight: 600; color: var(--text); margin: 0 0 4px; }
.upload-left .sub { font-size: 13px; color: var(--text-secondary); margin: 0 0 20px; }
.upload-right { width: 200px; min-width: 200px; }
.upload-right .label { font-size: 10px; font-weight: 600; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; margin: 0 0 8px; }
.upload-right .group { margin-bottom: 20px; }
.pill-group { display: flex; gap: 6px; }
.pill { font-size: 12px; padding: 5px 14px; border-radius: 20px; border: 1px solid var(--border); color: var(--text-secondary); background: var(--bg); cursor: pointer; font-weight: 500; transition: all 0.15s; }
.pill.active { background: var(--accent); color: white; border-color: var(--accent); }
.lang-item { display: flex; align-items: center; gap: 8px; padding: 7px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); cursor: pointer; transition: all 0.15s; margin: 3px 0; background: var(--bg); }
.lang-item:hover { border-color: var(--accent); }
.lang-item.active { border-color: var(--accent); color: var(--text); background: var(--accent-soft); }
.lang-item .check { margin-left: auto; color: var(--accent); font-size: 12px; }

.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-head h2 { font-size: 16px; font-weight: 600; color: var(--text); margin: 0; }
.section-head a { font-size: 13px; color: var(--accent); cursor: pointer; font-weight: 500; }
.card-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.pcard { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); overflow: hidden; transition: all 0.2s; }
.pcard:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.pcard .thumb { height: 100px; position: relative; }
.pcard .cat { position: absolute; top: 10px; right: 10px; font-size: 10px; font-weight: 600; padding: 2px 10px; border-radius: 8px; }
.pcard .body { padding: 14px 16px; }
.pcard .body h4 { font-size: 13px; font-weight: 600; color: var(--text); margin: 0 0 8px; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pcard .body .meta { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; }

.card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; margin: 12px 0; }
.badge-tag { padding: 2px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; display: inline-block; margin-right: 4px; background: var(--accent-soft); color: var(--accent); }
.point { padding: 10px 14px; border-radius: var(--radius-sm); margin: 6px 0; border-left: 3px solid var(--accent); font-size: 14px; line-height: 1.6; background: var(--bg-elevated); }
.meta-text { font-size: 13px; color: var(--text-secondary); }
.diff-badge { padding: 2px 10px; border-radius: 5px; font-size: 11px; font-weight: 600; display: inline-block; }
.diff-easy { background: rgba(52,199,89,0.15); color: var(--success); }
.diff-medium { background: rgba(255,159,10,0.15); color: var(--warning); }
.diff-hard { background: rgba(255,69,58,0.15); color: var(--danger); }

.stButton button { border-radius: var(--radius-sm) !important; font-size: 13px !important; font-weight: 500 !important; padding: 8px 18px !important; border: none !important; background: var(--accent) !important; color: white !important; transition: all 0.15s !important; }
.stButton button:hover { background: var(--accent-hover) !important; }
.stButton button[kind="secondary"] { background: transparent !important; border: 1px solid var(--border) !important; color: var(--text) !important; }
.stTextInput input, .stSelectbox > div > div { border-radius: var(--radius-sm) !important; font-size: 13px !important; border: 1px solid var(--border) !important; background: var(--bg) !important; color: var(--text) !important; }
.stTextInput input:focus { border-color: var(--accent) !important; }
div[data-testid="stFileUploader"] { border: 1.5px dashed var(--border) !important; border-radius: var(--radius-sm) !important; background: var(--bg) !important; padding: 12px !important; }
.stRadio > div { gap: 4px !important; }
.stRadio > div label { border-radius: var(--radius-sm) !important; padding: 6px 14px !important; font-size: 13px !important; border: 1px solid var(--border) !important; background: var(--bg) !important; color: var(--text-secondary) !important; }
.stRadio > div label[aria-checked="true"] { background: var(--accent-soft) !important; color: var(--text) !important; border-color: var(--accent) !important; }
.stTabs [data-baseweb="tab-list"] { gap: 2px; border-radius: var(--radius); padding: 3px; background: var(--bg); border: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius: var(--radius-sm); padding: 5px 14px; font-weight: 500; font-size: 12px; color: var(--text-muted); }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background: var(--bg-card); color: var(--text); }
.stChatInput { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
.stChatInput input { background: var(--bg) !important; color: var(--text) !important; }
section[data-testid="stSidebar"] { display: none !important; }
.st-emotion-cache-1jicfl2 { display: none !important; }
</style>"""

CSS = CSS.replace("THEME_VARS", DARK_VARS if IS_DARK else LIGHT_VARS)

st.markdown(CSS, unsafe_allow_html=True)

# ─── API ───
def api_summarize(file, lang, stype):
    try:
        r = requests.post(f"{API_URL}/summarize", files={"file": (file.name, file, "application/pdf")}, data={"language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except: return {"error": f"Connection failed"}

def api_summarize_url(url, lang, stype):
    try:
        r = requests.post(f"{API_URL}/summarize-url", json={"url": url, "language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except: return {"error": "Connection failed"}

@st.cache_data(ttl=30, show_spinner=False)
def _cached_history():
    try:
        r = requests.get(f"{API_URL}/history", timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def api_history():
    d = _cached_history()
    if d is not None: st.session_state.history = d

def api_delete(sid):
    try: requests.delete(f"{API_URL}/summary/{sid}", timeout=5); _cached_history.clear(); api_history()
    except: pass

def api_get(sid):
    try:
        r = requests.get(f"{API_URL}/summary/{sid}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def _src_link(s):
    url = s.get("source_url", "")
    return f'<p class="meta-text">Source: <a href="{url}" target="_blank" style="color:var(--accent)">{url[:80]}</a></p>'

def api_export(sid, fmt="txt"):
    try:
        r = requests.get(f"{API_URL}/export/{sid}?fmt={fmt}", timeout=30)
        return r.text if r.status_code == 200 else None
    except: return None

def api_ask(sid, question):
    try:
        r = requests.post(f"{API_URL}/ask/{sid}", json={"question": question}, timeout=60)
        return r.json().get("answer", "Error") if r.status_code == 200 else f"Error"
    except: return "Connection failed"

def api_compare(sid1, sid2):
    try:
        r = requests.post(f"{API_URL}/compare", json={"sid1": sid1, "sid2": sid2}, timeout=120)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except: return {"error": "Connection failed"}

# ─── ScholarAI Custom Layout ───

# Sidebar (Streamlit native sidebar hidden, we render custom HTML)
st.markdown('<div class="app-layout"><div class="sidebar">', unsafe_allow_html=True)
st.markdown("""
<div class="sb-brand">
    <h1>ScholarAI</h1>
    <p>PhD Research Assistant</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="sb-btn">', unsafe_allow_html=True)
if st.button("+ New Summary", key="new_summary_btn", use_container_width=True):
    st.session_state.current = None
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="sb-nav">', unsafe_allow_html=True)
nav_items = [
    ("upload", "Upload", "M12 3v13M5 10l7-7 7 7M5 21h14"),
    ("history", "History", "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"),
    ("settings", "Settings", "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15c.3.2.5.6.4 1l-.6 1.7c-.2.5-.7.8-1.2.8h-2.7c-.2.5-.5 1-.8 1.4l1.4 1.4c.3.3.3.8 0 1.1l-1.4 1.4c-.3.3-.8.3-1.1 0l-1.4-1.4c-.4.3-.9.6-1.4.8v2.7c0 .5-.3 1-.8 1.2l-1.7.6c-.4.1-.8 0-1-.4L12 19.4c-.5.2-1 .2-1.5 0l-1.1 1.6c-.3.4-.7.5-1.1.4l-1.7-.6c-.5-.2-.8-.7-.8-1.2v-2.7c-.5-.2-1-.5-1.4-.8l-1.4 1.4c-.3.3-.8.3-1.1 0l-1.4-1.4c-.3-.3-.3-.8 0-1.1l1.4-1.4c-.3-.4-.6-.9-.8-1.4H4.8c-.5 0-1-.3-1.2-.8l-.6-1.7c-.1-.4 0-.8.4-1l1.6-1.1c-.2-.5-.2-1 0-1.5l-1.6-1.1c-.4-.2-.5-.6-.4-1l.6-1.7c.2-.5.7-.8 1.2-.8h2.7c.2-.5.5-1 .8-1.4L7.1 5.9c-.3-.3-.3-.8 0-1.1l1.4-1.4c.3-.3.8-.3 1.1 0l1.4 1.4c.4-.3.9-.6 1.4-.8V1.3c0-.5.3-1 .8-1.2l1.7-.6c.4-.1.8 0 1 .4l1.1 1.6c.5-.2 1-.2 1.5 0l1.1-1.6c.3-.4.7-.5 1.1-.4l1.7.6c.5.2.8.7.8 1.2v2.7c.5.2 1 .5 1.4.8l1.4-1.4c.3-.3.8-.3 1.1 0l1.4 1.4c.3.3.3.8 0 1.1l-1.4 1.4c.3.4.6.9.8 1.4h2.7c.5 0 1 .3 1.2.8l.6 1.7c.1.4 0 .8-.4 1l-1.6 1.1c.2.5.2 1 0 1.5l1.6 1.1z"),
]
for key, label, path in nav_items:
    active = "active" if key == "upload" else ""
    st.markdown(f'<div class="sb-nav-item {active}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="{path}"/></svg>{label}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="sb-user">
    <div class="sb-avatar">AT</div>
    <div class="sb-user-info">
        <p class="name">Dr. Aris Thorne</p>
        <p class="plan">Premium Plan</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div><div class="main-area">', unsafe_allow_html=True)

# ─── Top Bar ───
st.markdown(f"""
<div class="topbar">
    <h2>Synthesis Dashboard <span class="badge">v2.4</span></h2>
    <div class="topbar-right">
        <button class="tb-btn" onclick="alert('Theme toggle would go here')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
        </button>
        <button class="tb-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
        </button>
        <button class="tb-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </button>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="content">', unsafe_allow_html=True)

# ─── Hero ───
st.markdown("""
<div class="hero">
    <h1>Synthesis Dashboard</h1>
    <p>Distill complex academic literature into actionable insights with multi-lingual support and precision AI analysis.</p>
</div>
""", unsafe_allow_html=True)

# ─── Controls ───
lang = st.selectbox("_lang", ["english", "urdu", "both"],
    format_func=lambda x: {"english":"English","urdu":"Urdu","both":"Dual (Eng + Urdu)"}[x],
    label_visibility="collapsed")
stype = st.selectbox("_stype", ["detailed", "brief", "bullet"],
    format_func=lambda x: {"detailed":"Full Detail","brief":"Quick Overview","bullet":"Key Points Only"}[x],
    label_visibility="collapsed")

# ─── Upload Panel ───
arxiv_url = st.session_state.pop("arxiv_url_to_summarize", None)

st.markdown(f"""
<div class="upload-card">
    <div class="upload-left">
        <div class="upload-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
        <h3>Upload Academic Document</h3>
        <p class="sub">Drag and drop PDF, TXT or paste a research DOI/URL</p>
        <div style="{{display:flex;gap:8px;}}"></div>
    </div>
    <div class="upload-right">
        <div class="group">
            <p class="label">Summary Depth</p>
            <div class="pill-group">
                <span class="pill {'active' if stype=='bullet' else ''}">Key Points</span>
                <span class="pill {'active' if stype=='detailed' else ''}">Full Detail</span>
            </div>
        </div>
        <div class="group">
            <p class="label">Language Output</p>
            <div class="lang-item {'active' if lang=='english' else ''}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
                English <span class="check">{'✓' if lang=='english' else ''}</span>
            </div>
            <div class="lang-item {'active' if lang=='urdu' else ''}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
                Urdu <span class="check">{'✓' if lang=='urdu' else ''}</span>
            </div>
            <div class="lang-item {'active' if lang=='both' else ''}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
                Dual (Eng + Urdu) <span class="check">{'✓' if lang=='both' else ''}</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("file", type=["pdf", "txt"], label_visibility="collapsed")
url = st.text_input("url_input", value=arxiv_url or "", placeholder="Paste research URL (e.g. https://arxiv.org/abs/...)")

if uploaded:
    size = uploaded.size / 1024
    sz = f"{size:.0f}KB" if size < 1024 else f"{size/1024:.1f}MB"
    ext = "PDF" if uploaded.name.endswith(".pdf") else "TXT"
    st.markdown(f'<div class="card" style="padding:14px 20px;display:flex;align-items:center;gap:12px;"><strong>{uploaded.name}</strong><span class="badge-tag">{ext}</span><span class="badge-tag">{sz}</span></div>', unsafe_allow_html=True)
    if st.button("Generate Summary", type="primary"):
        with st.spinner("AI is analyzing the paper..."):
            result = api_summarize(uploaded, lang, stype)
        if "error" in result: st.error(result["error"])
        else: st.session_state.current = result; st.session_state.pop("chat_history", None); _cached_history.clear(); api_history(); st.rerun()
elif url:
    if arxiv_url and not st.session_state.get("arxiv_auto"):
        st.session_state.arxiv_auto = True
        with st.spinner("Fetching URL..."):
            result = api_summarize_url(arxiv_url, lang, stype)
        if "error" in result: st.error(result["error"])
        else: st.session_state.current = result; st.session_state.pop("chat_history", None); _cached_history.clear(); api_history(); st.rerun()
    else:
        st.markdown(f'<div class="card" style="padding:14px 20px;"><strong>{url[:80]}</strong></div>', unsafe_allow_html=True)
        if st.button("Fetch & Summarize", type="primary"):
            with st.spinner("Fetching URL..."):
                result = api_summarize_url(url, lang, stype)
            if "error" in result: st.error(result["error"])
            else: st.session_state.current = result; st.session_state.pop("chat_history", None); _cached_history.clear(); api_history(); st.rerun()

# ─── Recent Syntheses ───
st.markdown('<div class="section-head"><h2>Recent Syntheses</h2><a>View all</a></div>', unsafe_allow_html=True)

cats = [
    ("#5e5ce6", "rgba(94,92,230,0.3)", "ML/AI"),
    ("#34c759", "rgba(52,199,89,0.3)", "Quantum"),
    ("#ff9f0a", "rgba(255,159,10,0.3)", "Bio-Med"),
]

cards = '<div class="card-row">'
for i, item in enumerate(st.session_state.history[:3]):
    c = cats[i % 3]
    cards += f'<div class="pcard"><div class="thumb" style="background:linear-gradient(135deg,{c[0]},{c[1]});"><span class="cat" style="background:{c[0]}22;color:{c[0]}">{c[2]}</span></div><div class="body"><h4>{item.get("title","Untitled")[:80]}</h4><p class="meta">{item.get("created_at","")[:10] or "—"}</p></div></div>'
if not st.session_state.history:
    for i in range(3):
        c = cats[i % 3]
        cards += f'<div class="pcard"><div class="thumb" style="background:linear-gradient(135deg,{c[0]},{c[1]});"><span class="cat" style="background:{c[0]}22;color:{c[0]}">{c[2]}</span></div><div class="body"><h4>No summaries yet</h4><p class="meta">Upload a paper to begin</p></div></div>'
cards += '</div>'
st.markdown(cards, unsafe_allow_html=True)

# ─── show_paper ───
def show_paper(s, show_chat=True):
    ll = {"english":"English","urdu":"Urdu","both":"Both"}
    tl = {"detailed":"In-Depth","brief":"Quick","bullet":"Key Points"}
    sz = f"{s.get('filesize',0)/1024:.0f}KB" if s.get('filesize',0)<1024*1024 else f"{s.get('filesize',0)/(1024*1024):.1f}MB"
    diff = s.get("difficulty_level","Intermediate")
    dc = {"Beginner":"diff-easy","Intermediate":"diff-medium","Advanced":"diff-hard"}.get(diff,"diff-medium")
    st.markdown(f'<div class="card"><h2 style="margin:0 0 6px;font-size:20px;">{s.get("title","Untitled")}</h2><p><span class="badge-tag">{ll.get(s.get("language",""),"")}</span><span class="badge-tag">{tl.get(s.get("summary_type",""),"")}</span><span class="badge-tag">{s.get("filetype","N/A")}</span><span class="badge-tag">{sz}</span><span class="badge-tag">{s.get("word_count",0)} words</span><span class="diff-badge {dc}">{diff}</span></p>{_src_link(s) if s.get("source_url") else ""}</div>', unsafe_allow_html=True)
    st.markdown("<div class='section-head' style='margin-top:20px'><h2>Summary</h2></div>", unsafe_allow_html=True)
    cls = "urdu" if s.get("language") == "urdu" else ""
    st.markdown(f'<div class="card {cls}">{s.get("summary","")}</div>', unsafe_allow_html=True)
    if s.get("key_points"):
        st.markdown("<div class='section-head'><h2>Key Takeaways</h2></div>", unsafe_allow_html=True)
        for p in s["key_points"]: st.markdown(f'<div class="point">{p}</div>', unsafe_allow_html=True)
    if s.get("methodology"):
        st.markdown("<div class='section-head'><h2>Methodology</h2></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="card">{s["methodology"]}</div>', unsafe_allow_html=True)
    if s.get("key_findings"):
        st.markdown("<div class='section-head'><h2>Key Findings</h2></div>", unsafe_allow_html=True)
        for i, f in enumerate(s["key_findings"],1): st.markdown(f'<div class="point" style="border-left-color:var(--success);"><strong>{i}.</strong> {f}</div>', unsafe_allow_html=True)
    if s.get("strengths") or s.get("weaknesses"):
        st.markdown("<div class='section-head'><h2>Critical Analysis</h2></div>", unsafe_allow_html=True)
        if s.get("strengths"):
            st.markdown('<p style="font-weight:600;color:var(--success);font-size:14px;">Strengths</p>', unsafe_allow_html=True)
            for x in s["strengths"]: st.markdown(f'<div class="point" style="border-left-color:var(--success);">{x}</div>', unsafe_allow_html=True)
        if s.get("weaknesses"):
            st.markdown('<p style="font-weight:600;color:var(--danger);font-size:14px;margin-top:12px;">Limitations</p>', unsafe_allow_html=True)
            for x in s["weaknesses"]: st.markdown(f'<div class="point" style="border-left-color:var(--danger);">{x}</div>', unsafe_allow_html=True)
    if s.get("research_gaps"):
        st.markdown("<div class='section-head'><h2>Research Gaps</h2></div>", unsafe_allow_html=True)
        for g in s["research_gaps"]: st.markdown(f'<div class="point" style="border-left-color:var(--warning);">{g}</div>', unsafe_allow_html=True)
    if s.get("future_directions"):
        st.markdown("<div class='section-head'><h2>Future Directions</h2></div>", unsafe_allow_html=True)
        for f in s["future_directions"]: st.markdown(f'<div class="point" style="border-left-color:var(--accent);">{f}</div>', unsafe_allow_html=True)
    if s.get("conclusion"):
        st.markdown("<div class='section-head'><h2>Conclusion</h2></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="card">{s["conclusion"]}</div>', unsafe_allow_html=True)
    if s.get("key_terms"):
        st.markdown("<div class='section-head'><h2>Key Terminology</h2></div>", unsafe_allow_html=True)
        for t in s["key_terms"]: st.markdown(f'<div class="point" style="background:transparent;border-left-color:var(--text-muted);font-size:13px;">{t}</div>', unsafe_allow_html=True)
    cites = s.get("citations",[])
    if cites:
        st.markdown("<div class='section-head'><h2>References</h2></div>", unsafe_allow_html=True)
        for i,c in enumerate(cites[:10]): st.markdown(f'<div style="padding:8px 14px;margin:3px 0;border-radius:var(--radius-sm);background:var(--bg-elevated);font-size:13px;">[{i+1}] {c}</div>', unsafe_allow_html=True)
    wc = len((s.get("summary") or "").split())
    st.markdown(f'<p class="meta-text" style="margin:12px 0;">Reading time: ~{max(1,round(wc/250))} min ({wc} words) &middot; Complexity: {diff}</p>', unsafe_allow_html=True)
    st.markdown("<div class='section-head'><h2>Export</h2></div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    sid = s["id"]
    with c1: st.download_button("JSON", json.dumps(s,indent=2,ensure_ascii=False), f"{sid}.json", use_container_width=True)
    txt = f"# {s.get('title','')}\n\n## Summary\n{s.get('summary','')}\n\n"
    with c2: st.download_button("TXT", txt, f"{sid}.txt", use_container_width=True)
    with c3: st.download_button("Markdown", txt, f"{sid}.md", use_container_width=True)
    with c4:
        r = api_export(sid)
        if r: st.download_button("Export", r, f"{sid}.txt", use_container_width=True)
    if show_chat and s.get("id"):
        st.markdown("<div class='section-head'><h2>Ask the Paper</h2></div>", unsafe_allow_html=True)
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        q = st.chat_input("Ask a question about this paper...", key=f"ask_{s['id']}")
        if q:
            st.session_state.chat_history.append({"role":"user","content":q})
            with st.spinner(""): a = api_ask(s["id"],q)
            st.session_state.chat_history.append({"role":"assistant","content":a}); st.rerun()

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload & Summarize", "View Summary", "Compare Papers", "ArXiv Search", "Thesis Proposal"])

with tab1:
    st.markdown('<p style="color:var(--text-secondary);font-size:14px;">Use the upload panel above to add a PDF/TXT file or paste a research URL.</p>', unsafe_allow_html=True)

with tab2:
    s = st.session_state.current
    if s and "error" not in s: show_paper(s)
    elif s and "error" in s: st.error(s["error"])
    else: st.info("No summary yet — upload a paper to get started.")

with tab3:
    st.markdown("<div class='section-head'><h2>Compare Papers</h2></div>", unsafe_allow_html=True)
    hist = st.session_state.history[:20]
    if len(hist) < 2: st.info("At least 2 papers needed in history.")
    else:
        opts = {f"{h['title'][:40]} ({h['created_at'][:10]})":h["id"] for h in hist}
        c1,c2 = st.columns(2)
        with c1: sel1 = st.selectbox("Paper 1", list(opts.keys()), index=0, key="cp1")
        with c2: sel2 = st.selectbox("Paper 2", list(opts.keys()), index=min(1,len(opts)-1), key="cp2")
        if st.button("Compare", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."): r = api_compare(opts[sel1],opts[sel2])
            if "error" in r: st.error(r["error"])
            else: st.markdown(f'<div class="card">{r["comparison"]}</div>', unsafe_allow_html=True)

with tab4:
    st.markdown("<div class='section-head'><h2>ArXiv Search</h2></div>", unsafe_allow_html=True)
    qc, nc = st.columns([3,1])
    with qc: aq = st.text_input("q", key="aq", placeholder="Search query...", label_visibility="collapsed")
    with nc: am = st.number_input("n", 1, 20, 5, label_visibility="collapsed")
    if aq and st.button("Search", use_container_width=True):
        with st.spinner("Searching..."): res = requests.post(f"{API_URL}/arxiv-search", json={"query":aq,"max_results":am}).json()
        for p in res.get("results",[]):
            with st.expander(f"**{p['title']}**"):
                st.markdown(f"**Authors:** {', '.join(p['authors'])}")
                st.markdown(f"**Published:** {p['published']}")
                st.markdown(f"**Abstract:** {p['summary']}")
                st.markdown(f"[Open on ArXiv]({p['link']})")
                if st.button("Summarize", key=f"ax_{p['link']}"):
                    st.session_state.current = None; st.session_state["arxiv_url_to_summarize"] = p['link']; st.rerun()

with tab5:
    st.markdown("<div class='section-head'><h2>Thesis Proposal</h2></div>", unsafe_allow_html=True)
    if st.session_state.history:
        opts = {f"{h['title'][:60]} ({h['created_at'][:10]})":h["id"] for h in st.session_state.history}
        sel = st.selectbox("Select a paper", list(opts.keys()), key="tp")
        if st.button("Generate Proposal", type="primary", use_container_width=True):
            with st.spinner("Generating..."): prop = requests.post(f"{API_URL}/generate-proposal", json={"sid":opts[sel]}).json()
            if "error" in prop: st.error(prop["error"])
            else: st.markdown(f"### {prop['paper_title']}"); st.markdown(f'<div class="card">{prop["proposal"]}</div>', unsafe_allow_html=True)
    else: st.info("Summarize a paper first!")

if not st.session_state.history: api_history()

st.markdown('<div style="text-align:center;font-size:12px;color:var(--text-muted);padding:32px 0 16px;border-top:1px solid var(--border);margin-top:32px;">ScholarAI v3.0 &middot; FastAPI &middot; Gemini 2.5 &middot; Streamlit &middot; PyPDF2 &middot; SQLite</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)
