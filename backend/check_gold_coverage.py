"""
Check Official Gold Document Coverage in the Full Graph.
Reads official_data/eval_public.jsonl.
Evaluates graph coverage of gold document IDs across all 100 questions.
Breaks down coverage by question type:
- lookup
- multi_hop
- temporal
- aggregation
- superlative
STRICTLY a coverage check (does NOT claim benchmark accuracy).
"""

import sys
import json
from pathlib import Path
from collections import defaultdict, Counter

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))
from config import Config
import pyTigerGraph as tg

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_PATH = BASE_DIR / "official_data" / "eval_public.jsonl"


def check_gold_coverage():
    print("=" * 80)
    print("CHECKING OFFICIAL GOLD DOCUMENT COVERAGE IN OLYMPIC_BENCHMARK")
    print("=" * 80)

    # 1. Connect to TigerGraph OLYMPIC_BENCHMARK to get all loaded Document IDs
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )
    conn.getToken(Config.TG_SECRET)

    # Query all Document doc_ids and Event event_ids
    # We can fetch vertices via getVertices or check via REST++
    # Since Document vertices have primary_id as doc_id:
    print("Fetching loaded Document and Event vertices from OLYMPIC_BENCHMARK...")
    doc_vertices = conn.getVertices("Document", limit=10000)
    event_vertices = conn.getVertices("Event", limit=10000)

    loaded_doc_ids = set()
    for d in doc_vertices:
        loaded_doc_ids.add(d["v_id"])

    loaded_event_ids = set()
    for e in event_vertices:
        loaded_event_ids.add(e["v_id"])

    print(f"Loaded Document vertices in graph: {len(loaded_doc_ids)}")
    print(f"Loaded Event vertices in graph:    {len(loaded_event_ids)}")

    # 2. Parse eval_public.jsonl
    questions = []
    all_gold_doc_ids = set()
    questions_by_type = defaultdict(list)

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            q = json.loads(line)
            questions.append(q)
            qtype = q["qtype"]
            questions_by_type[qtype].append(q)
            for gid in q.get("gold_doc_ids", []):
                all_gold_doc_ids.add(gid)

    total_questions = len(questions)
    total_unique_gold = len(all_gold_doc_ids)

    # 3. Overall Gold Document Coverage
    found_gold_in_doc = all_gold_doc_ids & loaded_doc_ids
    missing_gold_in_doc = all_gold_doc_ids - loaded_doc_ids

    # Also check if the corresponding Event vertex exists (event_{gid})
    found_gold_in_event = {gid for gid in all_gold_doc_ids if f"event_{gid}" in loaded_event_ids}
    missing_gold_in_event = all_gold_doc_ids - found_gold_in_event

    print(f"\nOverall Coverage:")
    print(f"  Total Questions:                 {total_questions}")
    print(f"  Total Unique Gold Document IDs:  {total_unique_gold}")
    print(f"  Gold Docs found as Document:     {len(found_gold_in_doc)} / {total_unique_gold} ({len(found_gold_in_doc)/total_unique_gold*100:.1f}%)")
    print(f"  Gold Docs found as Event:        {len(found_gold_in_event)} / {total_unique_gold} ({len(found_gold_in_event)/total_unique_gold*100:.1f}%)")
    print(f"  Missing Gold Docs:               {len(missing_gold_in_doc)}")

    # 4. Coverage breakdown by Question Type
    coverage_by_type = {}
    print("\nCoverage Breakdown by Question Type:")
    print(f"{'Question Type':<15} | {'Questions':<10} | {'Unique Gold':<12} | {'Found in Graph':<15} | {'Missing':<10} | {'Coverage %':<10}")
    print("-" * 80)

    for qtype in ["lookup", "multi_hop", "temporal", "aggregation", "superlative"]:
        q_list = questions_by_type.get(qtype, [])
        type_gold_ids = set()
        for q in q_list:
            for gid in q.get("gold_doc_ids", []):
                type_gold_ids.add(gid)

        found_in_graph = type_gold_ids & loaded_doc_ids
        missing_from_graph = type_gold_ids - loaded_doc_ids
        pct = (len(found_in_graph) / len(type_gold_ids) * 100) if type_gold_ids else 0.0

        coverage_by_type[qtype] = {
            "questions_count": len(q_list),
            "unique_gold_count": len(type_gold_ids),
            "found_count": len(found_in_graph),
            "missing_count": len(missing_from_graph),
            "coverage_pct": pct
        }

        print(f"{qtype:<15} | {len(q_list):<10} | {len(type_gold_ids):<12} | {len(found_in_graph):<15} | {len(missing_from_graph):<10} | {pct:>8.1f}%")

    # 5. Question-Level Full Coverage (Does question have 100% of its gold docs in graph?)
    fully_covered_questions = 0
    partially_covered_questions = 0
    zero_covered_questions = 0

    for q in questions:
        gids = set(q.get("gold_doc_ids", []))
        if not gids:
            continue
        found = gids & loaded_doc_ids
        if len(found) == len(gids):
            fully_covered_questions += 1
        elif len(found) > 0:
            partially_covered_questions += 1
        else:
            zero_covered_questions += 1

    print("\nQuestion-Level Coverage:")
    print(f"  Questions with 100% gold docs in graph: {fully_covered_questions} / {total_questions} ({fully_covered_questions/total_questions*100:.1f}%)")
    print(f"  Questions with Partial gold docs:       {partially_covered_questions} / {total_questions}")
    print(f"  Questions with Zero gold docs:          {zero_covered_questions} / {total_questions}")

    report_payload = {
        "total_questions": total_questions,
        "total_unique_gold_doc_ids": total_unique_gold,
        "gold_docs_found_in_graph": len(found_gold_in_doc),
        "gold_docs_missing_from_graph": len(missing_gold_in_doc),
        "coverage_by_type": coverage_by_type,
        "fully_covered_questions": fully_covered_questions
    }

    return report_payload


if __name__ == "__main__":
    check_gold_coverage()
