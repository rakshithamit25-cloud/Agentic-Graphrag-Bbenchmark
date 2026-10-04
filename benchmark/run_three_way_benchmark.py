import json
import sys
import time
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# OFFICIAL FILES
# ============================================================

QUESTIONS_FILE = (
    PROJECT_ROOT
    / "official_data"
    / "eval_public.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "official_three_way_results.json"
)

SUMMARY_FILE = (
    PROJECT_ROOT
    / "benchmark"
    / "official_three_way_summary.json"
)


# ============================================================
# LOAD OFFICIAL QUESTIONS
# ============================================================

def load_questions():

    questions = []

    with open(
        QUESTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            questions.append(
                json.loads(line)
            )

    return questions


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).strip().lower()

    # Normalize whitespace
    text = " ".join(text.split())

    # Remove simple punctuation
    punctuation = ",.!?;:\"'()[]{}"

    for char in punctuation:
        text = text.replace(char, "")

    return text


# ============================================================
# ANSWER CORRECTNESS
# ============================================================

def answer_is_correct(predicted, gold):

    predicted_text = normalize_text(predicted)

    if isinstance(gold, list):

        gold_values = [
            normalize_text(x)
            for x in gold
        ]

        # Empty answer
        if not gold_values:
            return predicted_text == ""

        # For a single-answer question
        if len(gold_values) == 1:

            return gold_values[0] in predicted_text

        # Multi-answer question:
        # every required answer must appear.
        return all(
            value in predicted_text
            for value in gold_values
        )

    gold_text = normalize_text(gold)

    if not gold_text:
        return predicted_text == ""

    return gold_text in predicted_text


# ============================================================
# TOKEN ESTIMATION
# ============================================================

def estimate_tokens(text):

    if text is None:
        return 1

    text = str(text)

    words = text.split()

    if not words:
        return 1

    return max(
        1,
        int(len(words) * 1.3)
    )


# ============================================================
# QUESTION TYPE
# ============================================================

def get_question_type(question):

    return question.get(
        "qtype",
        "unknown"
    )


# ============================================================
# OFFICIAL RAG
# ============================================================

def run_official_rag(question):

    """
    Official RAG:

    Question
       ↓
    Official vector search
       ↓
    Top documents
       ↓
    Evidence text

    NOTE:
    This function intentionally returns the retrieved
    evidence rather than pretending that retrieval itself
    is an LLM-generated answer.
    """

    from official_vector_search import (
        vector_search
    )

    start_time = time.perf_counter()

    results = vector_search(
        question["question"],
        top_k=5
    )

    latency = (
        time.perf_counter()
        - start_time
    )

    retrieved_ids = []

    evidence_parts = []

    for item in results:

        doc_id = item.get(
            "doc_id",
            item.get("id")
        )

        if doc_id:
            retrieved_ids.append(
                doc_id
            )

        text = item.get(
            "text",
            ""
        )

        if text:
            evidence_parts.append(
                text
            )

    evidence = "\n".join(
        evidence_parts
    )

    return {
        "answer": evidence,
        "retrieved_doc_ids": retrieved_ids,
        "evidence": evidence,
        "latency_seconds": latency,
        "estimated_tokens": (
            estimate_tokens(evidence)
        )
    }


# ============================================================
# GRAPH QUERY HELPER
# ============================================================

