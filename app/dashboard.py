import json
import sys
import html
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="EVIDENCE GRAPH",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
OFFICIAL_RESULTS_FILE = (
    PROJECT_ROOT / "official_data" / "official_three_way_results.json"
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from agent import run_agent
    BACKEND_AVAILABLE = True
    BACKEND_ERROR = None
except Exception as e:
    BACKEND_AVAILABLE = False
    BACKEND_ERROR = str(e)


BG = "#06111D"
PANEL = "#0B1B2A"
PANEL2 = "#0F2436"
BORDER = "#1C4058"
CYAN = "#38BDF8"
BLUE = "#0EA5E9"
TEAL = "#2DD4BF"
PURPLE = "#A78BFA"
GREEN = "#22C55E"
ORANGE = "#F59E0B"
RED = "#F87171"
TEXT = "#EAF6FC"
MUTED = "#91A9B9"
DIM = "#61798A"
NOT_AVAILABLE = "Not available"

EXAMPLE_QUESTIONS = [
    "Who won the men's 100m at the 2016 Olympics?",
    "Who won the men's 470 sailing event at the 2016 Summer Olympics?",
    "How many nations competed in Sailing at the 2016 Summer Olympics – Women's RS:X?",
    "According to the provided corpus, how many biathlon events at the 2018 Winter Olympics had more than 73 competitors?",
]


def load_official_results():
    if not OFFICIAL_RESULTS_FILE.exists():
        return None
    try:
        with open(OFFICIAL_RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def pipeline_stats(summary, key):
    data = (summary or {}).get(key) or {}
    correct = data.get("correct")
    total = data.get("total")
    accuracy = data.get("accuracy")
    avg_tokens = data.get("avg_tokens")
    avg_latency = data.get("avg_latency")
    return {
        "correct": correct,
        "total": total,
        "accuracy": accuracy,
        "avg_tokens": avg_tokens,
        "avg_latency": avg_latency,
        "score": (
            f"{correct}/{total}"
            if correct is not None and total is not None
            else NOT_AVAILABLE
        ),
        "accuracy_pct": (
            f"{float(accuracy) * 100:.0f}%"
            if accuracy is not None
            else NOT_AVAILABLE
        ),
    }


def display_value(value):
    if value is None or value == "":
        return NOT_AVAILABLE
    return value


def na_html(value):
    return html.escape(str(display_value(value)))


official = load_official_results()
summary = (official or {}).get("summary") or {}
total_questions = (official or {}).get("total_questions")
rag_stats = pipeline_stats(summary, "rag")
graphrag_stats = pipeline_stats(summary, "graphrag")
agentic_stats = pipeline_stats(summary, "agentic_graphrag")

if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "current_error" not in st.session_state:
    st.session_state.current_error = None
if "question_draft" not in st.session_state:
    st.session_state.question_draft = EXAMPLE_QUESTIONS[0]


st.html(
    f"""
<style>
html, body,
[data-testid="stAppViewContainer"] {{
    background: {BG};
}}
[data-testid="stHeader"],
[data-testid="stToolbar"] {{
    background: transparent;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #071725 0%, #06111D 100%);
    border-right: 1px solid {BORDER};
}}
.block-container {{
    padding-top: 1.25rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}}
h1, h2, h3, h4, p {{
    color: {TEXT};
}}
.section-title {{
    font-size: 21px;
    font-weight: 850;
    color: {TEXT};
    margin-top: 32px;
    margin-bottom: 6px;
}}
.section-sub {{
    color: {MUTED};
    font-size: 11px;
    margin-bottom: 16px;
    line-height: 1.5;
}}
.hero {{
    min-height: 220px;
    padding: 34px 40px;
    border-radius: 22px;
    border: 1px solid {BORDER};
    background:
        radial-gradient(circle at 85% 20%, rgba(56,189,248,0.15), transparent 35%),
        linear-gradient(145deg, #0C2334, #081622);
    box-shadow: 0 15px 40px rgba(0,0,0,0.18);
}}
.hero-small {{
    color: {CYAN};
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 2px;
    margin-bottom: 16px;
}}
.hero-title {{
    font-size: 44px;
    line-height: 1.05;
    font-weight: 900;
    letter-spacing: -1.5px;
    margin-bottom: 16px;
}}
.hero-title span {{
    color: {CYAN};
}}
.hero-text {{
    color: {MUTED};
    font-size: 13px;
    line-height: 1.8;
    max-width: 820px;
}}
.online {{
    display: inline-block;
    margin-top: 20px;
    padding: 8px 13px;
    border-radius: 20px;
    border: 1px solid rgba(45,212,191,0.35);
    background: rgba(45,212,191,0.06);
    color: {TEAL};
    font-size: 9px;
    font-weight: 850;
    letter-spacing: 1px;
}}
.metric, .info-card, .model-card {{
    min-height: 130px;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid {BORDER};
    background: linear-gradient(145deg, {PANEL2}, {PANEL});
    box-shadow: 0 8px 25px rgba(0,0,0,0.10);
}}
.metric-label {{
    color: {MUTED};
    font-size: 9px;
    font-weight: 850;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}
.metric-value {{
    font-size: 30px;
    font-weight: 900;
    margin-top: 12px;
}}
.metric-info {{
    color: {MUTED};
    font-size: 9px;
    margin-top: 6px;
}}
.info-title {{
    color: {TEXT};
    font-size: 14px;
    font-weight: 850;
    margin-bottom: 8px;
}}
.info-text {{
    color: {MUTED};
    font-size: 10px;
    line-height: 1.7;
}}
.model-name {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 900;
    margin-bottom: 14px;
}}
.model-number {{
    font-size: 31px;
    font-weight: 900;
    margin-top: 4px;
}}
.model-small {{
    color: {DIM};
    font-size: 9px;
    margin-top: 5px;
}}
.comparison-banner {{
    padding: 13px 16px;
    margin-top: 18px;
    margin-bottom: 10px;
    border-radius: 10px;
    border: 1px solid rgba(245,158,11,0.30);
    background: rgba(245,158,11,0.05);
    color: {MUTED};
    font-size: 10px;
    line-height: 1.6;
}}
.trace {{
    padding: 15px 16px;
    margin-bottom: 9px;
    border-radius: 11px;
    border: 1px solid {BORDER};
    background: linear-gradient(90deg, rgba(15,36,54,0.95), rgba(11,27,42,0.95));
}}
.trace-number {{
    color: {CYAN};
    font-size: 10px;
    font-weight: 900;
}}
.trace-title {{
    color: {TEXT};
    font-size: 12px;
    font-weight: 800;
}}
.trace-description {{
    color: {MUTED};
    font-size: 10px;
    margin-top: 5px;
    line-height: 1.5;
}}
.node {{
    display: inline-block;
    padding: 12px 16px;
    margin: 5px;
    border-radius: 10px;
    background: {PANEL2};
    border: 1px solid {BORDER};
    color: {TEXT};
    font-size: 10px;
    font-weight: 800;
}}
.node-main {{
    border-color: rgba(56,189,248,0.55);
    color: {CYAN};
}}
.arrow {{
    color: {CYAN};
    font-size: 18px;
    font-weight: 800;
}}
.stButton > button {{
    background: linear-gradient(135deg, {CYAN}, {BLUE}) !important;
    color: #03111C !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 900 !important;
    min-height: 46px !important;
    letter-spacing: 0.5px;
    box-shadow: 0 8px 25px rgba(56,189,248,0.18);
}}
label {{
    color: {MUTED} !important;
    font-size: 11px !important;
}}
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    overflow: hidden;
}}
.footer {{
    text-align: center;
    color: {DIM};
    font-size: 10px;
    line-height: 1.8;
    padding-top: 35px;
}}
</style>
"""
)

with st.sidebar:
    st.html(
        f"""
        <div style="padding:10px 4px 25px 4px; color:{TEXT}; font-family:Arial,sans-serif;">
            <div style="font-size:17px; font-weight:900; margin-bottom:30px;">
                <span style="color:{CYAN};">◆</span>
                EVIDENCE GRAPH
            </div>
            <div style="color:{MUTED}; font-size:9px; font-weight:800; letter-spacing:1.5px; margin-bottom:12px;">
                OLYMPIC HISTORY
            </div>
            <div style="color:{CYAN}; padding:8px 0; font-size:12px;">◉ Overview</div>
            <div style="color:{MUTED}; padding:8px 0; font-size:12px;">◦ Official Benchmark</div>
            <div style="color:{MUTED}; padding:8px 0; font-size:12px;">◦ Live Evidence Investigation</div>
            <hr style="border:0; border-top:1px solid {BORDER}; margin:25px 0;">
            <div style="color:{MUTED}; font-size:9px; font-weight:800; letter-spacing:1.5px; margin-bottom:12px;">
                PIPELINE
            </div>
            <div style="color:{GREEN}; padding:7px 0; font-size:11px;">● TigerGraph</div>
            <div style="color:{GREEN}; padding:7px 0; font-size:11px;">● Vector Search</div>
            <div style="color:{GREEN}; padding:7px 0; font-size:11px;">● Groq LLM</div>
            <hr style="border:0; border-top:1px solid {BORDER}; margin:25px 0;">
            <div style="color:{DIM}; font-size:9px; line-height:1.7;">
                USER QUESTION → UNDERSTAND → GRAPH / VECTOR → EVALUATE → ANSWER
            </div>
        </div>
        """
    )

st.html(
    """
    <div class="hero">
        <div class="hero-small">● EVIDENCE GRAPH</div>
        <div class="hero-title">
            Agentic GraphRAG
            <span>for Olympic History</span>
        </div>
        <div class="hero-text">
            Ask an Olympic history question. The live agent classifies the query,
            retrieves TigerGraph or vector evidence, evaluates what was found,
            and returns only an evidence-backed answer.
            <br><br>
            USER QUESTION → UNDERSTAND → GRAPH / VECTOR → EVALUATE → ANSWER
        </div>
        <div class="online">● LIVE INVESTIGATION READY</div>
    </div>
    """
)

st.html(
    """
    <div class="section-title">Official Benchmark</div>
    <div class="section-sub">
        Latest scores loaded from official_data/official_three_way_results.json.
        These values update automatically when the benchmark is rerun.
        They are not live-query metrics.
    </div>
    """
)

if not official:
    st.warning(
        "Official benchmark file was not found or could not be parsed: "
        "official_data/official_three_way_results.json"
    )
else:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">RAG</div>
                <div class="metric-value" style="color:{PURPLE};">{na_html(rag_stats['score'])}</div>
                <div class="metric-info">Accuracy {na_html(rag_stats['accuracy_pct'])}</div>
            </div>
            """
        )
    with m2:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">GraphRAG</div>
                <div class="metric-value" style="color:{TEAL};">{na_html(graphrag_stats['score'])}</div>
                <div class="metric-info">Accuracy {na_html(graphrag_stats['accuracy_pct'])}</div>
            </div>
            """
        )
    with m3:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Agentic GraphRAG</div>
                <div class="metric-value" style="color:{CYAN};">{na_html(agentic_stats['score'])}</div>
                <div class="metric-info">Accuracy {na_html(agentic_stats['accuracy_pct'])}</div>
            </div>
            """
        )
    with m4:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Questions</div>
                <div class="metric-value" style="color:{ORANGE};">{na_html(total_questions)}</div>
                <div class="metric-info">Official evaluation set</div>
            </div>
            """
        )

    c1, c2, c3 = st.columns(3, gap="medium")
    cards = [
        (c1, "RAG", rag_stats, PURPLE, "Retrieval-Augmented Generation"),
        (c2, "GraphRAG", graphrag_stats, TEAL, "TigerGraph retrieval"),
        (c3, "Agentic GraphRAG", agentic_stats, CYAN, "Understand → retrieve → evaluate"),
    ]
    for col, name, stats, color, caption in cards:
        with col:
            st.html(
                f"""
                <div class="model-card">
                    <div class="model-name">{html.escape(name)}</div>
                    <div class="metric-label">Correct / Total</div>
                    <div class="model-number" style="color:{color};">{na_html(stats['score'])}</div>
                    <div class="model-small">{html.escape(caption)}</div>
                    <br>
                    <div class="metric-label">Accuracy</div>
                    <div style="color:{TEXT}; font-size:20px; font-weight:800;">
                        {na_html(stats['accuracy_pct'])}
                    </div>
                    <div class="model-small">
                        Avg estimated tokens: {na_html(stats['avg_tokens'])}
                    </div>
                </div>
                """
            )

    st.markdown("#### Official Benchmark Comparison")
    comparison_table = pd.DataFrame(
        {
            "Model": ["RAG", "GraphRAG", "Agentic GraphRAG"],
            "Correct": [
                rag_stats["correct"],
                graphrag_stats["correct"],
                agentic_stats["correct"],
            ],
            "Total": [
                rag_stats["total"],
                graphrag_stats["total"],
                agentic_stats["total"],
            ],
            "Accuracy %": [
                None if rag_stats["accuracy"] is None else rag_stats["accuracy"] * 100,
                None if graphrag_stats["accuracy"] is None else graphrag_stats["accuracy"] * 100,
                None if agentic_stats["accuracy"] is None else agentic_stats["accuracy"] * 100,
            ],
            "Avg Tokens": [
                rag_stats["avg_tokens"],
                graphrag_stats["avg_tokens"],
                agentic_stats["avg_tokens"],
            ],
        }
    )
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)

    st.markdown("#### Official Accuracy")
    chart_accuracy = comparison_table[["Model", "Accuracy %"]].dropna(subset=["Accuracy %"])
    if not chart_accuracy.empty:
        st.bar_chart(chart_accuracy.set_index("Model"), height=300)
    else:
        st.info("Accuracy values are not available in the official JSON result file.")

