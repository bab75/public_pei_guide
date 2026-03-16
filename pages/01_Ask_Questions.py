"""
Page: Ask a Question
Auto-generated questions from PDF + free-text search.
All answers come directly from the uploaded document with page citations.
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="Ask a Question · IEP Guide", page_icon="❓", layout="wide")

from utils.rag_engine import init_session, auto_load_from_docs, search_chunks, get_related
from utils.theme import apply_theme, sidebar_brand, page_header, status_banner, answer_card

apply_theme()
init_session()
sidebar_brand()
auto_load_from_docs()

page_header("❓", "Ask a Question",
            "Click any question below — or type your own. Every answer comes from your document with the page number.",
            "#2563EB")
status_banner()

if not st.session_state.pdf_loaded:
    st.stop()

questions = st.session_state.pdf_questions
chunks    = st.session_state.pdf_chunks

# ── Layout: questions left, answers right ─────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown("""
    <div style="font-family:'Nunito',sans-serif;font-weight:800;
                color:#1E293B;font-size:1rem;margin-bottom:12px;">
        Questions from your document
    </div>
    """, unsafe_allow_html=True)

    # Category selector
    all_cats = list(questions.keys())
    if all_cats:
        selected_cat = st.selectbox(
            "Topic area",
            ["All Topics"] + all_cats,
            label_visibility="visible",
        )
    else:
        selected_cat = "All Topics"

    # Display questions grouped by category
    display_cats = all_cats if selected_cat == "All Topics" else [selected_cat]

    for cat in display_cats:
        cat_qs = questions.get(cat, [])
        if not cat_qs:
            continue

        color_map = {
            "Getting Started": "#2563EB",
            "Timelines":       "#D97706",
            "Evaluation":      "#7C3AED",
            "Eligibility":     "#0D9488",
            "The IEP Document":"#1D4ED8",
            "Placement":       "#16A34A",
            "Parent Rights":   "#DC2626",
            "Meetings":        "#0891B2",
            "Disagreements":   "#B45309",
            "Special Topics":  "#9333EA",
        }
        c = color_map.get(cat, "#475569")

        st.markdown(f"""
        <div style="font-size:0.75rem;font-weight:800;color:{c};
                    text-transform:uppercase;letter-spacing:0.06em;
                    margin:14px 0 6px;">{cat}</div>
        """, unsafe_allow_html=True)

        for q_item in cat_qs:
            q_text = q_item["question"]
            pg     = q_item["page"]
            if st.button(q_text, key=f"q_{q_text[:30]}", use_container_width=True):
                results = search_chunks(chunks, q_text, top_k=4)
                st.session_state.active_q   = q_text
                st.session_state.active_cat = cat
                st.session_state.search_results = results
                st.session_state.history.insert(0, {
                    "question": q_text,
                    "results":  results,
                    "category": cat,
                })
                st.rerun()

with right:
    # ── Free text search ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Nunito',sans-serif;font-weight:800;
                color:#1E293B;font-size:1rem;margin-bottom:8px;">
        Or type your own question
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        "Type a question",
        placeholder="e.g. What happens after I sign the consent form?",
        label_visibility="collapsed",
        key="free_query",
    )
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search_btn = st.button("Search Document", use_container_width=True, type="primary")
    with sc2:
        if st.button("Clear", use_container_width=True):
            st.session_state.search_results = []
            st.session_state.active_q       = ""
            st.session_state.history        = []
            st.rerun()

    if search_btn and query.strip():
        results = search_chunks(chunks, query, top_k=4)
        st.session_state.active_q          = query
        st.session_state.active_cat        = ""
        st.session_state.search_results    = results
        st.session_state.history.insert(0, {
            "question": query,
            "results":  results,
            "category": "",
        })

    # ── Show active answer ────────────────────────────────────────────────────
    if st.session_state.search_results:
        active_q = st.session_state.active_q

        st.markdown(f"""
        <div style="background:#EFF6FF;border-left:4px solid #2563EB;
                    border-radius:8px;padding:12px 16px;margin:16px 0 8px;">
            <div style="font-size:0.72rem;font-weight:700;color:#3B82F6;
                        text-transform:uppercase;letter-spacing:0.05em;
                        margin-bottom:4px;">Your Question</div>
            <div style="font-weight:700;color:#1E293B;font-size:1rem;">
                {active_q}</div>
        </div>
        """, unsafe_allow_html=True)

        results = st.session_state.search_results
        if not results:
            st.info("No matching passages found. Try rephrasing or use a different keyword from your document.")
        else:
            st.markdown(f"""
            <div style="color:#64748B;font-size:0.82rem;margin-bottom:12px;">
                Found {len(results)} relevant passage{"s" if len(results)>1 else ""} from your document
            </div>
            """, unsafe_allow_html=True)

            for i, r in enumerate(results, 1):
                answer_card(r, active_q, i)

        # ── Related questions ─────────────────────────────────────────────────
        cat  = st.session_state.active_cat
        related = get_related(active_q, questions, cat) if cat else []
        if related:
            st.markdown("""
            <div style="font-family:'Nunito',sans-serif;font-weight:800;
                        color:#1E293B;font-size:0.88rem;margin:16px 0 8px;">
                Related questions you might also want to know:
            </div>
            """, unsafe_allow_html=True)
            for rq in related:
                if st.button(f"→ {rq['question']}", key=f"rq_{rq['question'][:25]}",
                             use_container_width=False):
                    results = search_chunks(chunks, rq["question"], top_k=4)
                    st.session_state.active_q   = rq["question"]
                    st.session_state.active_cat = cat
                    st.session_state.search_results = results
                    st.session_state.history.insert(0, {
                        "question": rq["question"],
                        "results":  results,
                        "category": cat,
                    })
                    st.rerun()

    # ── History ───────────────────────────────────────────────────────────────
    if len(st.session_state.history) > 1:
        st.markdown("---")
        st.markdown("""
        <div style="font-family:'Nunito',sans-serif;font-weight:800;
                    color:#1E293B;font-size:0.88rem;margin-bottom:8px;">
            Previous questions this session
        </div>
        """, unsafe_allow_html=True)
        for entry in st.session_state.history[1:6]:
            pgs = list({r["page"] for r in entry["results"]}) if entry["results"] else []
            pg_str = f"Pages: {', '.join(str(p) for p in sorted(pgs))}" if pgs else "No results"
            if st.button(
                f"{entry['question']}  ·  {pg_str}",
                key=f"hist_{entry['question'][:20]}",
                use_container_width=True,
            ):
                st.session_state.active_q          = entry["question"]
                st.session_state.active_cat        = entry.get("category","")
                st.session_state.search_results    = entry["results"]
                st.rerun()
