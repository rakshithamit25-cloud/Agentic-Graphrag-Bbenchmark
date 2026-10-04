"""
Benchmark test script for Phase 2: Official RAG retrieval on official dataset.
Tests questions: pub-001, pub-002, pub-003 from eval_public.jsonl
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from official_vector_search import official_vector_search

EVAL_PATH = BASE_DIR / "official_data" / "eval_public.jsonl"
TARGET_QIDS = ["pub-001", "pub-002", "pub-003"]
TOP_K = 5


def load_eval_questions(target_qids):
    """Load specific evaluation questions by QID."""
    questions = {}
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("qid") in target_qids:
                questions[rec["qid"]] = rec
    return questions


def main():
    print("=" * 80)
    print("PHASE 2 — OFFICIAL RAG RETRIEVAL TEST")
    print(f"Target Questions: {', '.join(TARGET_QIDS)}")
    print(f"Top-K Retrieval: {TOP_K}")
    print("=" * 80)

    eval_data = load_eval_questions(TARGET_QIDS)
    summary_results = []

    for qid in TARGET_QIDS:
        rec = eval_data.get(qid)
        if not rec:
            print(f"\n[ERROR] Question {qid} not found in evaluation file!")
            continue

        question = rec.get("question")
        qtype = rec.get("qtype")
        expected_answer = rec.get("answer")
        gold_doc_ids = rec.get("gold_doc_ids", [])
        gold_set = set(gold_doc_ids)

        print(f"\n------------------------------------------------------------")
        print(f"QUESTION ID:     {qid}")
        print(f"QUESTION TYPE:   {qtype}")
        print(f"QUESTION:        {question}")
        print(f"EXPECTED ANSWER: {expected_answer}")
        print(f"GOLD DOC IDS:    {gold_doc_ids}")
        print(f"------------------------------------------------------------")

        # Run vector retrieval
        retrieved_docs = official_vector_search(question, top_k=TOP_K)

        retrieved_ids = [d["doc_id"] for d in retrieved_docs]
        retrieved_scores = [d["score"] for d in retrieved_docs]

        # Check whether any gold doc was retrieved
        found_golds = [doc_id for doc_id in retrieved_ids if doc_id in gold_set]
        at_least_one_gold = len(found_golds) > 0

        print(f"Top {len(retrieved_docs)} Retrieved Documents:")
        for idx, doc in enumerate(retrieved_docs, 1):
            is_gold = " [MATCHES GOLD!]" if doc["doc_id"] in gold_set else ""
            print(f"  {idx}. [{doc['doc_id']}] score: {doc['score']:.4f} | {doc['title']}{is_gold}")

        print(f"\nRetrieved Doc IDs: {retrieved_ids}")
        print(f"Similarity Scores: {[round(s, 4) for s in retrieved_scores]}")
        print(f"Gold Document IDs: {gold_doc_ids}")
        print(f"At least one gold document retrieved: {at_least_one_gold}")
        if at_least_one_gold:
            print(f"Matched Gold Doc IDs in Top-{TOP_K}: {found_golds}")

        summary_results.append({
            "qid": qid,
            "qtype": qtype,
            "question": question,
            "expected_answer": expected_answer,
            "gold_doc_ids": gold_doc_ids,
            "retrieved_ids": retrieved_ids,
            "similarity_scores": [round(s, 4) for s in retrieved_scores],
            "at_least_one_gold": at_least_one_gold,
            "matched_golds": found_golds,
        })

    print("\n" + "=" * 80)
    print("PHASE 2 RETRIEVAL SUMMARY")
    print("=" * 80)
    for res in summary_results:
        status = "HIT (Gold Doc Retrieved)" if res["at_least_one_gold"] else "MISS (No Gold Doc in Top-K)"
        print(f"- {res['qid']} ({res['qtype']}): {status}")
        if res["at_least_one_gold"]:
            print(f"  Matched: {res['matched_golds']} of {len(res['gold_doc_ids'])} gold docs")
        else:
            print(f"  Top retrieved: {res['retrieved_ids'][:3]}")
    print("=" * 80)


if __name__ == "__main__":
    main()