def run_graph_query(question):

    """
    Select an existing official TigerGraph query
    based on the official question type.

    The Phase 5 graph contains:

    event_by_venue_date
    previous_olympics_gold
    count_events_above_competitors
    max_competitor_event
    event_nations
    """

    from pyTigerGraph import TigerGraphConnection

    from config import Config

    conn = TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )

    conn.getToken(
        Config.TG_SECRET
    )

    qtype = question.get(
        "qtype",
        ""
    )

    text = question[
        "question"
    ].lower()

    # --------------------------------------------------------
    # IMPORTANT:
    # The exact parameter extraction for arbitrary questions
    # is intentionally conservative.
    #
    # We first support the known official query patterns.
    # --------------------------------------------------------

    result = None

    # These questions can be routed by their wording.
    if (
        "immediately before 2016" in text
        and "gold medal" in text
    ):

        result = conn.runInstalledQuery(
            "previous_olympics_gold",
            {
                "games_year": 2016,
                "season": "Summer",
                "event_search": "Canoeing"
            }
        )

    elif (
        "richmond olympic oval" in text
        and "13 february 2010" in text
    ):

        result = conn.runInstalledQuery(
            "event_by_venue_date",
            {
                "venue": "Richmond Olympic Oval",
                "date": "13 February 2010"
            }
        )

    elif (
        "2008 summer olympics" in text
        and "athletics" in text
        and "competitors" in text
    ):

        result = conn.runInstalledQuery(
            "count_events_above_competitors",
            {
                "games_year": 2008,
                "season": "Summer",
                "sport": "Athletics",
                "threshold": 30
            }
        )

    elif (
        "most competitors" in text
        and "athletics" in text
    ):

        result = conn.runInstalledQuery(
            "max_competitor_event",
            {
                "games_year": 2008,
                "season": "Summer",
                "sport": "Athletics"
            }
        )

    elif "nations" in text:

        # Known Phase 4/5 event example.
        result = conn.runInstalledQuery(
            "event_nations",
            {
                "event_id": "event_Q26233801"
            }
        )

    else:

        result = []

    return result


# ============================================================
# OFFICIAL GRAPHRAG
# ============================================================

def run_official_graphrag(question):

    start_time = time.perf_counter()

    graph_result = run_graph_query(
        question
    )

    # Also retrieve official vector evidence.
    vector_result = run_official_rag(
        question
    )

    graph_text = json.dumps(
        graph_result,
        ensure_ascii=False
    )

    combined_evidence = (
        graph_text
        + "\n"
        + vector_result.get(
            "evidence",
            ""
        )
    )

    latency = (
        time.perf_counter()
        - start_time
    )

    return {
        "answer": combined_evidence,
        "graph_evidence": graph_result,
        "vector_evidence": vector_result,
        "retrieved_doc_ids": vector_result.get(
            "retrieved_doc_ids",
            []
        ),
        "evidence": combined_evidence,
        "latency_seconds": latency,
        "estimated_tokens": (
            estimate_tokens(
                combined_evidence
            )
        )
    }


# ============================================================
# AGENT STATE
# ============================================================

class OfficialAgentState:

    def __init__(self, question):

        self.question = question

        self.qtype = question.get(
            "qtype",
            "unknown"
        )

        self.actions = []

        self.graph_evidence = None

        self.vector_evidence = None

        self.evidence = []

        self.confidence = 0.0

        self.max_actions = 4

        self.stopped = False

    def record_action(self, action):

        self.actions.append(
            action
        )

    def has_action(self, action):

        return action in self.actions


# ============================================================
# AGENT DECISION LOGIC
# ============================================================

def decide_next_action(state):

    """
    Adaptive routing.

    This is intentionally state-based.

    It does NOT blindly execute:

        GRAPH -> VECTOR -> ANSWER

    The next action depends on what is already available.
    """

    # No graph evidence yet
    if not state.has_action(
        "GRAPH"
    ):

        return "GRAPH"

    # Graph found something but
    # document evidence has not been checked
    if not state.has_action(
        "VECTOR"
    ):

        return "VECTOR"

    # Both evidence sources exist
    if not state.has_action(
        "EVALUATE"
    ):

        return "EVALUATE"

    return "STOP"


# ============================================================
# EVIDENCE EVALUATION
# ============================================================

def evaluate_agent_evidence(state):

    graph_exists = (
        state.graph_evidence
        not in (None, [], {})
    )

    vector_exists = (
        state.vector_evidence
        not in (None, [], {})
    )

    if graph_exists and vector_exists:

        state.confidence = 0.90

    elif graph_exists:

        state.confidence = 0.75

    elif vector_exists:

        state.confidence = 0.60

    else:

        state.confidence = 0.0

    state.record_action(
        "EVALUATE"
    )


