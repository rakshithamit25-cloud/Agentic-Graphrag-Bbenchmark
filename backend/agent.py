"""
Live Olympic investigation backend.

Reuses the official three-way benchmark retrieval (TigerGraph, vector RAG,
and Groq) without fabricating answers or benchmark metrics.

Live-query path bypasses the batch-benchmark's mandatory time.sleep(10)
throttle to give fast dashboard responses.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

BENCHMARK_PATH = (
    PROJECT_ROOT / "benchmark" / "run_official_three_way_benchmark.py"
)
CORPUS_FILE = PROJECT_ROOT / "official_data" / "corpus.jsonl"

INSUFFICIENT_MESSAGE = (
    "Investigation could not be completed with the available evidence sources."
)
NOT_AVAILABLE = "Not available"

_benchmark = None
_corpus_by_id = None


def _load_benchmark_module():
    global _benchmark
    if _benchmark is not None:
        return _benchmark

    spec = importlib.util.spec_from_file_location(
        "official_three_way_benchmark",
        BENCHMARK_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _benchmark = module
    return _benchmark


def _load_corpus_by_id():
    global _corpus_by_id
    if _corpus_by_id is not None:
        return _corpus_by_id

    bench = _load_benchmark_module()
    corpus = bench.load_jsonl(CORPUS_FILE)
    _corpus_by_id = {doc["doc_id"]: doc for doc in corpus}
    return _corpus_by_id


# ============================================================
# QUESTION CLASSIFIER
# ============================================================

def classify_question(question: str) -> str:
    """
    Map a live question onto benchmark query types.

    Types: aggregation | temporal | superlative | multi_hop | lookup | event_winner
    """
    q = (question or "").lower()

    # Aggregation: "how many X events had more than N competitors"
    if re.search(
        r"(more than|greater than|above)\s+\d+\s+(competitors|participants)",
        q,
    ):
        return "aggregation"

    # Superlative: highest/most competitors
    if "highest number of competitors" in q or "most competitors" in q:
        return "superlative"

    # Temporal: "held immediately before <year>"
    if "immediately before" in q:
        return "temporal"

    # Multi-hop: event at a specific venue on a specific date
    if re.search(r"event held at\s+.+\son\s+", q) or (
        "held at" in q and re.search(r"\bon\s+", q)
    ):
        return "multi_hop"

    # Lookup: "how many nations competed in X"
    if "how many nations" in q:
        return "lookup"

    # Winner questions
    if "who won" in q:
        # Try to detect if it can be answered via the temporal graph path:
        # "who won ... immediately before <year>" already caught above.
        # For direct "who won ... at the <year> Olympics" questions,
        # we first attempt TigerGraph lookup, then fall back to vector RAG.
        return "event_winner"

    return "lookup"


# ============================================================
# LIVE RAG — bypasses the 10s batch sleep in bench.rag_answer()
# ============================================================

def _live_rag_answer(question: str, corpus_by_id: dict, qtype: str) -> dict:
    """
    Perform vector search + Groq answer generation for a live query.

    Identical logic to benchmark rag_answer() but without time.sleep(10).
    """
    from official_vector_search import official_vector_search
    from groq_client import groq_generate_with_metadata, GROQ_MODEL

    bench = _load_benchmark_module()

    # Use the same adaptive retrieval settings as the benchmark
    settings = bench.get_rag_retrieval_settings(question, qtype or "lookup")
    top_k = settings["initial_top_k"]
    max_chars = settings["max_chars_per_doc"]

    retrieved = official_vector_search(question, top_k=top_k)

    retrieved_docs = []
    for item in retrieved:
        doc_id = item.get("doc_id")
        doc = corpus_by_id.get(doc_id)
        if doc:
            retrieved_docs.append({
                "doc_id": doc_id,
                "score": item.get("score"),
                "title": doc.get("title", ""),
                "text": doc.get("text", ""),
                "approx_tokens": doc.get("approx_tokens", 0),
            })

    if not retrieved_docs:
        return {
            "answer": [],
            "documents": [],
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
            "error": "No documents retrieved from vector index.",
        }

    # Apply the same filtering logic as the benchmark
    if settings.get("apply_entity_filter"):
        selected_docs = bench.filter_rag_candidates(
            question,
            retrieved_docs,
            max_docs=settings.get("max_filtered_docs", 25),
        )
    else:
        selected_docs = retrieved_docs[:top_k]

    # Build evidence context using the same extraction logic
    evidence_blocks = []
    for i, doc in enumerate(selected_docs, start=1):
        title = doc.get("title", "").strip()
        text = (doc.get("text", "") or "").strip()
        snippet = bench.extract_relevant_rag_fields(title, text, max_chars=max_chars)
        evidence_blocks.append(f"[Document {i}] {title}\n{snippet}")

    evidence_text = "\n\n".join(evidence_blocks)

    prompt = (
        "You are an answer extractor for an Olympic-history question-answering benchmark.\n"
        "\n"
        "STRICT RULES:\n"
        "- Answer ONLY using the supplied retrieved documents below.\n"
        "- Do NOT use prior knowledge or outside information of any kind.\n"
        "- If the documents do not contain enough information to answer, "
        "reply with exactly: INSUFFICIENT_EVIDENCE\n"
        "\n"
        "OUTPUT FORMAT:\n"
        "- Reply with the answer value only — no explanation, no preamble, no JSON.\n"
        "- For a person or event name: write only the name (e.g. Michael Phelps).\n"
        "- For a number: write only the digit(s) (e.g. 5).\n"
        "- For an event title: write only the full event title.\n"
        "- Do not add country names, parentheses, or extra context.\n"
        "\n"
        f"QUESTION: {question}\n"
        "\n"
        "RETRIEVED DOCUMENTS:\n"
        f"{evidence_text}\n"
        "\n"
        "ANSWER:"
    )

    llm_tokens = 0
    llm_latency = 0.0
    llm_model = GROQ_MODEL

    try:
        res = groq_generate_with_metadata(
            prompt,
            max_retries=3,
            initial_backoff=1.0,
        )
        llm_tokens = res.get("total_tokens", 0)
        llm_latency = res.get("latency", 0.0)
        llm_model = res.get("model", GROQ_MODEL)
        raw = res.get("content", "").strip()
    except Exception as exc:
        return {
            "answer": [],
            "documents": retrieved_docs,
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
            "error": str(exc),
        }

    if not raw or raw.upper() == "INSUFFICIENT_EVIDENCE":
        return {
            "answer": [],
            "documents": retrieved_docs,
            "llm_tokens": llm_tokens,
            "llm_latency": llm_latency,
            "llm_model": llm_model,
        }

    answer_text = raw.strip().strip('"').strip("'").strip()
    return {
        "answer": [answer_text],
        "documents": retrieved_docs,
        "llm_tokens": llm_tokens,
        "llm_latency": llm_latency,
        "llm_model": llm_model,
    }


# ============================================================
# HELPERS
# ============================================================

def _format_answer(answers) -> str | None:
    if answers is None:
        return None
    if isinstance(answers, str):
        text = answers.strip()
        return text or None
    if isinstance(answers, list):
        parts = [str(item).strip() for item in answers if str(item).strip()]
        if not parts:
            return None
        return ", ".join(parts)
    text = str(answers).strip()
    return text or None


def _present(value):
    if value is None:
        return NOT_AVAILABLE
    if isinstance(value, str) and not value.strip():
        return NOT_AVAILABLE
    if isinstance(value, (int, float)) and value == 0:
        return NOT_AVAILABLE
    return value


def _evidence_items(evidence) -> list:
    if not evidence:
        return []
    if isinstance(evidence, list):
        return evidence
    return [evidence]


def _empty_result(question: str, **overrides) -> dict:
    result = {
        "question": question,
        "final_answer": INSUFFICIENT_MESSAGE,
        "status": "failed",
        "question_type": NOT_AVAILABLE,
        "graph_supported": False,
        "actions_taken": [],
        "evidence_items": 0,
        "evidence": [],
        "evidence_agrees": NOT_AVAILABLE,
        "confidence": NOT_AVAILABLE,
        "estimated_tokens": NOT_AVAILABLE,
        "llm_tokens": NOT_AVAILABLE,
        "llm_latency": NOT_AVAILABLE,
        "llm_model": NOT_AVAILABLE,
        "response_time": NOT_AVAILABLE,
        "graph_result": None,
        "vector_result": None,
        "errors": [],
        "route_used": NOT_AVAILABLE,
        "graph_query": NOT_AVAILABLE,
    }
    result.update(overrides)
    return result


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def run_agent(question: str) -> dict:
    """
    Run one live investigation using official Olympic retrieval.

    Pipeline:
      UNDERSTAND → GRAPH (TigerGraph) → [VECTOR_SEARCH if graph empty] → EVALUATE → STOP

    Returns a structured dict for the dashboard. Does not invent answers
    or confidence scores.
    """
    question = (question or "").strip()
    started = time.time()

    if not question:
        return _empty_result(
            question,
            final_answer="Please enter a question.",
            status="error",
            errors=["Empty question"],
        )

    # ── 1. UNDERSTAND ──────────────────────────────────────────
    qtype = classify_question(question)
    actions = ["UNDERSTAND"]
    errors = []
    graph_result = None
    vector_result = None
    graph_answer = []
    final_answers = []
    evidence = []
    route_used = NOT_AVAILABLE
    graph_supported = False
    llm_tokens = None
    llm_latency = None
    llm_model = None
    estimated_tokens = None

    bench = _load_benchmark_module()
    corpus_by_id = _load_corpus_by_id()

    # ── 2. GRAPH ───────────────────────────────────────────────
    actions.append("GRAPH")

    conn = None
    try:
        conn = bench.get_connection()
    except Exception as exc:
        errors.append(f"TigerGraph unavailable: {exc}")

    # Determine which graph query type to attempt.
    # event_winner questions are not natively supported by any graph query,
    # but we attempt a lookup pass (event_nations) first — it may return
    # an empty result, which is fine; vector RAG will take over.
    graph_qtype = qtype
    if qtype == "event_winner":
        # Sailing / specific event winner: try lookup graph query first.
        # The lookup query (event_nations) searches by event title.
        # If TigerGraph has no matching record (winner questions have no
        # graph query), it returns an empty answer and we fall to vector.
        graph_qtype = "lookup"

    if conn is not None:
        try:
            graph_result = bench.run_graph_query(conn, graph_qtype, question)
            graph_answer = (graph_result or {}).get("answer") or []
        except Exception as exc:
            errors.append(f"TigerGraph query failed: {exc}")
            graph_result = {"answer": [], "results": [], "error": str(exc)}
    else:
        graph_result = {
            "answer": [],
            "results": [],
            "error": errors[-1] if errors else "TigerGraph unavailable",
        }

    # If TigerGraph returned an answer, synthesize it with the LLM
    if graph_answer:
        graph_supported = True
        route_used = "GRAPH"
        final_answers = graph_answer
        evidence = (graph_result or {}).get("results") or []
        try:
            synthesized, llm_meta = bench.synthesize_graph_answer(
                question,
                graph_result,
                pipeline_name="LiveAgent",
            )
            if synthesized:
                final_answers = synthesized
            llm_tokens = llm_meta.get("llm_tokens")
            llm_latency = llm_meta.get("llm_latency")
            llm_model = llm_meta.get("llm_model")
        except Exception as exc:
            errors.append(f"Graph answer synthesis failed: {exc}")

    else:
        # ── 3. VECTOR SEARCH ───────────────────────────────────
        actions.append("VECTOR_SEARCH")

        # For event_winner questions (e.g. "Who won the men's 100m at 2016 Olympics?"),
        # use lookup qtype for the RAG settings (conservative top_k, good for factoid).
        rag_qtype = qtype if qtype in {
            "aggregation", "temporal", "superlative", "multi_hop", "lookup",
        } else "lookup"

        try:
            # Use the live RAG path (no 10-second sleep) for fast dashboard response
            vector_result = _live_rag_answer(question, corpus_by_id, rag_qtype)
            final_answers = (vector_result or {}).get("answer") or []
            evidence = (vector_result or {}).get("documents") or []
            llm_tokens = (vector_result or {}).get("llm_tokens")
            llm_latency = (vector_result or {}).get("llm_latency")
            llm_model = (vector_result or {}).get("llm_model")

            try:
                estimated_tokens = bench.estimate_tokens_from_docs(evidence)
            except Exception:
                estimated_tokens = None

            if final_answers:
                route_used = "VECTOR"
            else:
                vector_error = (vector_result or {}).get("error")
                if vector_error:
                    errors.append(str(vector_error))
        except Exception as exc:
            errors.append(f"Vector retrieval failed: {exc}")
            vector_result = {"answer": [], "documents": [], "error": str(exc)}

    # ── 4. EVALUATE EVIDENCE ──────────────────────────────────
    actions.append("EVALUATE_EVIDENCE")
    actions.append("STOP")

    evidence_list = _evidence_items(evidence)
    final_answer = _format_answer(final_answers)

    if graph_supported and final_answer:
        status = "completed"
        evidence_agrees = True
    elif final_answer:
        status = "completed"
        evidence_agrees = NOT_AVAILABLE
    else:
        status = "failed"
        final_answer = INSUFFICIENT_MESSAGE
        evidence_agrees = False
        if not errors:
            errors.append(INSUFFICIENT_MESSAGE)

    elapsed = round(time.time() - started, 3)

    return {
        "question": question,
        "final_answer": final_answer,
        "status": status,
        "question_type": qtype,
        "graph_supported": graph_supported,
        "actions_taken": actions,
        "evidence_items": len(evidence_list),
        "evidence": evidence_list,
        "evidence_agrees": evidence_agrees,
        "confidence": NOT_AVAILABLE,
        "estimated_tokens": _present(estimated_tokens),
        "llm_tokens": _present(llm_tokens),
        "llm_latency": _present(llm_latency),
        "llm_model": _present(llm_model),
        "response_time": elapsed,
        "graph_result": graph_result,
        "vector_result": vector_result,
        "errors": errors,
        "route_used": route_used,
        "graph_query": (graph_result or {}).get("query") or NOT_AVAILABLE,
    }


if __name__ == "__main__":
    questions = [
        "Who won the men's 100m at the 2016 Olympics?",
        "Who won the men's 470 sailing event at the 2016 Summer Olympics?",
    ]
    for demo in questions:
        print(f"\n{'='*60}")
        result = run_agent(demo)
        print("Question:", result["question"])
        print("Status:  ", result["status"])
        print("Type:    ", result["question_type"])
        print("Route:   ", result["route_used"])
        print("Answer:  ", result["final_answer"])
        print("Time:    ", result["response_time"], "s")
        if result["errors"]:
            print("Errors:  ", result["errors"])
