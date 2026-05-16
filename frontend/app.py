"""
ScholarAI — PhD Research Assistant (Streamlit)
"""

import os, json, requests, streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8001")

st.set_page_config(page_title="ScholarAI — PhD Research Assistant", page_icon="", layout="wide")

for k, v in {"current": None, "history": [], "dark_mode": False}.items():
    if k not in st.session_state: st.session_state[k] = v

CSS = r"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* { font-family: 'Inter', -apple-system, sans-serif !important; }

section[data-testid="stSidebar"] { background:#16181d !important; min-width:210px !important; border:none !important; }
section[data-testid="stSidebar"] > div { background:#16181d !important; }
section[data-testid="stSidebar"] > div > div { padding:0 !important; }
section[data-testid="stSidebar"] div[data-testid="stSidebarCollapsedControl"] { display:none !important; }
.st-emotion-cache-1t41k4p, .st-emotion-cache-1dp5vir { display:none !important; }
header[data-testid="stHeader"] { background:transparent !important; }
.stApp { background:#f8f9fb !important; }
.block-container { max-width:100% !important; padding:0 !important; }

.topbar { display:flex; align-items:center; justify-content:space-between; background:white; border-bottom:1px solid #e5e7eb; padding:10px 28px; }
.topbar h2 { font-size:18px; font-weight:600; color:#111827; margin:0; display:flex; align-items:center; gap:10px; }
.topbar .version { font-size:10px; font-weight:500; color:#6b7280; background:#f3f4f6; padding:2px 8px; border-radius:8px; border:1px solid #e5e7eb; }
.topbar-right { display:flex; align-items:center; gap:10px; }
.topbar .search-wrap { position:relative; }
.topbar .search-wrap input { width:210px; padding:6px 10px 6px 32px; font-size:13px; border:1px solid #e5e7eb; border-radius:8px; outline:none; background:white; color:#111827; }
.topbar .search-wrap input::placeholder { color:#9ca3af; }
.topbar .icon-btn { color:#6b7280; cursor:pointer; padding:6px; border:none; background:none; border-radius:6px; display:flex; align-items:center; justify-content:center; }
.topbar .icon-btn:hover { background:#f3f4f6; color:#111827; }

.hero { padding:24px 28px 0; }
.hero h1 { font-size:28px; font-weight:600; color:#111827; margin:0 0 4px; }
.hero p { font-size:14px; color:#6b7280; max-width:500px; line-height:1.5; margin:0; }

.upload-panel { margin:20px 28px; background:#f1f5f9; border:2px dashed #e5e7eb; border-radius:12px; padding:24px; display:flex; gap:24px; }
.upload-left { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 0; }
.upload-icon { width:56px; height:56px; border-radius:50%; background:#dbeafe; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
.upload-left h3 { font-size:16px; font-weight:600; color:#111827; margin:0 0 4px; }
.upload-left p { font-size:13px; color:#6b7280; margin:0 0 20px; }

.upload-panel-right { width:220px; min-width:220px; }
.upload-label { font-size:10px; font-weight:600; color:#6b7280; letter-spacing:0.12em; text-transform:uppercase; margin:0 0 8px; }

.section-header { display:flex; justify-content:space-between; align-items:center; padding:0 28px; margin-bottom:16px; }
.section-header h2 { font-size:18px; font-weight:600; color:#111827; margin:0; }
.section-header a { font-size:13px; color:#2563eb; cursor:pointer; font-weight:500; }

.card-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; padding:0 28px 28px; }
.paper-card { background:white; border-radius:12px; border:1px solid #e5e7eb; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.paper-card .thumb { height:120px; position:relative; }
.paper-card .badge-cat { position:absolute; top:10px; right:10px; font-size:10px; font-weight:600; padding:2px 10px; border-radius:10px; }
.paper-card .body { padding:14px; }
.paper-card .body h4 { font-size:13px; font-weight:600; color:#111827; margin:0 0 8px; line-height:1.4; overflow:hidden; text-overflow:ellipsis; }
.paper-card .body .date { font-size:12px; color:#6b7280; display:flex; align-items:center; gap:5px; }

.card { animation:fadeIn .4s ease; border-radius:12px; padding:24px; margin:12px 0; background:white; border:1px solid #e5e7eb; }
@keyframes fadeIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
.point { padding:12px 16px; border-radius:8px; margin:6px 0; border-left:3px solid #3b82f6; font-size:14px; line-height:1.6; background:#f8fafc; }
.badge { padding:3px 12px; border-radius:6px; font-size:12px; font-weight:500; margin-right:4px; display:inline-block; background:#eff6ff; color:#2563eb; }
.meta { font-size:13px; color:#94a3b8; }
.urdu { direction:rtl; text-align:right; font-size:20px; line-height:2; }
.section-heading { font-size:17px; font-weight:600; margin:20px 0 10px; color:#111827; }
.research-section { padding:16px; border-radius:8px; margin:8px 0; line-height:1.7; background:#f8fafc; }
.finding-item { display:flex; gap:10px; padding:8px 12px; margin:4px 0; border-radius:6px; font-size:14px; background:#f8fafc; }
.finding-item .num { font-weight:700; min-width:22px; color:#2563eb; }
.gap-item { padding:10px 14px; margin:4px 0; border-radius:6px; border-left:3px solid #f59e0b; font-size:14px; background:#f8fafc; }
.term-item { padding:6px 12px; margin:3px 0; font-size:14px; }
.diff-badge { padding:2px 10px; border-radius:5px; font-size:11px; font-weight:600; display:inline-block; }
.diff-easy { background:#10b98120; color:#10b981; }
.diff-medium { background:#f59e0b20; color:#f59e0b; }
.diff-hard { background:#ef444420; color:#ef4444; }
pre { border-radius:8px !important; font-size:13px !important; }
.stButton button { border-radius:8px; padding:8px 20px; font-weight:500; font-size:13px; }
.stTextInput input { border-radius:8px; padding:8px 14px; font-size:13px; }
.stSelectbox > div > div { border-radius:8px; font-size:13px; }
.stRadio > div { gap:4px; }
.stRadio > div label { border-radius:8px !important; padding:7px 14px !important; font-size:13px !important; font-weight:500 !important; border:1px solid #e5e7eb !important; background:white !important; }
.stRadio > div label[data-baseweb="radio"] { border-color:#e5e7eb; }
div[data-testid="stFileUploader"] { border:1.5px dashed #cbd5e1; border-radius:8px; background:white; padding:16px; }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-radius:10px; padding:3px; margin:0 28px; background:#e5e7eb; }
.stTabs [data-baseweb="tab"] { border-radius:7px; padding:5px 14px; font-weight:500; font-size:12px; color:#6b7280; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { background:white; color:#2563eb; box-shadow:none; }
.st-emotion-cache-1jicfl2, .st-emotion-cache-1mi2ry5 { display:none !important; }
.st-emotion-cache-1r4qj8v { display:none !important; }
.st-emotion-cache-1aezhbc { display:none !important; }
.st-emotion-cache-79elbk { display:none !important; }
div.row-widget.stRadio > div { flex-direction:row !important; }
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

# ─── API ───
def api_summarize(file, lang, stype):
    try:
        r = requests.post(f"{API_URL}/summarize", files={"file": (file.name, file, "application/pdf")}, data={"language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except Exception as e: return {"error": f"Connection failed: {str(e)}"}

def api_summarize_url(url, lang, stype):
    try:
        r = requests.post(f"{API_URL}/summarize-url", json={"url": url, "language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except Exception as e: return {"error": f"Connection failed: {str(e)}"}

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
    return f'<p class="meta">Source: <a href="{url}" target="_blank">{url[:80]}</a></p>'

def api_export(sid, fmt="txt"):
    try:
        r = requests.get(f"{API_URL}/export/{sid}?fmt={fmt}", timeout=30)
        return r.text if r.status_code == 200 else None
    except: return None

def api_ask(sid, question):
    try:
        r = requests.post(f"{API_URL}/ask/{sid}", json={"question": question}, timeout=60)
        return r.json().get("answer", "Error") if r.status_code == 200 else f"Error: {r.json().get('detail', r.status_code)}"
    except: return f"Connection failed"

def api_compare(sid1, sid2):
    try:
        r = requests.post(f"{API_URL}/compare", json={"sid1": sid1, "sid2": sid2}, timeout=120)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except: return {"error": "Connection failed"}

# ─── Sidebar ───
with st.sidebar:
    st.markdown('<div style="padding:22px 18px 12px;"><h1 style="color:white;font-size:18px;font-weight:700;margin:0;letter-spacing:-0.3px;">ScholarAI</h1><p style="color:#9ca3af;font-size:12px;margin:2px 0 0;">PhD Research Assistant</p></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 14px 16px;">
        <div style="width:100%;background:#2563eb;color:white;border:none;border-radius:8px;padding:9px 0;font-size:13px;font-weight:500;display:flex;align-items:center;justify-content:center;gap:7px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
            New Summary
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding:0 12px;">', unsafe_allow_html=True)
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;background:rgba(255,255,255,0.04);position:relative;"><span style="position:absolute;left:0;top:50%;transform:translateY(-50%);width:3px;height:18px;background:#2563eb;border-radius:2px;"></span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg><span style="color:white;font-size:13px;">Upload</span></div>""", unsafe_allow_html=True)
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;color:#6b7280;font-size:13px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>History</span></div>""", unsafe_allow_html=True)
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;color:#6b7280;font-size:13px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg><span>Settings</span></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:16px 18px;border-top:1px solid rgba(255,255,255,0.05);margin-top:auto;position:fixed;bottom:0;width:210px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;border-radius:6px;background:#2a2d35;display:flex;align-items:center;justify-content:center;font-size:11px;color:#9ca3af;font-weight:600;flex-shrink:0;">AT</div>
            <div><p style="color:white;font-size:13px;font-weight:500;margin:0;line-height:1.2;">Dr. Aris Thorne</p><p style="color:#6b7280;font-size:11px;margin:0;">Premium Plan</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Topbar ───
st.markdown('<div class="topbar"><h2>Research Intelligence Engine <span class="version">v2.4.0-Alpha</span></h2><div class="topbar-right"><div class="search-wrap"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9ca3af;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><input type="text" placeholder="Search research repository..." disabled></div><button class="icon-btn"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg></button><button class="icon-btn"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></button></div></div>', unsafe_allow_html=True)

# ─── Hero ───
st.markdown('<div class="hero"><h1>Synthesis Dashboard</h1><p>Distill complex academic literature into actionable insights with multi-lingual support and precision AI analysis.</p></div>', unsafe_allow_html=True)

# ─── Upload Panel ───
arxiv_url = st.session_state.pop("arxiv_url_to_summarize", None)

# Two-column upload panel using Streamlit columns styled as ScholarAI
col_left, col_right = st.columns([1, 0.3], gap="large")

with col_left:
    st.markdown('<div style="background:#f1f5f9;border:2px dashed #e5e7eb;border-radius:12px;padding:24px;text-align:center;">', unsafe_allow_html=True)
    st.markdown('<div style="width:56px;height:56px;border-radius:50%;background:#dbeafe;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:16px;font-weight:600;color:#111827;margin:0 0 4px;">Upload Academic Document</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:13px;color:#6b7280;margin:0 0 16px;">Drag and drop PDF, TXT or paste a research DOI/URL</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader("file", type=["pdf", "txt"], label_visibility="collapsed")
    st.markdown('<div style="margin:8px 0;font-size:12px;color:#9ca3af;">or</div>', unsafe_allow_html=True)
    url = st.text_input("url_input", value=arxiv_url or "", placeholder="https://example.com/paper", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<p class="upload-label">Summary Depth</p>', unsafe_allow_html=True)
    stype = st.radio("depth", ["bullet", "detailed", "brief"],
        format_func=lambda x: {"bullet":"Key Points", "detailed":"Full Detail", "brief":"Quick Overview"}[x],
        label_visibility="collapsed", horizontal=True, index=1)
    st.markdown('<p class="upload-label" style="margin-top:16px;">Language Output</p>', unsafe_allow_html=True)
    lang = st.radio("lang", ["english", "urdu", "both"],
        format_func=lambda x: {"english":"English", "urdu":"Urdu", "both":"Dual (Eng + Urdu)"}[x],
        label_visibility="collapsed", horizontal=False, index=0)

# ─── Generate Button + Actions ───
if uploaded:
    size = uploaded.size / 1024
    size_str = f"{size:.1f} KB" if size < 1024 else f"{size/1024:.1f} MB"
    ext = "PDF" if uploaded.name.endswith(".pdf") else "TXT"
    st.markdown(f'<div style="padding:0 28px;"><div class="card" style="display:flex;align-items:center;gap:12px;padding:14px 20px;"><strong>{uploaded.name}</strong><span class="badge">{ext}</span><span class="badge">{size_str}</span></div></div>', unsafe_allow_html=True)
    if st.button("Generate Summary", type="primary", use_container_width=False):
        with st.spinner("AI is analyzing the paper..."):
            result = api_summarize(uploaded, lang, stype)
        if "error" in result: st.error(f"{result['error']}")
        else:
            st.session_state.current = result; st.session_state.pop("chat_history", None)
            _cached_history.clear(); api_history(); st.rerun()
elif url:
    if arxiv_url and not st.session_state.get("arxiv_auto_summarized"):
        st.session_state.arxiv_auto_summarized = True
        with st.spinner("Fetching URL..."):
            result = api_summarize_url(arxiv_url, lang, stype)
        if "error" in result: st.error(f"{result['error']}")
        else:
            st.session_state.current = result; st.session_state.pop("chat_history", None)
            _cached_history.clear(); api_history(); st.rerun()
    else:
        st.markdown(f'<div style="padding:0 28px;"><div class="card" style="padding:14px 20px;"><strong>{url[:80]}</strong></div></div>', unsafe_allow_html=True)
        if st.button("Fetch & Summarize", type="primary"):
            with st.spinner("Fetching URL..."):
                result = api_summarize_url(url, lang, stype)
            if "error" in result: st.error(f"{result['error']}")
            else:
                st.session_state.current = result; st.session_state.pop("chat_history", None)
                _cached_history.clear(); api_history(); st.rerun()

# ─── Recent Syntheses ───
st.markdown('<div class="section-header"><h2>Recent Syntheses</h2><a>View All History</a></div>', unsafe_allow_html=True)

gradients = [
    ("background:linear-gradient(135deg,#60a5fa,#6366f1,#7c3aed)", "background:#dbeafe;color:#1d4ed8", "Quantum Physics"),
    ("background:linear-gradient(135deg,#34d399,#14b8a6,#0891b2)", "background:#ccfbf1;color:#0f766e", "Economics"),
    ("background:linear-gradient(135deg,#f472b6,#e11d48,#be123c)", "background:#fce7f3;color:#be185d", "Bio-Med"),
]

cards = '<div class="card-grid">'
for i, item in enumerate(st.session_state.history[:3]):
    g = gradients[i % 3]
    cards += f'<div class="paper-card"><div class="thumb" style="{g[0]}"><span class="badge-cat" style="{g[1]}">{g[2]}</span></div><div class="body"><h4>{item.get("title","Untitled")[:70]}</h4><p class="date"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>{item.get("created_at","")[:10]}</p></div></div>'
if not st.session_state.history:
    for i in range(3):
        g = gradients[i % 3]
        cards += f'<div class="paper-card"><div class="thumb" style="{g[0]}"><span class="badge-cat" style="{g[1]}">{g[2]}</span></div><div class="body"><h4>No summaries yet</h4><p class="date">—</p></div></div>'
cards += '</div>'
st.markdown(cards, unsafe_allow_html=True)

# ─── show_paper ───
def show_paper(s, show_chat=True):
    lang_label = {"english":"English","urdu":"Urdu","both":"Both"}
    type_label = {"detailed":"In-Depth Research","brief":"Quick Overview","bullet":"Key Points Only"}
    size_str = f"{s.get('filesize',0)/1024:.0f}KB" if s.get('filesize',0)<1024*1024 else f"{s.get('filesize',0)/(1024*1024):.1f}MB"
    diff = s.get("difficulty_level", "Intermediate")
    diff_cls = {"Beginner":"diff-easy","Intermediate":"diff-medium","Advanced":"diff-hard"}.get(diff, "diff-medium")
    st.markdown(f'<div class="card"><h2 style="margin:0 0 4px;">{s.get("title","Untitled")}</h2><p class="meta"><span class="badge">{lang_label.get(s.get("language",""),"")}</span><span class="badge">{type_label.get(s.get("summary_type",""),"")}</span><span class="badge">{s.get("filetype","N/A")}</span><span class="badge">{size_str}</span><span class="badge">{s.get("word_count",0)} words</span><span class="badge">{s.get("processing_time",0)}s</span><span class="diff-badge {diff_cls}">{diff}</span></p>{_src_link(s) if s.get("source_url") else ""}</div>', unsafe_allow_html=True)
    st.markdown("<div class='section-heading'>Summary</div>", unsafe_allow_html=True)
    cls = "urdu" if s.get("language") == "urdu" else ""
    st.markdown(f'<div class="card {cls}">{s.get("summary","")}</div>', unsafe_allow_html=True)
    if s.get("key_points"):
        st.markdown("<div class='section-heading'>Key Takeaways</div>", unsafe_allow_html=True)
        for p in s["key_points"]: st.markdown(f'<div class="point">{p}</div>', unsafe_allow_html=True)
    if s.get("methodology"):
        st.markdown("<div class='section-heading'>Research Methodology</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="research-section">{s["methodology"]}</div>', unsafe_allow_html=True)
    if s.get("key_findings"):
        st.markdown("<div class='section-heading'>Key Findings</div>", unsafe_allow_html=True)
        for i, f in enumerate(s["key_findings"], 1): st.markdown(f'<div class="finding-item"><span class="num">{i}.</span><span>{f}</span></div>', unsafe_allow_html=True)
    if s.get("strengths") or s.get("weaknesses"):
        st.markdown("<div class='section-heading'>Critical Analysis</div>", unsafe_allow_html=True)
        if s.get("strengths"):
            st.markdown("<p style='font-weight:600;color:#10b981;'>Strengths</p>", unsafe_allow_html=True)
            for x in s["strengths"]: st.markdown(f'<div class="point" style="border-left-color:#10b981;">{x}</div>', unsafe_allow_html=True)
        if s.get("weaknesses"):
            st.markdown("<p style='font-weight:600;color:#ef4444;'>Weaknesses / Limitations</p>", unsafe_allow_html=True)
            for x in s["weaknesses"]: st.markdown(f'<div class="point" style="border-left-color:#ef4444;">{x}</div>', unsafe_allow_html=True)
    if s.get("research_gaps"):
        st.markdown("<div class='section-heading'>Research Gaps</div>", unsafe_allow_html=True)
        for g in s["research_gaps"]: st.markdown(f'<div class="gap-item">{g}</div>', unsafe_allow_html=True)
    if s.get("future_directions"):
        st.markdown("<div class='section-heading'>Future Directions</div>", unsafe_allow_html=True)
        for f in s["future_directions"]: st.markdown(f'<div class="gap-item" style="border-left-color:#89b4fa;">{f}</div>', unsafe_allow_html=True)
    if s.get("conclusion"):
        st.markdown("<div class='section-heading'>Conclusion</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="research-section">{s["conclusion"]}</div>', unsafe_allow_html=True)
    if s.get("key_terms"):
        st.markdown("<div class='section-heading'>Key Terminology</div>", unsafe_allow_html=True)
        for t in s["key_terms"]: st.markdown(f'<div class="term-item">{t}</div>', unsafe_allow_html=True)
    cites = s.get("citations", [])
    if cites:
        st.markdown("<div class='section-heading'>References</div>", unsafe_allow_html=True)
        for i, c in enumerate(cites[:10]): st.markdown(f'<div style="padding:8px 14px;margin:3px 0;border-radius:6px;background:#f8fafc;font-size:13px;">[{i+1}] {c}</div>', unsafe_allow_html=True)
    wc = len((s.get("summary") or "").split())
    st.markdown(f'<p class="meta">Reading time: ~{max(1,round(wc/250))} min ({wc} words) | Complexity: {diff}</p>', unsafe_allow_html=True)
    st.markdown("<div class='section-heading'>Export</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    sid = s["id"]
    with c1: st.download_button("JSON", json.dumps(s, indent=2, ensure_ascii=False), f"{sid}.json", use_container_width=True)
    with c2: st.download_button("TXT", f"# {s.get('title','')}\n\n## Summary\n{s.get('summary','')}\n\n", f"{sid}.txt", use_container_width=True)
    with c3: st.download_button("Markdown", f"# {s.get('title','')}\n\n## Summary\n{s.get('summary','')}\n\n", f"{sid}.md", use_container_width=True)
    with c4:
        resp = api_export(sid)
        if resp: st.download_button("Export TXT", resp, f"{sid}.txt", use_container_width=True)
    if show_chat and s.get("id"):
        st.markdown("<div class='section-heading'>Ask the Paper</div>", unsafe_allow_html=True)
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        q = st.chat_input("Ask a question about this paper...", key=f"ask_{s['id']}")
        if q:
            st.session_state.chat_history.append({"role": "user", "content": q})
            with st.spinner(""): answer = api_ask(s["id"], q)
            st.session_state.chat_history.append({"role": "assistant", "content": answer}); st.rerun()

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload & Summarize", "View Summary", "Compare Papers", "ArXiv Search", "Thesis Proposal"])

with tab1:
    st.markdown('<div style="padding:8px 0;"><p style="font-size:13px;color:#6b7280;">Use the upload panel above to upload a PDF/TXT file or paste a URL. Your syntheses appear in Recent Syntheses.</p></div>', unsafe_allow_html=True)

with tab2:
    s = st.session_state.current
    if s and "error" not in s: show_paper(s)
    elif s and "error" in s: st.error(f"{s['error']}")
    else: st.info("No summary yet. Upload a file using the panel above.")

with tab3:
    st.markdown("<div class='section-heading'>Compare Two Papers</div>", unsafe_allow_html=True)
    hist = st.session_state.history[:20]
    if len(hist) < 2: st.info("At least 2 papers needed in history.")
    else:
        opts = {f"{h['title'][:40]} ({h['created_at'][:10]})": h["id"] for h in hist}
        c1, c2 = st.columns(2)
        with c1: sel1 = st.selectbox("Paper 1", list(opts.keys()), index=0, key="cmp1")
        with c2: sel2 = st.selectbox("Paper 2", list(opts.keys()), index=min(1,len(opts)-1), key="cmp2")
        if st.button("Compare Papers", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."): result = api_compare(opts[sel1], opts[sel2])
            if "error" in result: st.error(f"{result['error']}")
            else: st.markdown(f'<div class="card"><h3>Comparison Result</h3><div style="line-height:1.8;">{result["comparison"]}</div></div>', unsafe_allow_html=True)

with tab4:
    st.markdown("<div class='section-heading'>Search ArXiv Papers</div>", unsafe_allow_html=True)
    col_q, col_n = st.columns([3, 1])
    with col_q: arxiv_query = st.text_input("query", key="arxiv_q", placeholder="e.g., machine learning transformers", label_visibility="collapsed")
    with col_n: arxiv_max = st.number_input("max", 1, 20, 5, label_visibility="collapsed")
    if arxiv_query and st.button("Search ArXiv", use_container_width=True):
        with st.spinner(f"Searching..."): res = requests.post(f"{API_URL}/arxiv-search", json={"query": arxiv_query, "max_results": arxiv_max}).json()
        for p in res.get("results", []):
            with st.expander(f"**{p['title']}**"):
                st.markdown(f"**Authors:** {', '.join(p['authors'])}")
                st.markdown(f"**Published:** {p['published']}")
                st.markdown(f"**Abstract:** {p['summary']}")
                st.markdown(f"**Link:** [{p['link']}]({p['link']})")
                if st.button("Summarize this Paper", key=f"arxiv_{p['link']}", use_container_width=True):
                    st.session_state.current = None; st.session_state.pop("chat_history", None)
                    st.session_state["arxiv_url_to_summarize"] = p['link']; st.rerun()

with tab5:
    st.markdown("<div class='section-heading'>Thesis Proposal Generator</div>", unsafe_allow_html=True)
    if st.session_state.history:
        opts = {f"{h['title'][:60]} ({h['created_at'][:10] if h.get('created_at') else ''})": h["id"] for h in st.session_state.history}
        sel = st.selectbox("Choose a paper", list(opts.keys()), key="prop_sel")
        if st.button("Generate Proposal", use_container_width=True):
            with st.spinner("Generating..."): prop = requests.post(f"{API_URL}/generate-proposal", json={"sid": opts[sel]}).json()
            if "error" in prop: st.error(f"{prop['error']}")
            else: st.markdown(f"### Thesis Proposal: {prop['paper_title']}"); st.markdown(f'<div class="card" style="line-height:1.8;">{prop["proposal"]}</div>', unsafe_allow_html=True)
    else: st.info("Summarize a paper first!")

# Load history
if not st.session_state.history: api_history()

st.markdown('<div style="text-align:center;font-size:12px;opacity:0.4;padding:24px;">v3.0 ScholarAI · FastAPI · Gemini 2.5 · Streamlit · PyPDF2 · SQLite</div>', unsafe_allow_html=True)
