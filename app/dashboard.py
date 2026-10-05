import json
import sys
import html
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EVIDENCE GRAPH — Agentic GraphRAG",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKEND_DIR = PROJECT_ROOT / "backend"

RESULTS_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "results.json"
)

# IMPORTANT:
# Three-way benchmark file
THREE_WAY_RESULTS_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "three_way_results.json"
)


# ============================================================
# BACKEND IMPORT
# ============================================================

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:

    from agent import run_agent

    BACKEND_AVAILABLE = True

except Exception as e:

    BACKEND_AVAILABLE = False
    BACKEND_ERROR = str(e)


# ============================================================
# COLORS
# ============================================================

BG = "#06111D"

PANEL = "#0B1B2A"
PANEL2 = "#0F2436"
PANEL3 = "#122D42"

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


# ============================================================
# LOAD AGENTIC RESULTS
# ============================================================

def load_results():

    if not RESULTS_FILE.exists():
        return None

    try:

        with open(
            RESULTS_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:

        return None


results = load_results()


if results:

    accuracy = (
        results.get("accuracy", 0) * 100
    )

    completeness = (
        results.get("completeness", 0) * 100
    )

    average_tokens = results.get(
        "average_estimated_tokens",
        0,
    )

    total_questions = results.get(
        "total_questions",
        0,
    )

    correct = results.get(
        "correct",
        0,
    )

    benchmark_rows = results.get(
        "results",
        [],
    )

else:

    accuracy = 0
    completeness = 0
    average_tokens = 0
    total_questions = 0
    correct = 0
    benchmark_rows = []


# ============================================================
# LOAD THREE-WAY BENCHMARK
# ============================================================

def load_three_way_results():

    if not THREE_WAY_RESULTS_FILE.exists():
        return None

    try:

        with open(
            THREE_WAY_RESULTS_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            return json.load(f)

    except Exception:

        return None


comparison = load_three_way_results()


# ============================================================
# SAFE METRIC FORMATTERS
# ============================================================

def format_percentage(value):

    if value is None:
        return "—"

    try:

        return f"{float(value) * 100:.0f}%"

    except Exception:

        return "—"


def format_tokens(value):

    if value is None:
        return "—"

    try:

        return f"{float(value):.1f}"

    except Exception:

        return "—"


# ============================================================
# GET MODEL VALUES
# ============================================================

if comparison:

    model_data = comparison.get(
        "models",
        {},
    )

else:

    model_data = {}


rag_data = model_data.get(
    "RAG",
    {},
)

graphrag_data = model_data.get(
    "GraphRAG",
    {},
)

agentic_data = model_data.get(
    "Agentic GraphRAG",
    {},
)


# ============================================================
# ROBUST TOKEN READER
# ============================================================

def get_average_tokens(data):

    if not data:
        return None

    # Main name used by three_way_results.json
    if data.get(
        "average_estimated_tokens"
    ) is not None:

        return data.get(
            "average_estimated_tokens"
        )

    # Fallback names
    if data.get(
        "average_tokens"
    ) is not None:

        return data.get(
            "average_tokens"
        )

    if data.get(
        "avg_tokens"
    ) is not None:

        return data.get(
            "avg_tokens"
        )

    if data.get(
        "estimated_tokens"
    ) is not None:

        return data.get(
            "estimated_tokens"
        )

    return None


rag_accuracy = rag_data.get(
    "accuracy"
)

rag_completeness = rag_data.get(
    "completeness"
)

rag_tokens = get_average_tokens(
    rag_data
)


graphrag_accuracy = graphrag_data.get(
    "accuracy"
)

graphrag_completeness = graphrag_data.get(
    "completeness"
)

graphrag_tokens = get_average_tokens(
    graphrag_data
)


agentic_accuracy = agentic_data.get(
    "accuracy"
)

agentic_completeness = agentic_data.get(
    "completeness"
)

agentic_tokens = get_average_tokens(
    agentic_data
)


# ============================================================
# GLOBAL CSS
# ============================================================

st.html(
    f"""
<style>

html, body,
[data-testid="stAppViewContainer"] {{
    background: {BG};
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

[data-testid="stToolbar"] {{
    background: transparent;
}}

[data-testid="stSidebar"] {{

    background:
        linear-gradient(
            180deg,
            #071725 0%,
            #06111D 100%
        );

    border-right:
        1px solid {BORDER};
}}

.block-container {{

    padding-top: 1.25rem;
    padding-bottom: 3rem;

    max-width: 1500px;
}}

h1, h2, h3, h4, p {{
    color: {TEXT};
}}


/* ========================================================
   SECTIONS
   ======================================================== */

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


/* ========================================================
   HERO
   ======================================================== */

.hero {{

    min-height: 245px;

    padding: 34px 40px;

    border-radius: 22px;

    border: 1px solid {BORDER};

    background:

        radial-gradient(
            circle at 85% 20%,
            rgba(56,189,248,0.15),
            transparent 35%
        ),

        linear-gradient(
            145deg,
            #0C2334,
            #081622
        );

    box-shadow:
        0 15px 40px
        rgba(0,0,0,0.18);
}}

.hero-small {{

    color: {CYAN};

    font-size: 10px;

    font-weight: 850;

    letter-spacing: 2px;

    margin-bottom: 16px;
}}

.hero-title {{

    font-size: 48px;

    line-height: 1.0;

    font-weight: 900;

    letter-spacing: -2px;

    margin-bottom: 20px;
}}

.hero-title span {{
    color: {CYAN};
}}

.hero-text {{

    color: {MUTED};

    font-size: 13px;

    line-height: 1.8;

    max-width: 760px;
}}

.online {{

    display: inline-block;

    margin-top: 20px;

    padding: 8px 13px;

    border-radius: 20px;

    border:
        1px solid
        rgba(45,212,191,0.35);

    background:
        rgba(45,212,191,0.06);

    color: {TEAL};

    font-size: 9px;

    font-weight: 850;

    letter-spacing: 1px;
}}


/* ========================================================
   CARDS
   ======================================================== */

.metric {{

    min-height: 130px;

    padding: 20px;

    border-radius: 15px;

    border: 1px solid {BORDER};

    background:
        linear-gradient(
            145deg,
            {PANEL2},
            {PANEL}
        );

    box-shadow:
        0 8px 25px
        rgba(0,0,0,0.10);
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

.info-card {{

    padding: 20px;

    border-radius: 15px;

    border: 1px solid {BORDER};

    background:
        linear-gradient(
            145deg,
            {PANEL2},
            {PANEL}
        );

    box-shadow:
        0 8px 25px
        rgba(0,0,0,0.10);
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


/* ========================================================
   MODEL COMPARISON
   ======================================================== */

.model-card {{

    padding: 22px;

    border-radius: 16px;

    border: 1px solid {BORDER};

    background:
        linear-gradient(
            145deg,
            {PANEL2},
            {PANEL}
        );

    min-height: 190px;
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

    border:
        1px solid
        rgba(245,158,11,0.30);

    background:
        rgba(245,158,11,0.05);

    color: {MUTED};

    font-size: 10px;

    line-height: 1.6;
}}


/* ========================================================
   TRACE
   ======================================================== */

.trace {{

    padding: 15px 16px;

    margin-bottom: 9px;

    border-radius: 11px;

    border: 1px solid {BORDER};

    background:
        linear-gradient(
            90deg,
            rgba(15,36,54,0.95),
            rgba(11,27,42,0.95)
        );
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


/* ========================================================
   GRAPH
   ======================================================== */

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

    border-color:
        rgba(56,189,248,0.55);

    color: {CYAN};

    box-shadow:
        0 0 20px
        rgba(56,189,248,0.07);
}}

.arrow {{

    color: {CYAN};

    font-size: 18px;

    font-weight: 800;
}}


/* ========================================================
   BUTTON
   ======================================================== */

[data-testid="stButton"] button {{

    background:
        linear-gradient(
            135deg,
            {CYAN},
            {BLUE}
        ) !important;

    color:
        #03111C !important;

    border:
        none !important;

    border-radius:
        10px !important;

    font-weight:
        900 !important;

    min-height:
        46px !important;

    letter-spacing:
        0.5px;

    box-shadow:
        0 8px 25px
        rgba(56,189,248,0.18);
}}

[data-testid="stButton"] button:hover {{

    box-shadow:
        0 10px 30px
        rgba(56,189,248,0.30);

    transform:
        translateY(-1px);
}}


/* ========================================================
   INPUTS
   ======================================================== */

div[data-baseweb="select"] > div {{

    background:
        {PANEL2} !important;

    border-color:
        {BORDER} !important;

    color:
        {TEXT} !important;
}}

div[data-baseweb="input"] > div {{

    background:
        {PANEL2} !important;

    border-color:
        {BORDER} !important;

    color:
        {TEXT} !important;
}}

input {{
    color: {TEXT} !important;
}}

label {{
    color: {MUTED} !important;
    font-size: 11px !important;
}}


/* ========================================================
   DATAFRAME
   ======================================================== */

[data-testid="stDataFrame"] {{
    border:
        1px solid {BORDER};

    border-radius:
        12px;

    overflow:
        hidden;
}}


/* ========================================================
   EXPANDERS
   ======================================================== */

[data-testid="stExpander"] {{

    background: {PANEL};

    border:
        1px solid {BORDER};

    border-radius: 10px;
}}


/* ========================================================
   FOOTER
   ======================================================== */

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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        f"""
        <div style="
            padding:10px 4px 25px 4px;
            color:{TEXT};
            font-family:Arial,sans-serif;
        ">

            <div style="
                font-size:17px;
                font-weight:900;
                margin-bottom:30px;
            ">

                <span style="color:{CYAN};">
                    ◆
                </span>

                EVIDENCE GRAPH

            </div>


            <div style="
                color:{MUTED};
                font-size:9px;
                font-weight:800;
                letter-spacing:1.5px;
                margin-bottom:12px;
            ">
                INTELLIGENCE
            </div>


            <div style="
                color:{CYAN};
                padding:8px 0;
                font-size:12px;
            ">
                ◉ Overview
            </div>


            <div style="
                color:{MUTED};
                padding:8px 0;
                font-size:12px;
            ">
                ◦ Model Comparison
            </div>


            <div style="
                color:{MUTED};
                padding:8px 0;
                font-size:12px;
            ">
                ◦ Olympics Evidence Intelligence
            </div>


            <div style="
                color:{MUTED};
                padding:8px 0;
                font-size:12px;
            ">
                ◦ System Architecture
            </div>


            <div style="
                color:{MUTED};
                padding:8px 0;
                font-size:12px;
            ">
                ◦ Evidence Graph
            </div>


            <div style="
                color:{MUTED};
                padding:8px 0;
                font-size:12px;
            ">
                ◦ Live Agent Investigation
            </div>


            <hr style="
                border:0;
                border-top:1px solid {BORDER};
                margin:25px 0;
            ">


            <div style="
                color:{MUTED};
                font-size:9px;
                font-weight:800;
                letter-spacing:1.5px;
                margin-bottom:12px;
            ">
                SYSTEM
            </div>


            <div style="
                color:{GREEN};
                padding:7px 0;
                font-size:11px;
            ">
                ● TigerGraph
            </div>


            <div style="
                color:{GREEN};
                padding:7px 0;
                font-size:11px;
            ">
                ● Vector Search
            </div>


            <div style="
                color:{GREEN};
                padding:7px 0;
                font-size:11px;
            ">
                ● Agent Orchestrator
            </div>


            <hr style="
                border:0;
                border-top:1px solid {BORDER};
                margin:25px 0;
            ">


            <div style="
                color:{DIM};
                font-size:9px;
                line-height:1.7;
            ">

                <b style="color:{MUTED};">
                    BENCHMARK
                </b>

                <br>

                Olympics Benchmark

            </div>

        </div>
        """
    )


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero">

        <div class="hero-small">
            ● THREE-WAY RETRIEVAL & REASONING BENCHMARK
        </div>


        <div class="hero-title">

            EVIDENCE GRAPH
            <span>— Agentic GraphRAG</span>

        </div>


        <div class="hero-text">

            Agentic GraphRAG — Olympics Benchmark

            <br><br>

            Agentic GraphRAG combines TigerGraph
            multi-hop reasoning with semantic evidence
            retrieval to investigate questions and
            produce explainable answers.

        </div>


        <div class="online">
            ● SYSTEM ONLINE
        </div>

    </div>
    """
)


# ============================================================
# SYSTEM PERFORMANCE
# ============================================================

st.html(
    """
    <div class="section-title">
        System Performance
    </div>

    <div class="section-sub">
        Current Agentic GraphRAG investigation results
        from the custom demonstration benchmark
    </div>
    """
)


m1, m2, m3, m4 = st.columns(4)


with m1:

    st.html(
        f"""
        <div class="metric">

            <div class="metric-label">
                Agentic Accuracy
            </div>

            <div
                class="metric-value"
                style="color:{CYAN};"
            >
                {accuracy:.0f}%
            </div>

            <div class="metric-info">
                Agentic GraphRAG
            </div>

        </div>
        """
    )


with m2:

    st.html(
        f"""
        <div class="metric">

            <div class="metric-label">
                Completeness
            </div>

            <div
                class="metric-value"
                style="color:{TEAL};"
            >
                {completeness:.0f}%
            </div>

            <div class="metric-info">
                Agentic evidence coverage
            </div>

        </div>
        """
    )


with m3:

    st.html(
        f"""
        <div class="metric">

            <div class="metric-label">
                Questions
            </div>

            <div
                class="metric-value"
                style="color:{PURPLE};"
            >
                {correct}/{total_questions}
            </div>

            <div class="metric-info">
                Correct investigations
            </div>

        </div>
        """
    )


with m4:

    st.html(
        f"""
        <div class="metric">

            <div class="metric-label">
                Avg Tokens
            </div>

            <div
                class="metric-value"
                style="color:{ORANGE};"
            >
                {average_tokens:.1f}
            </div>

            <div class="metric-info">
                Local estimate
            </div>

        </div>
        """
    )


# ============================================================
# BENCHMARK WARNING
# ============================================================

st.html(
    f"""
    <div class="comparison-banner">

        <b style="color:{ORANGE};">
            BENCHMARK STATUS
        </b>

        &nbsp;

        These measurements represent the
        custom demonstration dataset used during development.
        They are not the official hackathon benchmark results.

        <br>

        Token values are local estimated token counts,
        not exact API token usage.

    </div>
    """
)


# ============================================================
# MODEL COMPARISON
# ============================================================

st.html(
    """
    <div class="section-title">
        RAG vs GraphRAG vs Agentic GraphRAG
    </div>

    <div class="section-sub">
        Same benchmark questions evaluated across
        three retrieval and reasoning approaches
    </div>
    """
)


# ============================================================
# THREE MODEL CARDS
# ============================================================

c1, c2, c3 = st.columns(
    3,
    gap="medium",
)


# ============================================================
# RAG
# ============================================================

with c1:

    st.html(
        f"""
        <div class="model-card">

            <div class="model-name">
                RAG
            </div>

            <div class="metric-label">
                Accuracy
            </div>

            <div
                class="model-number"
                style="color:{PURPLE};"
            >
                {format_percentage(rag_accuracy)}
            </div>

            <div class="model-small">
                Retrieval-Augmented Generation
            </div>

            <br>

            <div class="metric-label">
                Completeness
            </div>

            <div style="
                color:{TEXT};
                font-size:20px;
                font-weight:800;
            ">
                {format_percentage(rag_completeness)}
            </div>

            <div class="model-small">
                Avg tokens:
                {format_tokens(rag_tokens)}
            </div>

        </div>
        """
    )


# ============================================================
# GRAPHRAG
# ============================================================

with c2:

    st.html(
        f"""
        <div class="model-card">

            <div class="model-name">
                GraphRAG
            </div>

            <div class="metric-label">
                Accuracy
            </div>

            <div
                class="model-number"
                style="color:{TEAL};"
            >
                {format_percentage(graphrag_accuracy)}
            </div>

            <div class="model-small">
                Graph-based multi-hop retrieval
            </div>

            <br>

            <div class="metric-label">
                Completeness
            </div>

            <div style="
                color:{TEXT};
                font-size:20px;
                font-weight:800;
            ">
                {format_percentage(graphrag_completeness)}
            </div>

            <div class="model-small">
                Avg tokens:
                {format_tokens(graphrag_tokens)}
            </div>

        </div>
        """
    )


# ============================================================
# AGENTIC GRAPHRAG
# ============================================================

with c3:

    st.html(
        f"""
        <div
            class="model-card"
            style="
                border-color:
                rgba(56,189,248,0.55);
            "
        >

            <div class="model-name">
                Agentic GraphRAG
            </div>

            <div class="metric-label">
                Accuracy
            </div>

            <div
                class="model-number"
                style="color:{CYAN};"
            >
                {format_percentage(agentic_accuracy)}
            </div>

            <div class="model-small">
                Agent-controlled investigation
            </div>

            <br>

            <div class="metric-label">
                Completeness
            </div>

            <div style="
                color:{TEXT};
                font-size:20px;
                font-weight:800;
            ">
                {format_percentage(agentic_completeness)}
            </div>

            <div class="model-small">
                Avg tokens:
                {format_tokens(agentic_tokens)}
            </div>

        </div>
        """
    )


# ============================================================
# COMPARISON TABLE
# ============================================================

st.markdown("#### Benchmark Comparison")


comparison_table = pd.DataFrame(
    {
        "Model": [
            "RAG",
            "GraphRAG",
            "Agentic GraphRAG",
        ],

        "Accuracy": [
            (
                rag_accuracy * 100
                if rag_accuracy is not None
                else None
            ),

            (
                graphrag_accuracy * 100
                if graphrag_accuracy is not None
                else None
            ),

            (
                agentic_accuracy * 100
                if agentic_accuracy is not None
                else None
            ),
        ],

        "Completeness": [
            (
                rag_completeness * 100
                if rag_completeness is not None
                else None
            ),

            (
                graphrag_completeness * 100
                if graphrag_completeness is not None
                else None
            ),

            (
                agentic_completeness * 100
                if agentic_completeness is not None
                else None
            ),
        ],

        "Avg Tokens": [
            rag_tokens,
            graphrag_tokens,
            agentic_tokens,
        ],
    }
)


st.dataframe(
    comparison_table,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# MODEL ACCURACY CHART
# ============================================================

st.markdown("#### Model Accuracy Comparison")


chart_accuracy = comparison_table[
    ["Model", "Accuracy"]
].dropna(
    subset=["Accuracy"]
)


if not chart_accuracy.empty:

    st.bar_chart(
        chart_accuracy.set_index("Model"),
        height=300,
    )

else:

    st.info(
        "Three-way benchmark data is not available."
    )


# ============================================================
# MODEL COMPLETENESS CHART
# ============================================================

st.markdown("#### Model Completeness Comparison")


chart_completeness = comparison_table[
    ["Model", "Completeness"]
].dropna(
    subset=["Completeness"]
)


if not chart_completeness.empty:

    st.bar_chart(
        chart_completeness.set_index("Model"),
        height=300,
    )

else:

    st.info(
        "Completeness measurements are not available."
    )


# ============================================================
# MODEL TOKEN COMPARISON
# ============================================================

st.markdown("#### Token Efficiency Comparison")


st.caption(
    "Lower estimated tokens indicate a shorter retrieved/generated "
    "response in this local benchmark. These are estimates, not "
    "exact API token counts."
)


chart_tokens = comparison_table[
    ["Model", "Avg Tokens"]
].dropna(
    subset=["Avg Tokens"]
)


if not chart_tokens.empty:

    st.bar_chart(
        chart_tokens.set_index("Model"),
        height=300,
    )

else:

    st.info(
        "Token measurements are not available yet."
    )


# ============================================================
# MODEL PERFORMANCE BY QUESTION
# ============================================================

st.html(
    """
    <div class="section-title">
        Agentic Model Performance
    </div>

    <div class="section-sub">
        Question-level accuracy and confidence
        for the Agentic GraphRAG system
    </div>
    """
)


if benchmark_rows:

    graph_data = []

    for index, item in enumerate(
        benchmark_rows,
        start=1,
    ):

        try:

            confidence = (
                float(
                    item.get(
                        "confidence",
                        0,
                    )
                ) * 100
            )

        except Exception:

            confidence = 0


        graph_data.append(
            {
                "Question": f"Q{index}",

                "Accuracy": (
                    100
                    if item.get(
                        "correct",
                        False,
                    )
                    else 0
                ),

                "Confidence": round(
                    confidence,
                    1,
                ),
            }
        )


    graph_df = pd.DataFrame(
        graph_data
    )


    chart_col1, chart_col2 = st.columns(
        [1.3, 1],
        gap="medium",
    )


    with chart_col1:

        st.markdown(
            "#### Accuracy by Question"
        )

        st.bar_chart(
            graph_df.set_index(
                "Question"
            )[["Accuracy"]],
            height=300,
        )


    with chart_col2:

        st.markdown(
            "#### Agent Confidence"
        )

        st.line_chart(
            graph_df.set_index(
                "Question"
            )[["Confidence"]],
            height=300,
        )


else:

    st.info(
        "Run the three-way benchmark to generate "
        "performance data."
    )


# ============================================================
# LIVE AGENT INVESTIGATION INPUT
# ============================================================

question = st.selectbox(
    "SELECT AN OLYMPICS QUESTION",
    question_options,
    key="olympics_question_select",
)

custom_question = st.text_input(
    "Or enter your own question",
    placeholder="Ask an Olympic question...",
    key="custom_olympics_question",
)

investigate = st.button(
    "🔎 INVESTIGATE",
    type="primary",
    use_container_width=True,
    key="investigate_button",
)

# ============================================================
# PROCESS INVESTIGATION
# ============================================================

if investigate:

    # Capture submitted question.
    if custom_question.strip():
        active_question = custom_question.strip()
    else:
        active_question = question.strip()

    # Clear previous result.
    st.session_state.pop("agent_result", None)
    st.session_state.pop("agent_question", None)

    st.session_state["agent_question"] = active_question

    if not BACKEND_AVAILABLE:
        st.error("❌ Backend could not be imported.")
        st.code(BACKEND_ERROR)
    else:
        with st.spinner("Agent is investigating the evidence..."):
            try:
                new_agent_result = run_agent(active_question)

                st.session_state["agent_result"] = new_agent_result
                st.session_state["agent_question"] = active_question

            except Exception as e:
                st.session_state.pop("agent_result", None)
                st.error(f"❌ Investigation failed: {e}")
                st.exception(e)



# ============================================================
# INVESTIGATION RESULT
# ============================================================

if "agent_result" in st.session_state:

    agent_result = st.session_state[
        "agent_result"
    ]


    st.html(
        """
        <div class="section-title">
            Investigation Result
        </div>

        <div class="section-sub">
            Answer generated from the current evidence
        </div>
        """
    )


    result_col1, result_col2 = st.columns(
        [1.25, 0.75],
        gap="medium",
    )


    with result_col1:

        answer = (
            agent_result.final_answer
            or "No final answer generated."
        )


        safe_answer = html.escape(
            str(answer)
        )


        safe_question = html.escape(
            str(
                st.session_state.get(
                    "agent_question",
                    "",
                )
            )
        )


        st.html(
            f"""
            <div style="
                padding:22px;

                border-radius:16px;

                border:
                    1px solid
                    rgba(56,189,248,0.35);

                background:
                    linear-gradient(
                        145deg,
                        #102B3F,
                        #0A1B29
                    );
            ">

                <div style="
                    color:{CYAN};

                    font-size:10px;

                    font-weight:900;

                    letter-spacing:1.5px;

                    margin-bottom:10px;
                ">
                    ● AGENT ANSWER
                </div>


                <div style="
                    color:{TEXT};

                    font-size:17px;

                    font-weight:750;

                    line-height:1.6;
                ">
                    {safe_answer}
                </div>

            </div>
            """
        )


        st.html(
            f"""
            <div
                class="info-card"
                style="margin-top:12px;"
            >

                <div class="info-title">
                    Investigation Query
                </div>

                <div class="info-text">
                    {safe_question}
                </div>

            </div>
            """
        )


    with result_col2:

        try:

            confidence = float(
                agent_result.confidence
            )

        except Exception:

            confidence = 0


        confidence = min(
            max(confidence, 0),
            1,
        )


        st.html(
            f"""
            <div class="info-card">

                <div class="metric-label">
                    AGENT CONFIDENCE
                </div>

                <div style="
                    font-size:38px;

                    font-weight:900;

                    color:{TEAL};

                    margin-top:10px;
                ">
                    {confidence * 100:.0f}%
                </div>

                <div class="metric-info">
                    Evidence confidence
                    after evaluation
                </div>

            </div>
            """
        )


        st.progress(
            confidence
        )


# ============================================================
# AGENT TRACE
# ============================================================

if "agent_result" in st.session_state:

    agent_result = st.session_state[
        "agent_result"
    ]

    st.html(
        """
        <div class="section-title">
            EVIDENCE GRAPH — OLYMPICS QUESTION ORCHESTRATOR
        </div>

        <div class="section-sub">
            The orchestrator identifies the question type and selects the appropriate retrieval and reasoning path.
        </div>
        """
    )

    # --------------------------------------------------------
    # Agent state summary
    # --------------------------------------------------------

    required = getattr(
        agent_result,
        "required_information",
        [],
    ) or []

    actions = getattr(
        agent_result,
        "actions_taken",
        [],
    ) or []

    missing = getattr(
        agent_result,
        "missing_information",
        [],
    ) or []

    try:
        trace_confidence = float(
            getattr(agent_result, "confidence", 0)
        )
    except Exception:
        trace_confidence = 0.0

    trace_confidence = min(
        max(trace_confidence, 0.0),
        1.0,
    )

    evidence_agrees = bool(
        getattr(
            agent_result,
            "evidence_agrees",
            False,
        )
    )

    stopped = bool(
        getattr(
            agent_result,
            "stopped",
            False,
        )
    )

    state_c1, state_c2, state_c3, state_c4 = st.columns(4)

    with state_c1:
        required_text = ", ".join(required) if required else "None"
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">
                    REQUIRED INFORMATION
                </div>
                <div style="
                    color:{CYAN};
                    font-size:18px;
                    font-weight:900;
                    margin-top:12px;
                ">
                    {html.escape(required_text)}
                </div>
                <div class="metric-info">
                    What the question requires
                </div>
            </div>
            """
        )

    with state_c2:
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">
                    ACTIONS TAKEN
                </div>
                <div style="
                    color:{PURPLE};
                    font-size:30px;
                    font-weight:900;
                    margin-top:8px;
                ">
                    {len(actions)}
                </div>
                <div class="metric-info">
                    Adaptive investigation steps
                </div>
            </div>
            """
        )

    with state_c3:
        agreement_text = "TRUE" if evidence_agrees else "PENDING"
        agreement_color = GREEN if evidence_agrees else ORANGE
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">
                    EVIDENCE AGREEMENT
                </div>
                <div style="
                    color:{agreement_color};
                    font-size:22px;
                    font-weight:900;
                    margin-top:12px;
                ">
                    {agreement_text}
                </div>
                <div class="metric-info">
                    Graph and document evidence
                </div>
            </div>
            """
        )

    with state_c4:
        status_text = "COMPLETE" if stopped else "RUNNING"
        status_color = GREEN if stopped else CYAN
        st.html(
            f"""
            <div class="metric">
                <div class="metric-label">
                    INVESTIGATION STATUS
                </div>
                <div style="
                    color:{status_color};
                    font-size:19px;
                    font-weight:900;
                    margin-top:12px;
                ">
                    {status_text}
                </div>
                <div class="metric-info">
                    Confidence: {trace_confidence * 100:.0f}%
                </div>
            </div>
            """
        )

    # --------------------------------------------------------
    # Action-by-action trace
    # --------------------------------------------------------

    action_descriptions = {
        "MARKET_GRAPH": (
            "Used the reverse graph path to resolve target entities "
            "through multi-hop graph relationships."
        ),
        "GRAPH": (
            "Traversed TigerGraph relationships to collect multi-hop "
            "evidence across entities."
        ),
        "VECTOR": (
            "Retrieved supporting document evidence using semantic "
            "vector search."
        ),
        "EVALUATE": (
            "Compared the collected evidence and evaluated whether "
            "the answer was sufficiently supported."
        ),
        "ENTITY": (
            "Linked entities mentioned in the question to known graph "
            "entities before selecting the next investigation action."
        ),
        "STOP": (
            "The stopping condition was reached, so the agent ended "
            "the investigation."
        ),
    }

    if actions:

        for index, action in enumerate(
            actions,
            start=1,
        ):

            action_name = str(action)
            action_upper = action_name.upper()

            description = action_descriptions.get(
                action_upper,
                "The orchestrator selected this investigation action "
                "based on the current evidence and missing information.",
            )

            if action_upper == "EVALUATE":
                icon = "✓"
            elif action_upper == "VECTOR":
                icon = "◇"
            elif action_upper == "MARKET_GRAPH":
                icon = "◆"
            elif action_upper == "GRAPH":
                icon = "◆"
            elif action_upper == "ENTITY":
                icon = "◎"
            elif action_upper == "STOP":
                icon = "■"
            else:
                icon = "•"

            st.html(
                f"""
                <div class="trace">
                    <span
                        class="trace-number"
                        style="margin-right:8px;"
                    >
                        {index:02d}
                    </span>

                    <span
                        style="
                            color:{CYAN};
                            font-size:12px;
                            font-weight:900;
                            margin-right:7px;
                        "
                    >
                        {icon}
                    </span>

                    <span class="trace-title">
                        {html.escape(action_name)}
                    </span>

                    <div class="trace-description">
                        {html.escape(description)}
                    </div>
                </div>
                """
            )

    else:
        st.info(
            "No agent actions recorded. Run an investigation to view the live trace."
        )

    # --------------------------------------------------------
    # Missing information / completion message
    # --------------------------------------------------------

    if missing:
        missing_text = ", ".join(str(item) for item in missing)
        st.html(
            f"""
            <div class="comparison-banner" style="border-color:rgba(245,158,11,0.35);">
                <b style="color:{ORANGE};">MORE INVESTIGATION MAY BE NEEDED</b><br>
                Missing information: {html.escape(missing_text)}
            </div>
            """
        )
    elif stopped:
        st.html(
            f"""
            <div class="comparison-banner" style="border-color:rgba(45,212,191,0.30);">
                <b style="color:{TEAL};">INVESTIGATION COMPLETE</b><br>
                The agent stopped after collecting and evaluating the available evidence.
                Final confidence: {trace_confidence * 100:.0f}%.
            </div>
            """
        )


# ============================================================
# EVIDENCE GRAPH
# ============================================================

st.html(
    """
    <div class="section-title">
        Evidence Graph
    </div>

    <div class="section-sub">
        Multi-hop relationships used during investigation
    </div>
    """
)


graph_col1, graph_col2 = st.columns(
    [1.35, 0.75],
    gap="medium",
)


with graph_col1:

    st.html(
        f"""
        <div
            class="info-card"
            style="
                text-align:center;
                min-height:220px;
            "
        >

            <div style="
                padding:25px 5px;
            ">

                <div class="node node-main">
                    🏅 Athlete
                </div>

                <span class="arrow">
                    →
                </span>

                <div class="node">
                    🥇 Medal
                </div>

                <span class="arrow">
                    →
                </span>

                <div class="node node-main">
                    🏟️ Event
                </div>

                <br>

                <div class="node">
                    🏛️ Venue
                </div>

                <span class="arrow">
                    →
                </span>

                <div class="node node-main">
                    🧠 Evidence
                </div>

            </div>

            <div style="
                color:{MUTED};
                font-size:10px;
                line-height:1.7;
            ">

                Athlete → Medal → Event

                <br>

                Event → Venue / Host Year

                <br>

                Vector evidence supports graph evidence

            </div>

        </div>
        """
    )


with graph_col2:

    st.html(
        f"""
        <div class="info-card">

            <div class="info-title">
                Graph Intelligence
            </div>

            <div class="info-text">

                <b style="color:{CYAN};">
                    8
                </b>

                vertex types

                <br><br>

                <b style="color:{TEAL};">
                    10
                </b>

                relationship types

                <br><br>

                <b style="color:{PURPLE};">
                    Multi-hop
                </b>

                traversal

                <br><br>

                <b style="color:{ORANGE};">
                    Vector
                </b>

                evidence verification

            </div>

        </div>
        """
    )


# ============================================================
# OLYMPICS EVIDENCE INTELLIGENCE
# ============================================================

st.html(
    """
    <div class="section-title">
        OLYMPICS EVIDENCE INTELLIGENCE
    </div>

    <div class="section-sub">
        Evidence-backed intelligence from Olympic documents and structured graph relationships.
    </div>
    """
)


d1, d2, d3 = st.columns(3)


with d1:

    st.html(
        f"""
        <div class="info-card">

            <div style="
                font-size:25px;
                margin-bottom:12px;
            ">
                🏅
            </div>

            <div class="info-title">
                Olympic Events & Sports
            </div>

            <div class="info-text">

                Connected competition events and sports in the structured evidence graph.

            </div>

        </div>
        """
    )


with d2:

    st.html(
        f"""
        <div class="info-card">

            <div style="
                font-size:25px;
                margin-bottom:12px;
            ">
                🥇
            </div>

            <div class="info-title">
                Athletes & Medals
            </div>

            <div class="info-text">

                Medal winners, competitors, and representing nations linked through graph relationships.

            </div>

        </div>
        """
    )


with d3:

    st.html(
        f"""
        <div class="info-card">

            <div style="
                font-size:25px;
                margin-bottom:12px;
            ">
                🏛️
            </div>

            <div class="info-title">
                Venues & Host Editions
            </div>

            <div class="info-text">

                Olympic host cities, stadiums, and competition dates connected across multi-hop paths.

            </div>

        </div>
        """
    )


# ============================================================
# INVESTIGATION HISTORY
# ============================================================

st.html(
    """
    <div class="section-title">
        Investigation History
    </div>

    <div class="section-sub">
        Questions evaluated by the Olympics benchmark
    </div>
    """
)


olympics_history_questions = [
    "Who won the gold medal in the event held at Olympic Aquatic Centre on August 14, 2004?",
    "Who won the gold medal in the men's 100m freestyle at the 2008 Summer Olympics?",
    "Which country won the most gold medals at the 2008 Summer Olympics?",
    "Who won the gold medal in the men's 400m individual medley at the 2004 Summer Olympics?",
    "Which athlete won the most medals at the 2008 Summer Olympics?",
    "Which event was held at Olympic Aquatic Centre on August 14, 2004?",
    "Who won the gold medal in the men's 470 sailing event at the 2016 Summer Olympics?",
    "What was the previous Olympic Games before the 2008 Summer Olympics, and who won the gold medal in the specified event?",
]


for index, question_text in enumerate(
    olympics_history_questions,
    start=1,
):

    item = (
        benchmark_rows[index - 1]
        if index - 1 < len(benchmark_rows)
        else {}
    )

    correct_status = item.get(
        "correct",
        False,
    )


    confidence = item.get(
        "confidence",
        0,
    )


    tokens = item.get(
        "estimated_tokens",
        0,
    )


    status = (
        "✓ CORRECT"
        if correct_status
        else "✗ REVIEW"
    )


    status_color = (
        GREEN
        if correct_status
        else RED
    )


       

# ============================================================
# AGENTIC ARCHITECTURE
# ============================================================

st.html(
    f"""
    <div class="section-title">
        EVIDENCE GRAPH — OLYMPICS SYSTEM ARCHITECTURE
    </div>

    <div class="section-sub">
        A three-way retrieval architecture comparing RAG, GraphRAG, and Agentic GraphRAG on Olympic benchmark questions.
    </div>

    <div class="info-card">

        <div style="text-align:center; padding:24px 8px;">

            <div style="margin-bottom:10px;">
                <span class="node">User Question</span>
                <span class="arrow">→</span>
                <span class="node">Entity Linking</span>
                <span class="arrow">→</span>
                <span class="node">Agent State / Memory</span>
            </div>

            <div style="margin:4px 0 10px; color:{DIM}; font-size:12px;">
                ↓
            </div>

            <div style="margin-bottom:10px;">
                <span class="node node-main">Adaptive Orchestrator</span>
            </div>

            <div style="
                color:{MUTED};
                font-size:10px;
                line-height:1.6;
                max-width:850px;
                margin:0 auto 14px;
            ">
                Chooses the next action from the original question,
                required information, evidence already collected,
                missing information and previous actions.
            </div>

            <div style="
                display:flex;
                justify-content:center;
                align-items:center;
                flex-wrap:wrap;
                gap:8px;
                margin-bottom:12px;
            ">
                <span class="node node-main">TigerGraph Multi-hop Search</span>
                <span class="node node-main">Vector / Document Search</span>
            </div>

            <div style="margin:4px 0 10px; color:{DIM}; font-size:12px;">
                ↓
            </div>

            <div style="margin-bottom:10px;">
                <span class="node">Evidence Evaluation</span>
                <span class="arrow">→</span>
                <span class="node node-main">Enough Evidence?</span>
            </div>

            <div style="
                display:flex;
                justify-content:center;
                align-items:flex-start;
                flex-wrap:wrap;
                gap:18px;
                margin-top:12px;
            ">
                <div style="
                    min-width:190px;
                    padding:12px;
                    border-radius:10px;
                    border:1px solid rgba(245,158,11,0.28);
                    background:rgba(245,158,11,0.05);
                    color:{MUTED};
                    font-size:10px;
                    line-height:1.5;
                ">
                    <b style="color:{ORANGE};">NO</b><br>
                    Return to the orchestrator for another investigation action.
                </div>

                <div style="
                    min-width:190px;
                    padding:12px;
                    border-radius:10px;
                    border:1px solid rgba(45,212,191,0.28);
                    background:rgba(45,212,191,0.05);
                    color:{MUTED};
                    font-size:10px;
                    line-height:1.5;
                ">
                    <b style="color:{TEAL};">YES</b><br>
                    Stop investigation and generate the evidence-backed final answer.
                </div>
            </div>

            <div style="
                margin-top:18px;
                color:{DIM};
                font-size:9px;
                line-height:1.5;
            ">
                Current implementation: Python state + rule-based adaptive routing,
                TigerGraph traversal, semantic vector retrieval and evidence evaluation.
            </div>

        </div>
    </div>
    """
)


# ============================================================
# FOOTER
# ============================================================

st.html(
    f"""
    <div class="footer">

        <b style="color:{CYAN};">
            EVIDENCE GRAPH
        </b>

        <br>

        Agentic GraphRAG — Olympics Benchmark

        <br><br>

        Three-Way Retrieval & Reasoning Benchmark

    </div>
    """
)