st.html(
    """
    <div class="section-title">Live Evidence Investigation</div>
    <div class="section-sub">
        Ask an Olympic history question and inspect the evidence-backed investigation path.
    </div>
    """
)

st.text_area(
    "Olympic history question",
    key="question_draft",
    height=90,
    placeholder="Ask an Olympic history question...",
)

example_cols = st.columns(len(EXAMPLE_QUESTIONS))
for index, example in enumerate(EXAMPLE_QUESTIONS):
    if example_cols[index].button(
        f"Example {index + 1}",
        use_container_width=True,
        key=f"example_{index}",
    ):
        st.session_state.question_draft = example
        st.rerun()

investigate = st.button(
    "INVESTIGATE",
    type="primary",
    use_container_width=True,
)

if investigate:
    submitted = (st.session_state.question_draft or "").strip()
    st.session_state.current_question = submitted
    st.session_state.current_result = None
    st.session_state.current_error = None

    if not submitted:
        st.session_state.current_error = "Please enter a question."
    elif not BACKEND_AVAILABLE:
        st.session_state.current_error = (
            f"Backend could not be imported: {BACKEND_ERROR}"
        )
    else:
        with st.spinner("Investigating Olympic evidence..."):
            try:
                st.session_state.current_result = run_agent(submitted)
            except Exception as exc:
                st.session_state.current_error = str(exc)

