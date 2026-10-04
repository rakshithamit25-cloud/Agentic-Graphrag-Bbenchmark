import json
import os
import sys
import time
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# PROJECT ROOT & PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "benchmark"))

from benchmark.run_official_three_way_benchmark import (
    load_jsonl,
    get_connection,
    rag_answer,
    run_graph_query,
    synthesize_graph_answer,
    agentic_answer,
    answers_match,
    estimate_tokens_from_docs,
    calculate_gold_coverage,
    GROQ_MODEL,
    CORPUS_FILE,
)

# ============================================================
# FILE PATHS
# ============================================================

EVAL_FILE = BASE_DIR / "official_data" / "eval_hidden.jsonl"
RESULT_FILE = BASE_DIR / "official_data" / "hidden_50_results.json"
REPORT_FILE = BASE_DIR / "official_data" / "HIDDEN_50_REPORT.md"


# ============================================================
# GENERATE MARKDOWN REPORT
# ============================================================

def generate_markdown_report(output_data):
    summary = output_data["summary"]
    total = output_data["total_questions"]
    results = output_data["results"]
    distribution = output_data["question_distribution"]
    has_gold = any(r.get("gold_answer") is not None for r in results)

    rag_sum = summary["rag"]
    graph_sum = summary["graphrag"]
    agentic_sum = summary["agentic_graphrag"]

    # Calculate type breakdown
    type_stats = {}
    for r in results:
        qt = r["qtype"]
        if qt not in type_stats:
            type_stats[qt] = {
                "total": 0,
                "rag_correct": 0,
                "graphrag_correct": 0,
                "agentic_correct": 0,
            }
        type_stats[qt]["total"] += 1
        if r["rag"]["correct"]:
            type_stats[qt]["rag_correct"] += 1
        if r["graphrag"]["correct"]:
            type_stats[qt]["graphrag_correct"] += 1
        if r["agentic_graphrag"]["correct"]:
            type_stats[qt]["agentic_correct"] += 1

    lines = []
    lines.append("# Official Hidden 50-Question Benchmark Report")
    lines.append("")
    lines.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Dataset:** `official_data/eval_hidden.jsonl` (Confirmed {total} questions)")
    lines.append(f"**LLM Model:** `{summary['llm_model']}`")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("| Pipeline | Correct | Total | Accuracy | Avg Latency (s) | Avg LLM Tokens |")
    lines.append("|---|---|---|---|---|---|")
    if has_gold:
        lines.append(f"| **Standard RAG** | {rag_sum['correct']} | {rag_sum['total']} | **{rag_sum['accuracy']:.1%}** | {rag_sum['avg_latency']:.2f}s | {rag_sum['avg_tokens']:.1f} |")
        lines.append(f"| **GraphRAG** | {graph_sum['correct']} | {graph_sum['total']} | **{graph_sum['accuracy']:.1%}** | {graph_sum['avg_latency']:.2f}s | {graph_sum['avg_tokens']:.1f} |")
        lines.append(f"| **Agentic GraphRAG** | {agentic_sum['correct']} | {agentic_sum['total']} | **{agentic_sum['accuracy']:.1%}** | {agentic_sum['avg_latency']:.2f}s | {agentic_sum['avg_tokens']:.1f} |")
    else:
        lines.append(f"| **Standard RAG** | N/A | {rag_sum['total']} | **N/A (Hidden Test)** | {rag_sum['avg_latency']:.2f}s | {rag_sum['avg_tokens']:.1f} |")
        lines.append(f"| **GraphRAG** | N/A | {graph_sum['total']} | **N/A (Hidden Test)** | {graph_sum['avg_latency']:.2f}s | {graph_sum['avg_tokens']:.1f} |")
        lines.append(f"| **Agentic GraphRAG** | N/A | {agentic_sum['total']} | **N/A (Hidden Test)** | {agentic_sum['avg_latency']:.2f}s | {agentic_sum['avg_tokens']:.1f} |")
    lines.append("")
    lines.append("## 2. Breakdown by Question Type")
    lines.append("")
    if has_gold:
        lines.append("| Question Type | Count | RAG Accuracy | GraphRAG Accuracy | Agentic GraphRAG Accuracy |")
        lines.append("|---|---|---|---|---|")
        for qt, st in sorted(type_stats.items()):
            cnt = st["total"]
            rag_pct = (st["rag_correct"] / cnt) * 100 if cnt else 0.0
            graph_pct = (st["graphrag_correct"] / cnt) * 100 if cnt else 0.0
            agentic_pct = (st["agentic_correct"] / cnt) * 100 if cnt else 0.0
            lines.append(f"| `{qt}` | {cnt} | {st['rag_correct']}/{cnt} ({rag_pct:.1f}%) | {st['graphrag_correct']}/{cnt} ({graph_pct:.1f}%) | {st['agentic_correct']}/{cnt} ({agentic_pct:.1f}%) |")
    else:
        lines.append("| Question Type | Count | Evaluated Status |")
        lines.append("|---|---|---|")
        for qt, st in sorted(type_stats.items()):
            cnt = st["total"]
            lines.append(f"| `{qt}` | {cnt} | Generated across all 3 pipelines |")
    lines.append("")
    lines.append("## 3. Question Distribution")
    lines.append("")
    for qt, count in sorted(distribution.items()):
        lines.append(f"- **{qt}**: {count} questions")
    lines.append("")
    lines.append("## 4. Detailed Per-Question Evaluation")
    lines.append("")
    if has_gold:
        lines.append("| QID | Type | Question | Ground Truth | RAG Prediction | RAG | GraphRAG Prediction | GraphRAG | Agentic Prediction | Agentic |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
    else:
        lines.append("| QID | Type | Question | Ground Truth | RAG Prediction | GraphRAG Prediction | Agentic Prediction |")
        lines.append("|---|---|---|---|---|---|---|")

    for r in results:
        qid = r["qid"]
        qtype = r["qtype"]
        q_text = r["question"].replace("|", "\\|")
        gold = "N/A (Hidden)" if r.get("gold_answer") is None else str(r["gold_answer"]).replace("|", "\\|")
        rag_ans = str(r["rag"]["answer"]).replace("|", "\\|")
        gr_ans = str(r["graphrag"]["answer"]).replace("|", "\\|")
        ag_ans = str(r["agentic_graphrag"]["answer"]).replace("|", "\\|")

        if has_gold:
            rag_stat = "PASS" if r["rag"]["correct"] else "FAIL"
            gr_stat = "PASS" if r["graphrag"]["correct"] else "FAIL"
            ag_stat = "PASS" if r["agentic_graphrag"]["correct"] else "FAIL"
            lines.append(f"| `{qid}` | `{qtype}` | {q_text} | `{gold}` | `{rag_ans}` | {rag_stat} | `{gr_ans}` | {gr_stat} | `{ag_ans}` | {ag_stat} |")
        else:
            lines.append(f"| `{qid}` | `{qtype}` | {q_text} | `{gold}` | `{rag_ans}` | `{gr_ans}` | `{ag_ans}` |")
    lines.append("")
    lines.append("## 5. Agentic Traces Summary")
    lines.append("")
    for r in results:
        actions = r["agentic_graphrag"].get("actions", [])
        if actions:
            lines.append(f"### Question `{r['qid']}` ({r['qtype']})")
            lines.append(f"> **Q:** {r['question']}")
            lines.append(f"> **Actions Taken:**")
            for act in actions:
                lines.append(f"> - {act}")
            lines.append(f"> **Final Agentic Answer:** {r['agentic_graphrag']['answer']}")
            lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN BENCHMARK EXECUTION
# ============================================================

def main():
    print("=" * 80)
    print("HIDDEN 50-QUESTION THREE-WAY BENCHMARK")
    print("Pipelines: Standard RAG | GraphRAG | Agentic GraphRAG")
    print(f"Model: {GROQ_MODEL}")
    print("=" * 80)

    # 1. Load hidden dataset
    if not EVAL_FILE.exists():
        print(f"ERROR: Hidden file not found at {EVAL_FILE}")
        sys.exit(1)

    questions = load_jsonl(EVAL_FILE)
    total_loaded = len(questions)
    print(f"Loaded questions from {EVAL_FILE.name}: {total_loaded}")

    # 2. Confirm exactly 50 questions
    if total_loaded != 50:
        print(f"WARNING: Expected exactly 50 questions, found {total_loaded}!")
    else:
        print("CONFIRMED: Exactly 50 hidden questions loaded.")

    # Load corpus for RAG & Agentic fallback
    corpus = load_jsonl(CORPUS_FILE)
    corpus_by_id = {doc["doc_id"]: doc for doc in corpus}
    print(f"Corpus documents loaded: {len(corpus_by_id)}")

    distribution = Counter(q["qtype"] for q in questions)
    print("Question distribution:", dict(distribution))

    # Optional --limit flag for quick validation
    limit = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--limit":
        try:
            limit = int(sys.argv[2])
        except ValueError:
            limit = None

    if limit:
        questions_to_run = questions[:limit]
        print(f"TEST MODE: Running first {limit} questions")
    else:
        questions_to_run = questions
        print("FULL MODE: Running all 50 questions")

    # Connect to TigerGraph
    conn = get_connection()

    rag_correct = 0
    graphrag_correct = 0
    agentic_correct = 0
    results = []

    # Process questions
    for index, row in enumerate(questions_to_run, start=1):
        qid = row["qid"]
        qtype = row["qtype"]
        question = row["question"]
        gold_answer = row.get("answer", None)
        gold_doc_ids = row.get("gold_doc_ids", [])
        has_gold = gold_answer is not None

        print()
        print(f"Processing {index}/{len(questions_to_run)}")
        print("-" * 80)
        print(f"{qid} | {qtype}")
        print(f"Question: {question}")
        print(f"Expected: {gold_answer if has_gold else 'N/A (Hidden Ground Truth)'}")

        # ----------------------------------------------------
        # 1. Standard RAG
        # ----------------------------------------------------
        rag_result = rag_answer(
            question,
            corpus_by_id,
            qtype=qtype,
        )
        rag_predicted = rag_result.get("answer", [])
        rag_pass = answers_match(rag_predicted, gold_answer) if has_gold else None
        if rag_pass:
            rag_correct += 1

        rag_tokens = estimate_tokens_from_docs(rag_result.get("documents", []))
        rag_coverage = calculate_gold_coverage(
            rag_result.get("documents", []),
            gold_doc_ids,
        )
        status_rag = "PASS" if rag_pass else ("FAIL" if has_gold else "GENERATED")
        print(f"RAG       : {rag_predicted} | {status_rag}")

        # ----------------------------------------------------
        # 2. GraphRAG
        # ----------------------------------------------------
        try:
            graph_result = run_graph_query(conn, qtype, question)
        except Exception as exc:
            graph_result = {
                "query": None,
                "parameters": {},
                "results": [],
                "answer": [],
                "error": str(exc),
            }

        graph_predicted, graph_llm_meta = synthesize_graph_answer(
            question,
            graph_result,
            pipeline_name="GraphRAG",
        )
        graph_pass = answers_match(graph_predicted, gold_answer) if has_gold else None
        if graph_pass:
            graphrag_correct += 1

        graph_evidence = graph_result.get("results", [])
        graph_tokens = len(json.dumps(graph_evidence, ensure_ascii=False).split())
        status_graph = "PASS" if graph_pass else ("FAIL" if has_gold else "GENERATED")
        print(f"GraphRAG  : {graph_predicted} | {status_graph}")

        # ----------------------------------------------------
        # 3. Agentic GraphRAG
        # ----------------------------------------------------
        agentic_result = agentic_answer(
            conn,
            row,
            corpus_by_id,
        )
        agentic_predicted, agentic_llm_meta = synthesize_graph_answer(
            question,
            {
                "answer": agentic_result.get("answer", []),
                "results": agentic_result.get("evidence", []),
            },
            pipeline_name="Agentic GraphRAG",
        )
        agentic_pass = answers_match(agentic_predicted, gold_answer) if has_gold else None
        if agentic_pass:
            agentic_correct += 1

        agentic_evidence = agentic_result.get("evidence", [])
        agentic_tokens = len(json.dumps(agentic_evidence, ensure_ascii=False).split())
        status_agentic = "PASS" if agentic_pass else ("FAIL" if has_gold else "GENERATED")
        print(f"Agentic   : {agentic_predicted} | {status_agentic}")

        # Record record
        results.append({
            "qid": qid,
            "qtype": qtype,
            "question": question,
            "gold_answer": gold_answer,
            "rag": {
                "answer": rag_predicted,
                "correct": rag_pass,
                "estimated_evidence_tokens": rag_tokens,
                "gold_doc_coverage": rag_coverage,
                "llm_model": rag_result.get("llm_model", GROQ_MODEL),
                "llm_tokens": rag_result.get("llm_tokens", 0),
                "llm_latency": rag_result.get("llm_latency", 0.0),
            },
            "graphrag": {
                "answer": graph_predicted,
                "correct": graph_pass,
                "estimated_evidence_tokens": graph_tokens,
                "query": graph_result.get("query"),
                "parameters": graph_result.get("parameters"),
                "results": graph_evidence,
                "llm_model": graph_llm_meta.get("llm_model", GROQ_MODEL),
                "llm_tokens": graph_llm_meta.get("llm_tokens", 0),
                "llm_latency": graph_llm_meta.get("llm_latency", 0.0),
            },
            "agentic_graphrag": {
                "answer": agentic_predicted,
                "correct": agentic_pass,
                "actions": agentic_result.get("actions", []),
                "estimated_evidence_tokens": agentic_tokens,
                "llm_model": agentic_llm_meta.get("llm_model", GROQ_MODEL),
                "llm_tokens": agentic_llm_meta.get("llm_tokens", 0),
                "llm_latency": agentic_llm_meta.get("llm_latency", 0.0),
            },
        })

        time.sleep(2)

    # --------------------------------------------------------
    # Summarize & Save
    # --------------------------------------------------------
    total = len(questions_to_run)
    has_any_gold = any(r.get("gold_answer") is not None for r in results)
    rag_accuracy = (rag_correct / total) if (total and has_any_gold) else None
    graph_accuracy = (graphrag_correct / total) if (total and has_any_gold) else None
    agentic_accuracy = (agentic_correct / total) if (total and has_any_gold) else None

    output = {
        "benchmark": "Official Hidden 50-Question Benchmark",
        "dataset": "official_data/eval_hidden.jsonl",
        "total_questions": total,
        "question_distribution": dict(distribution),
        "summary": {
            "llm_model": GROQ_MODEL,
            "has_ground_truth": has_any_gold,
            "rag": {
                "correct": rag_correct if has_any_gold else None,
                "total": total,
                "accuracy": rag_accuracy,
                "avg_latency": (
                    sum(r["rag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["rag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },
            "graphrag": {
                "correct": graphrag_correct if has_any_gold else None,
                "total": total,
                "accuracy": graph_accuracy,
                "avg_latency": (
                    sum(r["graphrag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["graphrag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },
            "agentic_graphrag": {
                "correct": agentic_correct if has_any_gold else None,
                "total": total,
                "accuracy": agentic_accuracy,
                "avg_latency": (
                    sum(r["agentic_graphrag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["agentic_graphrag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },
        },
        "results": results,
    }

    # Save JSON
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nJSON results saved to: {RESULT_FILE}")

    # Save Markdown Report
    report_content = generate_markdown_report(output)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Markdown report saved to: {REPORT_FILE}")

    # Print Final Summary
    print("\n" + "=" * 80)
    print("HIDDEN 50 BENCHMARK COMPLETE")
    print("=" * 80)
    print(f"Total Questions Evaluated: {total}")
    print(f"LLM Model                : {GROQ_MODEL}")
    if has_any_gold:
        print(f"Standard RAG Accuracy    : {rag_correct}/{total} ({rag_accuracy:.2%})")
        print(f"GraphRAG Accuracy        : {graphrag_correct}/{total} ({graph_accuracy:.2%})")
        print(f"Agentic GraphRAG Accuracy: {agentic_correct}/{total} ({agentic_accuracy:.2%})")
    else:
        print("Ground Truth Answer Key  : Withheld (Hidden Evaluation Set)")
        print(f"Standard RAG Predictions : {total} generated")
        print(f"GraphRAG Predictions     : {total} generated")
        print(f"Agentic GraphRAG Preds   : {total} generated")
    print("=" * 80)


if __name__ == "__main__":
    main()