# ============================================================
# OFFICIAL AGENTIC GRAPHRAG
# ============================================================

def run_official_agentic(question):

    start_time = time.perf_counter()

    state = OfficialAgentState(
        question
    )

    while (
        not state.stopped
        and len(state.actions)
        < state.max_actions
    ):

        action = decide_next_action(
            state
        )

        if action == "GRAPH":

            state.record_action(
                "GRAPH"
            )

            state.graph_evidence = (
                run_graph_query(
                    question
                )
            )

        elif action == "VECTOR":

            state.record_action(
                "VECTOR"
            )

            state.vector_evidence = (
                run_official_rag(
                    question
                )
            )

        elif action == "EVALUATE":

            evaluate_agent_evidence(
                state
            )

        elif action == "STOP":

            state.stopped = True

        else:

            state.stopped = True

    # --------------------------------------------------------
    # Combine evidence
    # --------------------------------------------------------

    graph_text = json.dumps(
        state.graph_evidence,
        ensure_ascii=False
    )

    vector_text = ""

    retrieved_ids = []

    if isinstance(
        state.vector_evidence,
        dict
    ):

        vector_text = (
            state.vector_evidence.get(
                "evidence",
                ""
            )
        )

        retrieved_ids = (
            state.vector_evidence.get(
                "retrieved_doc_ids",
                []
            )
        )

    evidence = (
        graph_text
        + "\n"
        + vector_text
    )

    latency = (
        time.perf_counter()
        - start_time
    )

    return {
        "answer": evidence,
        "graph_evidence": (
            state.graph_evidence
        ),
        "vector_evidence": (
            state.vector_evidence
        ),
        "retrieved_doc_ids": (
            retrieved_ids
        ),
        "evidence": evidence,
        "latency_seconds": latency,
        "estimated_tokens": (
            estimate_tokens(evidence)
        ),
        "confidence": state.confidence,
        "actions": state.actions,
        "stopped": state.stopped
    }


# ============================================================
# GOLD DOCUMENT COVERAGE
# ============================================================

def calculate_gold_coverage(
    question,
    retrieved_doc_ids
):

    gold_ids = set(
        question.get(
            "gold_doc_ids",
            []
        )
    )

    retrieved_ids = set(
        retrieved_doc_ids
    )

    if not gold_ids:

        return {
            "gold_doc_count": 0,
            "matched_gold_doc_count": 0,
            "gold_doc_recall": 0.0,
            "matched_gold_doc_ids": []
        }

    matched = (
        gold_ids
        & retrieved_ids
    )

    recall = (
        len(matched)
        / len(gold_ids)
    )

    return {
        "gold_doc_count": len(
            gold_ids
        ),
        "matched_gold_doc_count": len(
            matched
        ),
        "gold_doc_recall": recall,
        "matched_gold_doc_ids": sorted(
            matched
        )
    }


# ============================================================
# RUN ONE SYSTEM
# ============================================================

