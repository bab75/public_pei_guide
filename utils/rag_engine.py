"""
IEP Parent App — RAG Engine
Handles: PDF extraction, section detection, chunk indexing,
         auto question generation, semantic + keyword search.
No API key. No external AI. 100% local and free.
"""

import re
import math
import streamlit as st
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"

# ── Question templates mapped to common SOP heading patterns ─────────────────
QUESTION_TEMPLATES = [
    (r"referral",          "How does the referral process work?"),
    (r"child find",        "What is Child Find and who does it cover?"),
    (r"consent",           "When is parental consent required?"),
    (r"evaluat",           "What happens during the evaluation?"),
    (r"60.day|timeline|timeframe", "What is the 60-day timeline?"),
    (r"eligib",            "How is eligibility for special education determined?"),
    (r"classif",           "What disability classifications are used?"),
    (r"iep meeting|meeting", "What happens at an IEP meeting?"),
    (r"iep team|team comp", "Who is on the IEP team?"),
    (r"present level",     "What are Present Levels of Performance?"),
    (r"annual goal",       "What are annual goals and how are they written?"),
    (r"service",           "What special education services are available?"),
    (r"related service",   "What are related services?"),
    (r"placement",         "How is a placement decided?"),
    (r"least restrict|lre","What is Least Restrictive Environment (LRE)?"),
    (r"accommodat",        "What accommodations can be put in an IEP?"),
    (r"modif",             "What modifications can be made?"),
    (r"annual review",     "How often is the IEP reviewed?"),
    (r"reevaluat",         "When does my child get reevaluated?"),
    (r"amendment",         "How can an IEP be changed between annual reviews?"),
    (r"prior written|pwn", "What is Prior Written Notice?"),
    (r"procedural safeguard|parent right", "What are my rights as a parent?"),
    (r"independent.*eval|iee", "Can I get an Independent Educational Evaluation?"),
    (r"mediat",            "How does mediation work?"),
    (r"complaint|due process", "What can I do if I disagree with the IEP?"),
    (r"transition",        "What is transition planning?"),
    (r"extend.*school|esy","What is Extended School Year (ESY)?"),
    (r"behavior|bip|fba",  "What is a Behavioral Intervention Plan?"),
    (r"paraprofessional|para", "When does a student get a paraprofessional?"),
    (r"transport",         "What transportation services are available?"),
    (r"notif",             "When must the school notify me?"),
    (r"record",            "How do I get my child's school records?"),
    (r"surrogate",         "What is a surrogate parent?"),
    (r"transfer",          "What happens to the IEP when my child transfers schools?"),
    (r"home instruct",     "What is home instruction?"),
    (r"interim|pendency",  "What happens to services during a dispute?"),
    (r"discipline|suspend","What are the rules around discipline for students with IEPs?"),
    (r"manifestat",        "What is a Manifestation Determination Review?"),
    (r"social histor",     "What is a Social History Interview?"),
    (r"assistive tech",    "What assistive technology support is available?"),
    (r"12.month|summer",   "Can my child receive summer services?"),
    (r"preschool|early",   "Are there special education services for preschool children?"),
]

# ── Section category labels ───────────────────────────────────────────────────
SECTION_CATEGORIES = {
    "Getting Started":  [r"referral", r"child find", r"overview", r"introduction", r"purpose"],
    "Timelines":        [r"timeline", r"timeframe", r"60.day", r"deadline", r"calendar"],
    "Evaluation":       [r"evaluat", r"assess", r"test", r"social histor", r"psycho"],
    "Eligibility":      [r"eligib", r"classif", r"disability", r"determin"],
    "The IEP Document": [r"iep", r"present level", r"annual goal", r"service", r"accommodat", r"modif"],
    "Placement":        [r"placement", r"least restrict", r"lre", r"continuum", r"program"],
    "Parent Rights":    [r"parent right", r"procedural", r"consent", r"notice", r"pwn", r"record", r"iee"],
    "Meetings":         [r"meeting", r"team", r"committee", r"cse"],
    "Disagreements":    [r"mediat", r"complaint", r"due process", r"dispute", r"appeal", r"hearing"],
    "Special Topics":   [r"transition", r"esy", r"behavior", r"bip", r"fba", r"transport",
                         r"discipline", r"suspend", r"assistive", r"paraprofessional"],
}


# ── PDF extraction ────────────────────────────────────────────────────────────