current_question = st.session_state.current_question
current_result = st.session_state.current_result
current_error = st.session_state.current_error

if current_error and current_result is None:
    st.error(current_error)

if current_result is not None:
    result = current_result
    query_text = getattr(result, "question", None) or current_question or ""
    answer_text = result.get("final_answer") or NOT_AVAILABLE
    status = result.get("status") or NOT_AVAILABLE
    actions = result.get("actions_taken") or []
    evidence = result.get("evidence") or []
    errors = result.get("errors") or []

    st.markdown("### Query")
    st.html(
        f"""
        <div class="info-card">
            <div class="info-text">{html.escape(str(query_text))}</div>
        </div>
        """
    )

    st.markdown("### Answer")
    st.html(
        f"""
        <div style="
            padding:22px;
            border-radius:16px;
            border: 1px solid rgba(56,189,248,0.35);
            background: linear-gradient(145deg, #102B3F, #0A1B29);
        ">
            <div style="color:{CYAN}; font-size:10px; font-weight:900; letter-spacing:1.5px; margin-bottom:10px;">
                ● FINAL ANSWER
            </div>
            <div style="color:{TEXT}; font-size:17px; font-weight:750; line-height:1.6;">
                {html.escape(str(answer_text))}
            </div>
        </div>
        """
    )

    if errors and status != "completed":
        st.error(" ".join(str(item) for item in errors))
    elif errors:
        st.warning("Retrieval notes: " + " ".join(str(item) for item in errors))

    st.markdown("### Investigation")
    response_time = result.get("response_time")
    if isinstance(response_time, (int, float)):
        response_time_text = f"{response_time}s"
    else:
        response_time_text = display_value(response_time)

    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Status</div>
                <div class="metric-value" style="color:{GREEN if status == 'completed' else ORANGE};">
                    {na_html(status)}
                </div>
                <div class="metric-info">Current investigation only</div>
            </div>
            """
        )
    with i2:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Response time</div>
                <div class="metric-value" style="color:{CYAN};">
                    {html.escape(str(response_time_text))}
                </div>
                <div class="metric-info">Live query latency</div>
            </div>
            """
        )
    with i3:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Actions</div>
                <div class="metric-value" style="color:{PURPLE};">{len(actions)}</div>
                <div class="metric-info">{na_html(', '.join(actions) if actions else None)}</div>
            </div>
            """
        )
    with i4:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Evidence items</div>
                <div class="metric-value" style="color:{TEAL};">
                    {na_html(result.get('evidence_items'))}
                </div>
                <div class="metric-info">Retrieved for this question</div>
            </div>
            """
        )

    j1, j2, j3, j4 = st.columns(4)
    with j1:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Question type</div>
                <div style="color:{TEXT}; font-size:18px; font-weight:900; margin-top:12px;">
                    {na_html(result.get('question_type'))}
                </div>
            </div>
            """
        )
    with j2:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Route used</div>
                <div style="color:{TEXT}; font-size:18px; font-weight:900; margin-top:12px;">
                    {na_html(result.get('route_used'))}
                </div>
            </div>
            """
        )
    with j3:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Confidence</div>
                <div style="color:{TEXT}; font-size:18px; font-weight:900; margin-top:12px;">
                    {na_html(result.get('confidence'))}
                </div>
                <div class="metric-info">Not inferred from benchmark accuracy</div>
            </div>
            """
        )
    with j4:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">Estimated tokens</div>
                <div style="color:{TEXT}; font-size:18px; font-weight:900; margin-top:12px;">
                    {na_html(result.get('estimated_tokens'))}
                </div>
                <div class="metric-info">
                    Actual LLM tokens: {na_html(result.get('llm_tokens'))}
                </div>
            </div>
            """
        )

    st.markdown("### Evidence")
    if not evidence:
        st.info("No evidence items were returned for this investigation.")
    else:
        for index, item in enumerate(evidence[:12], start=1):
            if isinstance(item, dict):
                title = (
                    item.get("title")
                    or item.get("event_name")
                    or item.get("doc_id")
                    or f"Evidence {index}"
                )
                body_parts = []
                for key, value in item.items():
                    if key in {"text"} and value:
                        body_parts.append(str(value)[:600])
                    elif key not in {"text", "title"} and value not in (None, "", [], {}):
                        body_parts.append(f"{key}: {value}")
                body = "\n".join(body_parts)[:900]
            else:
                title = f"Evidence {index}"
                body = str(item)
            with st.expander(f"{index}. {title}"):
                st.text(body)

    st.markdown("### Trace")
    descriptions = {
        "UNDERSTAND": "Classified the submitted question before retrieval.",
        "GRAPH": "Queried TigerGraph with the official Olympic graph pipeline.",
        "VECTOR_SEARCH": "Used vector / RAG retrieval as the evidence source or fallback.",
        "EVALUATE_EVIDENCE": "Checked whether retrieved evidence produced an answer.",
        "STOP": "Ended the investigation after evaluation.",
    }
    if not actions:
        st.info("No investigation actions were recorded.")
    else:
        for index, action in enumerate(actions, start=1):
            description = descriptions.get(
                str(action),
                "Recorded by the live investigation backend.",
            )
            st.html(
                f"""
                <div class="trace">
                    <span class="trace-number">{index:02d}</span>
                    <span class="trace-title"> {html.escape(str(action))}</span>
                    <div class="trace-description">{html.escape(description)}</div>
                </div>
                """
            )

st.html(
    f"""
    <div class="section-title">Agentic Architecture</div>
    <div class="section-sub">Live investigation flow used by this dashboard</div>
    <div class="info-card" style="text-align:center; padding:24px 8px;">
        <span class="node">USER QUESTION</span>
        <span class="arrow">→</span>
        <span class="node">UNDERSTAND</span>
        <span class="arrow">→</span>
        <span class="node node-main">GRAPH / VECTOR</span>
        <span class="arrow">→</span>
        <span class="node">EVALUATE</span>
        <span class="arrow">→</span>
        <span class="node node-main">ANSWER</span>
    </div>
    """
)

st.html(
    f"""
    <div class="footer">
        <b style="color:{CYAN};">EVIDENCE GRAPH</b><br>
        Agentic GraphRAG for Olympic History<br><br>
        Official benchmark values are read from official_three_way_results.json
    </div>
    """
)