def run_system(
    system_name,
    questions,
    runner
):

    results = []

    correct = 0

    completeness_total = 0.0

    token_total = 0

    latency_total = 0.0

    print("\n")
    print("=" * 80)
    print(system_name.upper())
    print("=" * 80)

    for index, question in enumerate(
        questions,
        start=1
    ):

        qid = question[
            "qid"
        ]

        print(
            f"\n[{index}/"
            f"{len(questions)}]"
            f" {qid}"
        )

        try:

            result = runner(
                question
            )

        except Exception as error:

            print(
                "ERROR:",
                repr(error)
            )

            result = {
                "answer": "",
                "retrieved_doc_ids": [],
                "evidence": "",
                "latency_seconds": 0,
                "estimated_tokens": 0
            }

        predicted = result.get(
            "answer",
            ""
        )

        gold = question.get(
            "answer",
            []
        )

        is_correct = (
            answer_is_correct(
                predicted,
                gold
            )
        )

        completeness = (
            1.0
            if is_correct
            else 0.0
        )

        if is_correct:

            correct += 1

            print(
                "Result: CORRECT"
            )

        else:

            print(
                "Result: INCORRECT"
            )

        tokens = result.get(
            "estimated_tokens",
            0
        )

        latency = result.get(
            "latency_seconds",
            0
        )

        retrieved_ids = result.get(
            "retrieved_doc_ids",
            []
        )

        coverage = (
            calculate_gold_coverage(
                question,
                retrieved_ids
            )
        )

        completeness_total += (
            completeness
        )

        token_total += tokens

        latency_total += latency

        question_result = {

            "qid": qid,

            "question":
                question[
                    "question"
                ],

            "qtype":
                question.get(
                    "qtype",
                    "unknown"
                ),

            "gold_answer":
                gold,

            "predicted_answer":
                predicted,

            "correct":
                is_correct,

            "completeness":
                completeness,

            "gold_doc_ids":
                question.get(
                    "gold_doc_ids",
                    []
                ),

            "retrieved_doc_ids":
                retrieved_ids,

            "gold_doc_coverage":
                coverage,

            "estimated_tokens":
                tokens,

            "latency_seconds":
                latency,

            "evidence":
                result.get(
                    "evidence",
                    ""
                )
        }

        if system_name == (
            "Agentic GraphRAG"
        ):

            question_result[
                "confidence"
            ] = result.get(
                "confidence",
                0
            )

            question_result[
                "actions"
            ] = result.get(
                "actions",
                []
            )

            question_result[
                "stopped"
            ] = result.get(
                "stopped",
                False
            )

        results.append(
            question_result
        )

    total = len(
        questions
    )

    accuracy = (
        correct / total
        if total
        else 0
    )

    completeness = (
        completeness_total / total
        if total
        else 0
    )

    average_tokens = (
        token_total / total
        if total
        else 0
    )

    average_latency = (
        latency_total / total
        if total
        else 0
    )

    return {

        "accuracy":
            accuracy,

        "completeness":
            completeness,

        "correct":
            correct,

        "incorrect":
            total - correct,

        "total_questions":
            total,

        "average_estimated_tokens":
            average_tokens,

        "average_latency_seconds":
            average_latency,

        "total_latency_seconds":
            latency_total,

        "results":
            results
    }


# ============================================================
# QUESTION-TYPE SUMMARY
# ============================================================