def extract_pdf(file_obj) -> dict:
    """Extract {page_num: text} from uploaded file or path. Tries pdfplumber then PyMuPDF."""
    pages = {}
    data = None
    try:
        if hasattr(file_obj, "read"):
            data = file_obj.read()
        else:
            data = open(file_obj, "rb").read()
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return {}

    # Try pdfplumber first
    try:
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                pages[i] = text.strip()
        if any(pages.values()):
            return pages
    except Exception:
        pass

    # Fallback: PyMuPDF
    try:
        import fitz, io
        doc = fitz.open(stream=data, filetype="pdf")
        for i, page in enumerate(doc, 1):
            pages[i] = page.get_text().strip()
        return pages
    except Exception as e:
        st.error(f"PDF extraction failed. Install pdfplumber or PyMuPDF. Error: {e}")
        return {}


# ── Section detection ─────────────────────────────────────────────────────────

def detect_sections(pages: dict) -> list:
    """
    Scan pages for headings (ALL CAPS lines, short bold-like lines).
    Returns list of {page, heading, heading_lower} dicts sorted by page.
    """
    headings = []
    heading_pattern = re.compile(
        r'^([A-Z][A-Z\s\-\/\(\)]{4,80})$'   # ALL CAPS line ≥ 5 chars
        r'|^(\d+[\.\)]\s+[A-Z][A-Z\s]{3,60})$'  # Numbered heading
    )
    for page_num, text in pages.items():
        for line in text.split("\n"):
            line = line.strip()
            if len(line) < 5 or len(line) > 90:
                continue
            if heading_pattern.match(line):
                headings.append({
                    "page": page_num,
                    "heading": line,
                    "heading_lower": line.lower(),
                })
    return headings


def assign_category(heading_lower: str) -> str:
    """Map a heading to its display category."""
    for cat, patterns in SECTION_CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, heading_lower):
                return cat
    return "General Information"


# ── Chunking ──────────────────────────────────────────────────────────────────

def build_chunks(pages: dict, sections: list, chunk_size: int = 350, overlap: int = 80) -> list:
    """
    Split pages into overlapping word-chunks.
    Each chunk tagged with page number and nearest section heading.
    """
    # Build page → section lookup
    section_map = {}
    for s in sections:
        section_map[s["page"]] = s["heading"]

    chunks = []
    current_section = "General Information"

    for page_num in sorted(pages.keys()):
        if page_num in section_map:
            current_section = section_map[page_num]
        text = pages[page_num]
        words = text.split()
        if not words:
            continue
        step = chunk_size - overlap
        for start in range(0, max(1, len(words) - chunk_size + 1), max(1, step)):
            chunk_words = words[start: start + chunk_size]
            chunk_text  = " ".join(chunk_words)
            if len(chunk_text.strip()) < 40:
                continue
            chunks.append({
                "page":     page_num,
                "section":  current_section,
                "category": assign_category(current_section.lower()),
                "text":     chunk_text,
                "start":    start,
            })
    return chunks


# ── Question auto-generation ──────────────────────────────────────────────────

def generate_questions(sections: list, chunks: list) -> dict:
    """
    Build question bank from PDF section headings.
    Returns {category: [{"question": ..., "section": ..., "page": ...}]}
    """
    found_questions: dict = {}  # question_text → {section, page, category}

    # Match section headings against question templates
    for s in sections:
        hl = s["heading_lower"]
        for pattern, question in QUESTION_TEMPLATES:
            if re.search(pattern, hl):
                cat = assign_category(hl)
                if question not in found_questions:
                    found_questions[question] = {
                        "section":  s["heading"],
                        "page":     s["page"],
                        "category": cat,
                    }

    # Also scan chunk text for topics not caught by headings
    seen_cats = {v["category"] for v in found_questions.values()}
    for chunk in chunks:
        chunk_lower = chunk["text"].lower()
        for pattern, question in QUESTION_TEMPLATES:
            if re.search(pattern, chunk_lower) and question not in found_questions:
                cat = assign_category(chunk_lower[:100])
                found_questions[question] = {
                    "section":  chunk["section"],
                    "page":     chunk["page"],
                    "category": cat,
                }

    # Group by category
    by_category: dict = {}
    for q, meta in found_questions.items():
        cat = meta["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({
            "question": q,
            "section":  meta["section"],
            "page":     meta["page"],
        })

    # Sort categories by importance
    order = list(SECTION_CATEGORIES.keys()) + ["General Information"]
    return {k: by_category[k] for k in order if k in by_category}


