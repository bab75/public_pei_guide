"""
IEP Parent Guide — Home
Upload your SOP PDF here. Everything else flows from this page.
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="IEP Parent Guide",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.rag_engine import init_session, load_pdf_to_session, auto_load_from_docs
from utils.theme import apply_theme, sidebar_brand, page_header

apply_theme()
init_session()
sidebar_brand()
auto_load_from_docs()

# ── Hero ──────────────────────────────────────────────────────────────────────
page_header(
    "📚",
    "IEP Parent Guide",
    "Upload your IEP Standard Operating Procedures document — we'll turn it into plain-English answers, visual guides and checklists just for you",
    "#1E3A8A"
)

# ── Upload section ────────────────────────────────────────────────────────────
if not st.session_state.pdf_loaded:
    st.markdown("""
    <div style="background:white;border:2px dashed #93C5FD;border-radius:16px;
                padding:32px;text-align:center;margin-bottom:24px;">
        <div style="font-size:3rem;margin-bottom:12px;">📄</div>
        <div style="font-family:'Nunito',sans-serif;font-weight:800;font-size:1.2rem;
                    color:#1E3A8A;margin-bottom:8px;">
            Upload Your IEP SOP Document
        </div>
        <div style="color:#64748B;font-size:0.92rem;max-width:500px;margin:0 auto;">
            Upload your state or district's IEP Standard Operating Procedures PDF.
            The app reads it and builds everything from your document — not generic text.
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Choose your IEP SOP PDF",
        type=["pdf"],
        help="Your PDF stays private — it is read locally and never sent anywhere.",
        label_visibility="collapsed",
    )
    if uploaded:
        ok = load_pdf_to_session(uploaded, uploaded.name)
        if ok:
            st.success(f"✅ Document loaded! {len(st.session_state.pdf_pages)} pages · "
                       f"{sum(len(v) for v in st.session_state.pdf_questions.values())} questions generated")
            st.balloons()
            st.rerun()
        else:
            st.error("Could not read this PDF. Please check the file and try again.")

else:
    # ── Loaded state — show summary ───────────────────────────────────────────
    name  = st.session_state.pdf_name
    pages = len(st.session_state.pdf_pages)
    secs  = len(st.session_state.pdf_sections)
    qs    = sum(len(v) for v in st.session_state.pdf_questions.values())
    cats  = len(st.session_state.pdf_questions)

    st.markdown(f"""
    <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:14px;
                padding:18px 24px;margin-bottom:20px;">
        <div style="font-family:'Nunito',sans-serif;font-weight:800;
                    color:#15803D;font-size:1rem;margin-bottom:4px;">
            ✅ Document Ready
        </div>
        <div style="color:#166534;font-size:0.88rem;">
            {name} &nbsp;·&nbsp; {pages} pages &nbsp;·&nbsp;
            {secs} sections detected &nbsp;·&nbsp;
            {qs} questions generated across {cats} topic areas
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Option to replace
    with st.expander("Upload a different document"):
        new_file = st.file_uploader("Replace current document", type=["pdf"],
                                     label_visibility="collapsed")
        if new_file:
            load_pdf_to_session(new_file, new_file.name)
            st.rerun()

    # ── Metric row ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Pages Read", pages)
    with c2: st.metric("Sections Found", secs)
    with c3: st.metric("Questions Generated", qs)
    with c4: st.metric("Topic Areas", cats)

    st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)

    # ── What's available ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Nunito',sans-serif;font-weight:800;
                font-size:1.1rem;color:#1E293B;margin:20px 0 12px;">
        What you can explore
    </div>
    """, unsafe_allow_html=True)

    row1 = st.columns(3)
    row2 = st.columns(3)
    features = [
        ("❓", "Ask a Question",
         "Ask anything about the IEP process. The app finds the exact answer from your document with the page number.",
         "#2563EB", "Ask Questions"),
        ("🗺️", "Process Flowchart",
         "See the entire IEP journey as a visual step-by-step map. Click any step to read what your document says.",
         "#0D9488", "Flowchart"),
        ("📋", "Cheat Sheet",
         "Every section of your document explained in plain English. One card per topic. No jargon.",
         "#7C3AED", "Cheat Sheet"),
        ("⏱️", "My Timeline",
         "Enter the date you signed consent. See your 60-day deadline, where you are today, and what comes next.",
         "#D97706", "My Timeline"),
        ("🛡️", "My Rights",
         "Every parent right pulled from your document. What it means, what to say, what to do if refused.",
         "#DC2626", "My Rights"),
        ("📖", "Glossary",
         "Every term from your document explained in plain language. No more confusing abbreviations.",
         "#16A34A", "Glossary"),
    ]
    all_cols = list(row1) + list(row2)
    for col, (icon, title, desc, color, page_name) in zip(all_cols, features):
        with col:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;border:1px solid #E2E8F0;
                        border-top:4px solid {color};padding:20px 18px;
                        margin-bottom:12px;min-height:160px;">
                <div style="font-size:1.6rem;margin-bottom:8px;">{icon}</div>
                <div style="font-family:'Nunito',sans-serif;font-weight:800;
                            color:#1E293B;font-size:0.95rem;margin-bottom:6px;">
                    {title}</div>
                <div style="color:#64748B;font-size:0.82rem;line-height:1.6;">
                    {desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Where to start based on situation ────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Nunito',sans-serif;font-weight:800;
                font-size:1.1rem;color:#1E293B;margin:20px 0 12px;">
        Where should I start?
    </div>
    """, unsafe_allow_html=True)

    sit1, sit2, sit3 = st.columns(3)
    situations = [
        ("🆕", "Just getting started",
         "Go to → Process Flowchart to see the big picture, then → Ask Questions to understand what happens first.",
         "#EFF6FF", "#1E40AF"),
        ("📅", "Have a meeting coming up",
         "Go to → My Timeline to check your deadlines, then → My Rights to know what to ask for at the meeting.",
         "#FFF7ED", "#92400E"),
        ("❓", "Something feels wrong",
         "Go to → My Rights to understand what the school must do, then → Ask Questions about your specific concern.",
         "#FFF1F2", "#9F1239"),
    ]
    for col, (icon, title, desc, bg, fg) in zip([sit1, sit2, sit3], situations):
        with col:
            st.markdown(f"""
            <div style="background:{bg};border-radius:12px;padding:16px 18px;
                        border:1px solid {fg}33;">
                <div style="font-size:1.4rem;margin-bottom:6px;">{icon}</div>
                <div style="font-family:'Nunito',sans-serif;font-weight:800;
                            color:{fg};font-size:0.9rem;margin-bottom:6px;">
                    {title}</div>
                <div style="color:{fg}cc;font-size:0.82rem;line-height:1.6;">
                    {desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#94A3B8;font-size:0.75rem;
            margin-top:40px;padding-top:16px;border-top:1px solid #E2E8F0;">
    IEP Parent Guide · All answers come from your uploaded document ·
    Based on IDEA Federal Guidelines · Free to use
</div>
""", unsafe_allow_html=True)