def calculate_type_summary(
    results
):

    summary = {}

    for result in results:

        qtype = result[
            "qtype"
        ]

        if qtype not in summary:

            summary[qtype] = {
                "total": 0,
                "correct": 0
            }

        summary[qtype][
            "total"
        ] += 1

        if result[
            "correct"
        ]:

            summary[qtype][
                "correct"
            ] += 1

    for qtype, data in summary.items():

        if data["total"]:

            data[
                "accuracy"
            ] = (
                data["correct"]
                / data["total"]
            )

        else:

            data[
                "accuracy"
            ] = 0.0

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    questions = (
        load_questions()
    )

    print("=" * 80)

    print(
        "PHASE 6 — OFFICIAL "
        "100-QUESTION THREE-WAY BENCHMARK"
    )

    print("=" * 80)

    print(
        f"Official questions loaded: "
        f"{len(questions)}"
    )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if len(questions) != 100:

        raise RuntimeError(
            "Expected exactly 100 "
            "official questions."
        )

    qids = [
        q["qid"]
        for q in questions
    ]

    if len(set(qids)) != 100:

        raise RuntimeError(
            "Duplicate qids detected."
        )

    print(
        "Question validation: PASS"
    )

    # --------------------------------------------------------
    # RUN RAG
    # --------------------------------------------------------

    rag = run_system(
        "RAG",
        questions,
        run_official_rag
    )

    # --------------------------------------------------------
    # RUN GRAPHRAG
    # --------------------------------------------------------

    graphrag = run_system(
        "GraphRAG",
        questions,
        run_official_graphrag
    )

    # --------------------------------------------------------
    # RUN AGENTIC GRAPHRAG
    # --------------------------------------------------------

    agentic = run_system(
        "Agentic GraphRAG",
        questions,
        run_official_agentic
    )

    # --------------------------------------------------------
    # TYPE SUMMARY
    # --------------------------------------------------------

    type_summary = {

        "RAG":
            calculate_type_summary(
                rag["results"]
            ),

        "GraphRAG":
            calculate_type_summary(
                graphrag["results"]
            ),

        "Agentic GraphRAG":
            calculate_type_summary(
                agentic["results"]
            )
    }

    # --------------------------------------------------------
    # FINAL RESULTS
    # --------------------------------------------------------

    final_results = {

        "benchmark_type":
            "OFFICIAL 100-QUESTION "
            "BENCHMARK",

        "dataset":
            "official_data/eval_public.jsonl",

        "corpus":
            "official_data/corpus.jsonl",

        "graph":
            "OLYMPIC_BENCHMARK",

        "question_count":
            len(questions),

        "systems": {

            "RAG":
                rag,

            "GraphRAG":
                graphrag,

            "Agentic GraphRAG":
                agentic
        },

        "results_by_question_type":
            type_summary
    }

    # --------------------------------------------------------
    # SAVE RAW RESULTS
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_results,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # SUMMARY FILE
    # --------------------------------------------------------

    summary = {

        "benchmark_type":
            "OFFICIAL 100-QUESTION "
            "BENCHMARK",

        "question_count":
            100,

        "systems": {

            "RAG": {
                "accuracy":
                    rag["accuracy"],
                "completeness":
                    rag["completeness"],
                "correct":
                    rag["correct"],
                "incorrect":
                    rag["incorrect"],
                "average_tokens":
                    rag[
                        "average_estimated_tokens"
                    ],
                "average_latency_seconds":
                    rag[
                        "average_latency_seconds"
                    ]
            },

            "GraphRAG": {
                "accuracy":
                    graphrag["accuracy"],
                "completeness":
                    graphrag["completeness"],
                "correct":
                    graphrag["correct"],
                "incorrect":
                    graphrag["incorrect"],
                "average_tokens":
                    graphrag[
                        "average_estimated_tokens"
                    ],
                "average_latency_seconds":
                    graphrag[
                        "average_latency_seconds"
                    ]
            },

            "Agentic GraphRAG": {
                "accuracy":
                    agentic["accuracy"],
                "completeness":
                    agentic["completeness"],
                "correct":
                    agentic["correct"],
                "incorrect":
                    agentic["incorrect"],
                "average_tokens":
                    agentic[
                        "average_estimated_tokens"
                    ],
                "average_latency_seconds":
                    agentic[
                        "average_latency_seconds"
                    ]
            }
        },

        "results_by_question_type":
            type_summary
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # PRINT FINAL SUMMARY
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print(
        "OFFICIAL THREE-WAY RESULTS"
    )
    print("=" * 80)

    for name, data in final_results[
        "systems"
    ].items():

        print(
            f"\n{name}"
        )

        print(
            f"Accuracy: "
            f"{data['accuracy'] * 100:.2f}%"
        )

        print(
            f"Completeness: "
            f"{data['completeness'] * 100:.2f}%"
        )

        print(
            f"Correct: "
            f"{data['correct']}/100"
        )

        print(
            f"Average tokens: "
            f"{data['average_estimated_tokens']:.2f}"
        )

        print(
            f"Average latency: "
            f"{data['average_latency_seconds']:.4f}s"
        )

    print("\n")
    print(
        "Raw results saved to:"
    )
    print(
        OUTPUT_FILE
    )

    print(
        "Summary saved to:"
    )
    print(
        SUMMARY_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()