# ── Search ────────────────────────────────────────────────────────────────────

IEP_DOMAIN_WEIGHTS = {
    "iep": 4, "evaluation": 3, "eligibility": 3, "placement": 3,
    "annual review": 4, "amendment": 2, "consent": 3, "disability": 2,
    "classification": 2, "services": 2, "least restrictive": 4, "lre": 4,
    "transition": 2, "prior written notice": 4, "pwn": 4, "parent": 2,
    "goals": 2, "present levels": 3, "fape": 4, "idea": 3,
    "referral": 3, "60 day": 4, "reevaluation": 3, "procedural": 3,
    "mediation": 3, "due process": 4, "discipline": 2, "bip": 3, "fba": 3,
}


def search_chunks(chunks: list, query: str, top_k: int = 5, section_filter: str = "") -> list:
    """
    Score chunks by keyword relevance + domain boosting.
    Optional section_filter restricts to chunks from that section.
    Returns top_k results sorted by score desc.
    """
    if not query.strip():
        return []

    query_lower  = query.lower()
    query_terms  = re.findall(r'\w+', query_lower)
    results      = []

    for chunk in chunks:
        if section_filter and section_filter.lower() not in chunk["section"].lower():
            continue

        text_lower = chunk["text"].lower()

        # Exact phrase match — strong bonus
        exact = 10 if query_lower in text_lower else 0

        # Term frequency
        tf = sum(text_lower.count(t) for t in query_terms if len(t) > 2)

        # Domain keyword boost
        domain = sum(w for kw, w in IEP_DOMAIN_WEIGHTS.items() if kw in text_lower)

        # Section-heading match bonus
        section_bonus = 3 if any(t in chunk["section"].lower() for t in query_terms) else 0

        score = tf + exact + domain + section_bonus
        if score > 0:
            results.append({**chunk, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def highlight(text: str, query: str, max_chars: int = 500) -> str:
    """Truncate and highlight matching terms in text."""
    # Find best window around first match
    query_lower = query.lower()
    text_lower  = text.lower()
    pos = text_lower.find(query_lower.split()[0]) if query_lower.split() else 0
    start = max(0, pos - 80)
    snippet = text[start: start + max_chars]
    if start > 0:
        snippet = "…" + snippet
    if start + max_chars < len(text):
        snippet = snippet + "…"

    # Highlight terms
    terms = sorted(re.findall(r'\w{3,}', query), key=len, reverse=True)
    for term in terms[:6]:
        snippet = re.sub(
            rf'\b({re.escape(term)})\b',
            r'<mark style="background:#FFF176;border-radius:2px;padding:0 1px;">\1</mark>',
            snippet, flags=re.IGNORECASE
        )
    return snippet


# ── Related questions ─────────────────────────────────────────────────────────

def get_related(question: str, all_questions: dict, current_category: str, n: int = 3) -> list:
    """Return n questions from the same category, excluding the current one."""
    pool = all_questions.get(current_category, [])
    return [q for q in pool if q["question"] != question][:n]


# ── Session state helpers ─────────────────────────────────────────────────────

def init_session():
    defaults = {
        "pdf_pages":    {},
        "pdf_chunks":   [],
        "pdf_sections": [],
        "pdf_questions":{},
        "pdf_name":     "",
        "pdf_loaded":   False,
        "active_q":     "",
        "active_cat":   "",
        "search_results": [],
        "history":      [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load_pdf_to_session(file_obj, name: str):
    """Extract, chunk, index and generate questions. Stores all in session_state."""
    with st.spinner("Reading your document… this takes about 10 seconds for an 80-page PDF."):
        pages = extract_pdf(file_obj)
    if not pages:
        return False

    with st.spinner("Detecting sections and building question bank…"):
        sections  = detect_sections(pages)
        chunks    = build_chunks(pages, sections)
        questions = generate_questions(sections, chunks)

    st.session_state.pdf_pages     = pages
    st.session_state.pdf_chunks    = chunks
    st.session_state.pdf_sections  = sections
    st.session_state.pdf_questions = questions
    st.session_state.pdf_name      = name
    st.session_state.pdf_loaded    = True
    st.session_state.history       = []
    return True


def auto_load_from_docs():
    """Try to load the first PDF found in the docs/ folder."""
    if st.session_state.get("pdf_loaded"):
        return True
    pdfs = list(DOCS_DIR.glob("*.pdf"))
    if not pdfs:
        return False
    return load_pdf_to_session(pdfs[0], pdfs[0].name)
