"""
AI Research Paper Summarizer Pro v3.0
Professional Streamlit Frontend with Dark/Light Mode
"""

import os, json, requests, streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8001")

st.set_page_config(
    page_title="AI Paper Summarizer Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Session State ───
defaults = {
    "current": None, "history": [], "dark_mode": False, "page": "summarize",
    "editing_title": "", "editing_summary": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Theme ───
def theme_css(dark: bool):
    base = """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        .card { animation: fadeIn 0.4s ease; border-radius: 16px; padding: 28px; margin: 16px 0; transition: all 0.3s ease; }
        .card:hover { transform: translateY(-2px); }
        .header { animation: fadeIn 0.5s ease; padding: 36px 40px; border-radius: 20px; margin-bottom: 28px; }
        .header h1 { margin:0; font-size:36px; font-weight: 800; letter-spacing: -0.5px; }
        .header p { font-size:15px; font-weight: 400; margin-top: 6px; opacity: 0.85; }
        .point { padding: 14px 18px; border-radius: 12px; margin: 8px 0; border-left: 4px solid; font-size: 14px; line-height: 1.6; transition: all 0.2s; }
        .point:hover { transform: translateX(4px); }
        .badge { padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 6px; display: inline-block; }
        .meta { font-size: 13px; opacity: 0.7; }
        .urdu { direction: rtl; text-align: right; font-size: 20px; line-height: 2; }
        .history-item { padding: 14px; border-radius: 12px; margin: 6px 0; transition: all 0.2s; }
        div[data-testid="stFileUploader"] { border-radius: 16px; padding: 28px; transition: all 0.3s; }
        .stButton > button { border-radius: 12px; padding: 12px 28px; font-weight: 600; font-size: 15px; border: none; transition: all 0.25s ease; }
        .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
        .stTextInput > div > input { border-radius: 12px; padding: 12px 16px; font-size: 14px; }
        .stSelectbox > div > div { border-radius: 12px; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; border-radius: 14px; padding: 4px; }
        .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 20px; font-weight: 500; }
        .sidebar-section { margin-bottom: 28px; }
        .sidebar-section h3 { font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 8px; }
        .section-heading { font-size: 18px; font-weight: 700; margin: 24px 0 12px; display: flex; align-items: center; gap: 8px; }
        .section-heading .icon { font-size: 20px; }
        .finding-item { padding: 14px 18px; border-radius: 12px; margin: 8px 0; display: flex; gap: 12px; font-size: 14px; line-height: 1.6; align-items: flex-start; }
        .finding-item .num { font-weight: 700; min-width: 24px; font-size: 13px; }
        .gap-item { padding: 12px 16px; border-radius: 10px; margin: 6px 0; font-size: 14px; line-height: 1.5; border-left: 3px solid; transition: all 0.2s; }
        .gap-item:hover { transform: translateX(3px); }
        .term-item { padding: 10px 16px; border-radius: 10px; margin: 5px 0; font-size: 13px; line-height: 1.5; }
        .term-item strong { font-weight: 600; }
        .research-section { padding: 24px; border-radius: 14px; margin: 12px 0; }
        .chat-msg { padding: 14px 18px; border-radius: 14px; margin: 8px 0; max-width: 85%; font-size: 14px; line-height: 1.6; }
        .diff-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    </style>"""
    if dark:
        return base + """
        <style>
            .main, .stApp { background: #0b0e14; color: #cdd6f4; }
            .card { background: rgba(30, 34, 48, 0.85); border: 1px solid rgba(137, 180, 250, 0.08); box-shadow: 0 4px 24px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.03); }
            .card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.35); border-color: rgba(137, 180, 250, 0.2); }
            .card h2, .card h3, .card p { color: #cdd6f4 !important; }
            .header { background: linear-gradient(135deg, #11141f, #1a1f35); border: 1px solid rgba(137, 180, 250, 0.12); }
            .header h1 { color: #89b4fa !important; }
            .header p { color: #9399b2 !important; }
            .point { background: rgba(30, 34, 48, 0.6); border-left-color: #89b4fa; color: #cdd6f4; }
            .badge { background: rgba(137, 180, 250, 0.12); color: #89b4fa; }
            .meta { color: #6c7086 !important; }
            .urdu { color: #cdd6f4; }
            .history-item { background: rgba(30, 34, 48, 0.6); border: 1px solid rgba(137, 180, 250, 0.06); }
            .history-item:hover { border-color: #89b4fa; background: rgba(137, 180, 250, 0.06); }
            div[data-testid="stFileUploader"] { border: 2px dashed rgba(137, 180, 250, 0.25); background: rgba(30, 34, 48, 0.5); }
            .stButton > button { background: linear-gradient(135deg, #89b4fa, #b4d0ff); color: #0b0e14 !important; }
            .stButton > button:hover { background: linear-gradient(135deg, #9dc2ff, #c8ddff); }
            .stTextInput > div > input { background: rgba(30, 34, 48, 0.8); border: 1px solid rgba(137, 180, 250, 0.12); color: #cdd6f4; }
            .stSelectbox > div > div { background: rgba(30, 34, 48, 0.8); border: 1px solid rgba(137, 180, 250, 0.12); color: #cdd6f4; }
            .stRadio > div { color: #cdd6f4; }
            .stTabs [data-baseweb="tab-list"] { background: rgba(30, 34, 48, 0.6); }
            .stTabs [data-baseweb="tab"] { color: #6c7086; }
            .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(137, 180, 250, 0.15); color: #89b4fa; }
            .sidebar-section h3 { color: #89b4fa !important; }
            .finding-item { background: rgba(30, 34, 48, 0.5); }
            .finding-item .num { color: #89b4fa; }
            .gap-item { background: rgba(30, 34, 48, 0.4); border-left-color: #f9e2af; }
            .gap-item:hover { background: rgba(249, 226, 175, 0.08); }
            .term-item { background: rgba(30, 34, 48, 0.4); }
            .term-item strong { color: #a6e3a1; }
            .research-section { background: rgba(30, 34, 48, 0.4); border: 1px solid rgba(137, 180, 250, 0.06); }
            .chat-msg { background: rgba(30, 34, 48, 0.6); }
            hr { border-color: rgba(137, 180, 250, 0.1); }
            code { background: rgba(137, 180, 250, 0.1); color: #89b4fa; padding: 2px 8px; border-radius: 6px; font-size: 13px; }
        </style>"""
    else:
        return base + """
        <style>
            .main, .stApp { background: #f0f2f5; color: #1e1e2e; }
            .card { background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(0,0,0,0.06); backdrop-filter: blur(8px); box-shadow: 0 2px 16px rgba(0,0,0,0.04); }
            .card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.08); border-color: rgba(37, 99, 235, 0.15); }
            .card h2, .card h3, .card p { color: #1e1e2e !important; }
            .header { background: linear-gradient(135deg, #2563eb, #6366f1, #7c3aed); }
            .header h1 { color: white !important; }
            .header p { color: rgba(255,255,255,0.85) !important; }
            .point { background: rgba(37, 99, 235, 0.06); border-left-color: #2563eb; }
            .badge { background: rgba(37, 99, 235, 0.08); color: #2563eb; }
            .meta { color: #64748b !important; }
            .history-item { background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.04); }
            .history-item:hover { border-color: #2563eb; background: rgba(37, 99, 235, 0.03); }
            div[data-testid="stFileUploader"] { border: 2px dashed rgba(37, 99, 235, 0.2); background: rgba(255,255,255,0.6); }
            .stButton > button { background: linear-gradient(135deg, #2563eb, #6366f1); color: white !important; }
            .stButton > button:hover { background: linear-gradient(135deg, #3b82f6, #818cf8); }
            .stTextInput > div > input { background: rgba(255,255,255,0.8); border: 1px solid rgba(0,0,0,0.08); color: #1e1e2e; }
            .stSelectbox > div > div { background: rgba(255,255,255,0.8); border: 1px solid rgba(0,0,0,0.08); color: #1e1e2e; }
            .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.6); }
            .stTabs [data-baseweb="tab"] { color: #64748b; }
            .stTabs [data-baseweb="tab"][aria-selected="true"] { background: rgba(37, 99, 235, 0.08); color: #2563eb; }
            .sidebar-section h3 { color: #2563eb !important; }
            .finding-item { background: rgba(37, 99, 235, 0.04); }
            .finding-item .num { color: #2563eb; }
            .gap-item { background: rgba(245, 158, 11, 0.06); border-left-color: #f59e0b; }
            .gap-item:hover { background: rgba(245, 158, 11, 0.1); }
            .term-item { background: rgba(16, 185, 129, 0.06); }
            .term-item strong { color: #059669; }
            .research-section { background: rgba(255,255,255,0.6); border: 1px solid rgba(0,0,0,0.04); }
            .chat-msg { background: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.06); }
            hr { border-color: rgba(0,0,0,0.06); }
            code { background: rgba(37, 99, 235, 0.06); color: #2563eb; padding: 2px 8px; border-radius: 6px; font-size: 13px; }
        </style>"""

# ─── API ───
def api_summarize(file, lang: str, stype: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/summarize", files={"file": (file.name, file, "application/pdf")}, data={"language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": _fmt_err(r)}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

def api_summarize_url(url: str, lang: str, stype: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/summarize-url", json={"url": url, "language": lang, "summary_type": stype}, timeout=180)
        return r.json() if r.status_code == 200 else {"error": _fmt_err(r)}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

def _fmt_err(r) -> str:
    try:
        detail = r.json().get("detail", "")
        if "BLOCKED_PUBLISHER" in detail:
            return detail.replace("BLOCKED_PUBLISHER: ", "🔒 ")
        if "403" in detail or "forbidden" in detail.lower():
            return "🔒 This publisher blocks automated access. Try ArXiv/PubMed URLs or upload PDF directly."
        if "429" in detail or "quota" in detail.lower() or "rate limit" in detail.lower():
            return "⏳ API limit reached. All providers are out of quota. Try again in 15-30 minutes."
        return detail or f"HTTP {r.status_code}"
    except:
        return f"HTTP {r.status_code}"

def api_history():
    st.session_state.history = _cached_history()

@st.cache_data(ttl=30, show_spinner=False)
def _cached_history():
    try:
        r = requests.get(f"{API_URL}/history", timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def api_delete(sid: str):
    try: requests.delete(f"{API_URL}/summary/{sid}", timeout=5); _cached_history.clear(); api_history()
    except: pass

def api_get(sid: str):
    try:
        r = requests.get(f"{API_URL}/summary/{sid}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def _src_link(s: dict) -> str:
    url = s.get("source_url", "")
    return f'<p class="meta">🔗 Source: <a href="{url}" target="_blank">{url[:80]}</a></p>'

def api_export(sid: str, fmt: str = "txt"):
    try:
        r = requests.get(f"{API_URL}/export/{sid}?fmt={fmt}", timeout=30)
        return r.text if r.status_code == 200 else None
    except: return None

def api_ask(sid: str, question: str) -> str:
    try:
        r = requests.post(f"{API_URL}/ask/{sid}", json={"question": question}, timeout=60)
        return r.json().get("answer", "Error: Could not get answer") if r.status_code == 200 else f"Error: {r.json().get('detail', r.status_code)}"
    except Exception as e:
        return f"Connection failed: {e}"

def api_compare(sid1: str, sid2: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/compare", json={"sid1": sid1, "sid2": sid2}, timeout=120)
        return r.json() if r.status_code == 200 else {"error": r.json().get("detail", f"HTTP {r.status_code}")}
    except Exception as e:
        return {"error": f"Connection failed: {e}"}

# ─── Render ───
dark = st.session_state.dark_mode
st.markdown(theme_css(dark), unsafe_allow_html=True)

# ─── Header ───
mode_icon = "🌙" if not dark else "☀️"
st.markdown(f"""
<div class="header" style="display:flex; justify-content:space-between; align-items:center;">
    <div>
        <h1>📄 AI Paper Summarizer</h1>
        <p>MPhil/PhD Research Assistant — Extract methodology, findings, gaps & more — English & Urdu</p>
    </div>
    <div style="text-align:right; display:flex; gap:10px; align-items:center;">
        <span style="font-size:12px; opacity:0.6; background:rgba(255,255,255,0.08); padding:4px 14px; border-radius:20px;">v3.0</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)

    # Theme toggle
    if st.button(f"{mode_icon} {'Light Mode' if dark else 'Dark Mode'}", use_container_width=True):
        st.session_state.dark_mode = not dark
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 🌐 Language / زبان")

    lang = st.radio("lang", ["english", "urdu", "both"],
        format_func=lambda x: {"english": "🇬🇧 English", "urdu": "🇵🇰 Urdu (اردو)", "both": "🌐 Both"}[x],
        label_visibility="collapsed", index=0)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 📋 Summary Type")
    stype = st.radio("type", ["detailed", "brief", "bullet"],
        format_func=lambda x: {"detailed": "🔍 In-Depth Research", "brief": "📝 Quick Overview", "bullet": "• Key Points Only"}[x],
        label_visibility="collapsed", index=0)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown("### 📂 History")
    if st.button("🔄 Refresh", use_container_width=True): api_history()

    for item in st.session_state.history[:15]:
        flag = {"english":"🇬🇧","urdu":"🇵🇰","both":"🌐"}.get(item["language"], "🌐")
        size = f"{item['filesize']/1024:.0f}KB" if item['filesize'] < 1024*1024 else f"{item['filesize']/(1024*1024):.1f}MB"
        label = item['title'][:25]
        if item.get('source_url'):
            label = "🔗 " + label
        cols = st.columns([3, 1, 1])
        with cols[0]:
            st.markdown(f"""<div class="history-item">
                <small>{flag} <strong>{label}</strong></small><br>
                <small class="meta">{item['filetype']} · {size} · {item['created_at'][:10]}</small>
            </div>""", unsafe_allow_html=True)
        with cols[1]:
            if st.button("📂", key=f"l_{item['id']}"):
                s = api_get(item['id'])
                if s: st.session_state.current = s; st.rerun()
                else: st.toast("Failed to load summary")
        with cols[2]:
            if st.button("🗑", key=f"d_{item['id']}"):
                api_delete(item['id']); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Main Tabs ───
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload & Summarize", "📖 View Summary", "📊 Compare Papers", "📚 ArXiv Search", "📝 Thesis Proposal"])

# ─── TAB 1 ───
with tab1:
    input_mode = st.radio("Input Mode", ["📄 File Upload", "🔗 URL"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📄 File Upload":
        st.markdown("### Upload Document")
        uploaded = st.file_uploader("Choose PDF or TXT file", type=["pdf", "txt"], label_visibility="collapsed")

        if uploaded:
            size = uploaded.size / 1024
            size_str = f"{size:.1f} KB" if size < 1024 else f"{size/1024:.1f} MB"
            ext = "PDF" if uploaded.name.endswith(".pdf") else "TXT"

            st.markdown(f"""
            <div class="card" style="padding:16px;">
                <strong>📎 {uploaded.name}</strong>
                <span class="badge">{ext}</span>
                <span class="badge">{size_str}</span>
            </div>""", unsafe_allow_html=True)

            if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is analyzing the paper..."):
                    result = api_summarize(uploaded, lang, stype)

                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.current = result
                    st.success("✅ Summary generated!")
                    api_history()
                    st.rerun()
    else:
        st.markdown("### Enter URL")
        url = st.text_input("Paste research paper / article URL", placeholder="https://arxiv.org/abs/...", label_visibility="collapsed")
        st.markdown('<p class="meta" style="margin:4px 0 8px;">💡 Supported: <strong>ArXiv</strong>, <strong>PubMed</strong>, PubMed Central. Most publisher sites (MDPI, Elsevier, Springer) block automated access — upload PDF instead.</p>', unsafe_allow_html=True)

        if url:
            st.markdown(f"""
            <div class="card" style="padding:16px;">
                <strong>🔗 {url[:80]}{'...' if len(url) > 80 else ''}</strong>
            </div>""", unsafe_allow_html=True)

            if st.button("🚀 Fetch & Summarize", type="primary", use_container_width=True):
                with st.spinner("🌐 Fetching URL..."):
                    result = api_summarize_url(url, lang, stype)

                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.session_state.current = result
                    st.success("✅ Summary generated!")
                    api_history()
                    st.rerun()

    st.markdown("""
    <div class="card" style="background:transparent; border-style:dashed;">
        <strong>💡 Supported:</strong> PDF, TXT (up to 50MB), URL &nbsp;|&nbsp;
        <strong>🌐 Languages:</strong> English, Urdu, Both
    </div>""", unsafe_allow_html=True)

# ─── TAB 2 ───
def show_paper(s, show_chat=True):
    lang_label = {"english":"🇬🇧 English","urdu":"🇵🇰 Urdu","both":"🌐 Both"}
    type_label = {"detailed":"In-Depth Research","brief":"Quick Overview","bullet":"Key Points Only"}
    size_str = f"{s['filesize']/1024:.0f}KB" if s['filesize']<1024*1024 else f"{s['filesize']/(1024*1024):.1f}MB"
    diff = s.get("difficulty_level", "Intermediate")
    diff_cls = {"Beginner":"diff-easy","Intermediate":"diff-medium","Advanced":"diff-hard"}.get(diff, "diff-medium")

    st.markdown(f"""
    <div class="card">
        <h2 style="margin:0 0 4px;">{s['title']}</h2>
        <p class="meta">
            <span class="badge">{lang_label.get(s['language'],s['language'])}</span>
            <span class="badge">{type_label.get(s['summary_type'],s['summary_type'])}</span>
            <span class="badge">{s['filetype']}</span>
            <span class="badge">{size_str}</span>
            <span class="badge">📝 {s['word_count']} words</span>
            <span class="badge">⚡ {s['processing_time']}s</span>
            <span class="diff-badge {diff_cls}">{diff}</span>
        </p>
        {_src_link(s) if s.get('source_url') else ''}
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'><span class='icon'>📝</span> Summary</div>", unsafe_allow_html=True)
    cls = "urdu" if s["language"] == "urdu" else ""
    st.markdown(f'<div class="card {cls}">{s["summary"]}</div>', unsafe_allow_html=True)

    if s.get("key_points"):
        st.markdown("<div class='section-heading'><span class='icon'>🎯</span> Key Takeaways</div>", unsafe_allow_html=True)
        for p in s["key_points"]:
            st.markdown(f'<div class="point">✦ {p}</div>', unsafe_allow_html=True)

    if s.get("methodology"):
        st.markdown("<div class='section-heading'><span class='icon'>🔬</span> Research Methodology</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="research-section">{s["methodology"]}</div>', unsafe_allow_html=True)

    if s.get("key_findings"):
        st.markdown("<div class='section-heading'><span class='icon'>📊</span> Key Findings & Results</div>", unsafe_allow_html=True)
        for i, f in enumerate(s["key_findings"], 1):
            st.markdown(f'<div class="finding-item"><span class="num">{i}.</span><span>{f}</span></div>', unsafe_allow_html=True)

    if s.get("strengths") or s.get("weaknesses"):
        st.markdown("<div class='section-heading'><span class='icon'>⚖️</span> Critical Analysis</div>", unsafe_allow_html=True)
        if s.get("strengths"):
            st.markdown("<p style='margin:4px 0;font-weight:600;color:#10b981;'>✅ Strengths</p>", unsafe_allow_html=True)
            for x in s["strengths"]:
                st.markdown(f'<div class="point" style="border-left-color:#10b981;">✦ {x}</div>', unsafe_allow_html=True)
        if s.get("weaknesses"):
            st.markdown("<p style='margin:12px 0 4px;font-weight:600;color:#ef4444;'>❌ Weaknesses / Limitations</p>", unsafe_allow_html=True)
            for x in s["weaknesses"]:
                st.markdown(f'<div class="point" style="border-left-color:#ef4444;">✦ {x}</div>', unsafe_allow_html=True)

    if s.get("research_gaps"):
        st.markdown("<div class='section-heading'><span class='icon'>🔍</span> Research Gaps</div>", unsafe_allow_html=True)
        for g in s["research_gaps"]:
            st.markdown(f'<div class="gap-item">⚠ {g}</div>', unsafe_allow_html=True)

    if s.get("future_directions"):
        st.markdown("<div class='section-heading'><span class='icon'>🔮</span> Future Directions</div>", unsafe_allow_html=True)
        for f in s["future_directions"]:
            st.markdown(f'<div class="gap-item" style="border-left-color:#89b4fa;">▸ {f}</div>', unsafe_allow_html=True)

    if s.get("conclusion"):
        st.markdown("<div class='section-heading'><span class='icon'>✅</span> Conclusion & Implications</div>", unsafe_allow_html=True)
        st.markdown(f'<div class="research-section">{s["conclusion"]}</div>', unsafe_allow_html=True)

    if s.get("key_terms"):
        st.markdown("<div class='section-heading'><span class='icon'>📖</span> Key Terminology</div>", unsafe_allow_html=True)
        for t in s["key_terms"]:
            st.markdown(f'<div class="term-item">▸ {t}</div>', unsafe_allow_html=True)

    cites = s.get("citations", [])
    if cites:
        st.markdown("<div class='section-heading'><span class='icon'>📚</span> References & Citations</div>", unsafe_allow_html=True)
        for i, c in enumerate(cites[:10]):
            st.markdown(f'<div class="card" style="padding:10px 16px;margin:4px 0;"><small>[{i+1}] {c}</small></div>', unsafe_allow_html=True)

    # Reading Time + Complexity
    wc = len((s.get("summary", "") or "").split())
    read_min = max(1, round(wc / 250))
    st.markdown(f'<p class="meta">⏱ Reading time: ~{read_min} min ({wc} words) &nbsp;|&nbsp; 📊 Complexity: {diff}</p>', unsafe_allow_html=True)

    st.markdown("<div class='section-heading'><span class='icon'>📥</span> Export</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    sid = s["id"]
    with col1:
        j = json.dumps(s, indent=2, ensure_ascii=False)
        st.download_button("📋 JSON", j, f"{sid}.json", use_container_width=True)
    with col2:
        t = f"# {s['title']}\n\n## Summary\n{s['summary']}\n\n"
        if s.get("methodology"): t += f"## Methodology\n{s['methodology']}\n\n"
        if s.get("key_findings"): t += "## Key Findings\n" + "\n".join(f"- {f}" for f in s["key_findings"]) + "\n\n"
        if s.get("strengths"): t += "## Strengths\n" + "\n".join(f"- {x}" for x in s["strengths"]) + "\n\n"
        if s.get("weaknesses"): t += "## Weaknesses\n" + "\n".join(f"- {x}" for x in s["weaknesses"]) + "\n\n"
        if s.get("research_gaps"): t += "## Research Gaps\n" + "\n".join(f"- {g}" for g in s["research_gaps"]) + "\n\n"
        if s.get("future_directions"): t += "## Future Directions\n" + "\n".join(f"- {f}" for f in s["future_directions"]) + "\n\n"
        if s.get("conclusion"): t += f"## Conclusion\n{s['conclusion']}\n\n"
        if s.get("key_terms"): t += "## Key Terms\n" + "\n".join(f"- {t}" for t in s["key_terms"]) + "\n\n"
        if s.get("key_points"): t += "## Key Takeaways\n" + "\n".join(f"- {p}" for p in s["key_points"]) + "\n\n"
        st.download_button("📄 TXT", t, f"{sid}.txt", use_container_width=True)
    with col3:
        m = f"# {s['title']}\n\n## Summary\n{s['summary']}\n\n"
        if s.get("methodology"): m += f"## Methodology\n{s['methodology']}\n\n"
        if s.get("key_findings"): m += "## Key Findings\n" + "\n".join(f"- {f}" for f in s["key_findings"]) + "\n\n"
        if s.get("strengths"): m += "## Strengths\n" + "\n".join(f"- {x}" for x in s["strengths"]) + "\n\n"
        if s.get("weaknesses"): m += "## Weaknesses\n" + "\n".join(f"- {x}" for x in s["weaknesses"]) + "\n\n"
        if s.get("research_gaps"): m += "## Research Gaps\n" + "\n".join(f"- {g}" for g in s["research_gaps"]) + "\n\n"
        if s.get("future_directions"): m += "## Future Directions\n" + "\n".join(f"- {f}" for f in s["future_directions"]) + "\n\n"
        if s.get("conclusion"): m += f"## Conclusion\n{s['conclusion']}\n\n"
        if s.get("key_terms"): m += "## Key Terms\n" + "\n".join(f"- {t}" for t in s["key_terms"]) + "\n\n"
        if s.get("key_points"): m += "## Key Takeaways\n" + "\n".join(f"- {p}" for p in s["key_points"]) + "\n\n"
        st.download_button("📝 Markdown", m, f"{sid}.md", use_container_width=True)
    with col4:
        resp = api_export(sid)
        if resp:
            st.download_button("📥 Export TXT", resp, f"{sid}.txt", use_container_width=True)
    # PDF export
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 10, s.get("title", "Untitled")[:100])
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, s.get("summary", "")[:2000])
        pdf_file = pdf.output(dest="S").encode("latin-1", errors="replace")
        st.download_button("📕 PDF", pdf_file, f"{sid}.pdf", use_container_width=True)
    except:
        pass

    # ─── Ask the Paper (Chat) ───
    if show_chat and s.get("id"):
        st.markdown("<div class='section-heading'><span class='icon'>💬</span> Ask the Paper</div>", unsafe_allow_html=True)
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        # Show chat history with avatars
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        # Chat input (resets automatically after submit)
        q = st.chat_input("Ask a question about this paper...", key=f"ask_{s['id']}")
        if q:
            st.session_state.chat_history.append({"role": "user", "content": q})
            with st.spinner(""):
                answer = api_ask(s["id"], q)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

with tab2:
    s = st.session_state.current
    if s and "error" not in s:
        show_paper(s)
    elif s and "error" in s:
        st.error(f"❌ {s['error']}")
    else:
        st.info("No summary yet. Upload a file in Tab 1.")

# ─── TAB 3 (Compare) ───
with tab3:
    st.markdown("<div class='section-heading'><span class='icon'>📊</span> Compare Two Papers</div>", unsafe_allow_html=True)
    hist = st.session_state.history[:20]
    if len(hist) < 2:
        st.info("At least 2 papers needed in history for comparison. Upload and summarize papers first.")
    else:
        opts = {f"{h['title'][:40]} ({h['created_at'][:10]})": h["id"] for h in hist}
        c1, c2 = st.columns(2)
        with c1:
            sel1 = st.selectbox("Select Paper 1", list(opts.keys()), index=0, key="cmp1")
        with c2:
            sel2 = st.selectbox("Select Paper 2", list(opts.keys()), index=min(1, len(opts)-1), key="cmp2")
        if st.button("🔍 Compare Papers", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing differences..."):
                result = api_compare(opts[sel1], opts[sel2])
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.markdown(f'<div class="card"><h3>📊 Comparison Result</h3><div style="line-height:1.8;">{result["comparison"]}</div></div>', unsafe_allow_html=True)
                with st.expander("📄 Paper 1 Details"):
                    show_paper(result["paper1"], show_chat=False)
                with st.expander("📄 Paper 2 Details"):
                    show_paper(result["paper2"], show_chat=False)

# ─── TAB 4: ArXiv Search ───
with tab4:
    st.markdown('<div class="section-heading"><span class="icon">📚</span> Search ArXiv Papers</div>', unsafe_allow_html=True)
    col_q, col_n = st.columns([3, 1])
    with col_q:
        arxiv_query = st.text_input("Search query", key="arxiv_q", placeholder="e.g., machine learning transformers", label_visibility="collapsed")
    with col_n:
        arxiv_max = st.number_input("Max results", 1, 20, 5, label_visibility="collapsed")
    if arxiv_query and st.button("🔍 Search ArXiv", use_container_width=True):
        with st.spinner(f"Searching ArXiv for '{arxiv_query}'..."):
            res = requests.post(f"{API_URL}/arxiv-search", json={"query": arxiv_query, "max_results": arxiv_max}).json()
        for p in res.get("results", []):
            with st.expander(f"**{p['title']}**"):
                st.markdown(f"**Authors:** {', '.join(p['authors'])}")
                st.markdown(f"**Published:** {p['published']}")
                st.markdown(f"**Abstract:** {p['summary']}")
                st.markdown(f"**Link:** [{p['link']}]({p['link']})")

# ─── TAB 5: Thesis Proposal ───
with tab5:
    st.markdown('<div class="section-heading"><span class="icon">📝</span> Thesis Proposal Generator</div>', unsafe_allow_html=True)
    st.markdown("Select a previously summarized paper to generate a thesis proposal from its research gaps.")
    if st.session_state.history:
        opts = {f"{h['title'][:60]}... ({h['date'][:10] if h.get('date') else ''})": h["id"] for h in st.session_state.history}
        sel_prop = st.selectbox("Choose a paper", list(opts.keys()), key="prop_sel")
        if st.button("🎯 Generate Proposal", use_container_width=True):
            with st.spinner("Generating thesis proposal..."):
                prop = requests.post(f"{API_URL}/generate-proposal", json={"sid": opts[sel_prop]}).json()
            if "error" in prop:
                st.error(f"❌ {prop['error']}")
            else:
                st.markdown(f"### Thesis Proposal: {prop['paper_title']}")
                st.markdown(f'<div class="card" style="line-height:1.8;">{prop["proposal"]}</div>', unsafe_allow_html=True)
    else:
        st.info("📄 Summarize a paper first!")

# Load history on start
if not st.session_state.history:
    st.session_state.history = _cached_history()




