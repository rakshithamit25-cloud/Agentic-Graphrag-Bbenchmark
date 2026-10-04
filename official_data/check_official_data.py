"""
Validation script for official hackathon evaluation dataset and corpus.
This script ONLY inspects and validates the files, without making any modifications.
"""

import os
import sys
import json
from collections import Counter
from pathlib import Path


def main():
    print("=" * 80)
    print("OFFICIAL DATASET & CORPUS VALIDATION (PHASE 1)")
    print("=" * 80)

    base_dir = Path(__file__).resolve().parent
    eval_file = base_dir / "eval_public.jsonl"
    corpus_file = base_dir / "corpus.jsonl"

    # Step 1 & 2 Checks: File existence
    print(f"\n[1] Checking file existence...")
    print(f"  Eval file path:   {eval_file}")
    print(f"  Eval file exists: {eval_file.exists()}")
    print(f"  Corpus file path:   {corpus_file}")
    print(f"  Corpus file exists: {corpus_file.exists()}")

    if not eval_file.exists():
        print(f"ERROR: {eval_file} not found!")
        sys.exit(1)
    if not corpus_file.exists():
        print(f"ERROR: {corpus_file} not found!")
        sys.exit(1)

    # Step 3, 4, 12, 13: Parse eval_public.jsonl
    print(f"\n[2] Parsing evaluation dataset: {eval_file.name}...")
    eval_records = []
    eval_malformed_lines = []
    with open(eval_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = json.loads(line_str)
                eval_records.append(record)
            except Exception as e:
                eval_malformed_lines.append((line_num, str(e)))

    print(f"  Total evaluation records parsed: {len(eval_records)}")
    if eval_malformed_lines:
        print(f"  WARNING: Found {len(eval_malformed_lines)} malformed lines in evaluation file:")
        for line_num, err in eval_malformed_lines:
            print(f"    Line {line_num}: {err}")
    else:
        print("  All evaluation lines parsed successfully (0 malformed lines).")

    # Step 5, 6, 12, 13: Parse corpus.jsonl
    print(f"\n[3] Parsing corpus dataset: {corpus_file.name}...")
    corpus_docs = []
    corpus_doc_ids = set()
    corpus_malformed_lines = []
    with open(corpus_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = json.loads(line_str)
                corpus_docs.append(record)
                if "doc_id" in record:
                    corpus_doc_ids.add(record["doc_id"])
            except Exception as e:
                corpus_malformed_lines.append((line_num, str(e)))

    print(f"  Total corpus documents parsed: {len(corpus_docs)}")
    print(f"  Total unique corpus doc_ids:   {len(corpus_doc_ids)}")
    if corpus_malformed_lines:
        print(f"  WARNING: Found {len(corpus_malformed_lines)} malformed lines in corpus file:")
        for line_num, err in corpus_malformed_lines:
            print(f"    Line {line_num}: {err}")
    else:
        print("  All corpus lines parsed successfully (0 malformed lines).")

    # Step 7 & 8: Keys / fields of first records
    print(f"\n[4] Record Field Names / Keys:")
    first_eval = eval_records[0] if eval_records else {}
    first_corpus = corpus_docs[0] if corpus_docs else {}
    print(f"  First evaluation record keys ({len(first_eval.keys())} keys):")
    print(f"    {list(first_eval.keys())}")
    print(f"  First corpus record keys ({len(first_corpus.keys())} keys):")
    print(f"    {list(first_corpus.keys())}")

    # Step 9, 10, 11: First 3 evaluation questions
    print(f"\n[5] First 3 Evaluation Questions:")
    for idx, rec in enumerate(eval_records[:3], 1):
        print(f"  --- Question #{idx} ---")
        print(f"    QID:      {rec.get('qid')}")
        print(f"    QType:    {rec.get('qtype')}")
        print(f"    Question: {rec.get('question')}")
        print(f"    Gold Doc IDs: {rec.get('gold_doc_ids')}")
        print(f"    Answer:   {rec.get('answer')}")

    # Step 6: Verify gold document IDs against corpus
    print(f"\n[6] Gold Document IDs Verification:")
    all_gold_doc_ids = set()
    questions_with_gold = 0
    for rec in eval_records:
        gold_ids = rec.get("gold_doc_ids", [])
        if gold_ids:
            questions_with_gold += 1
            for gid in gold_ids:
                all_gold_doc_ids.add(gid)

    found_ids = all_gold_doc_ids.intersection(corpus_doc_ids)
    missing_ids = all_gold_doc_ids.difference(corpus_doc_ids)

    print(f"  Number of evaluation questions:         {len(eval_records)}")
    print(f"  Questions with gold_doc_ids:            {questions_with_gold}")
    print(f"  Total unique gold document IDs:         {len(all_gold_doc_ids)}")
    print(f"  Gold document IDs FOUND in corpus:      {len(found_ids)}")
    print(f"  Gold document IDs MISSING from corpus:  {len(missing_ids)}")
    if missing_ids:
        print(f"  Missing Gold Doc IDs sample (up to 10): {sorted(list(missing_ids))[:10]}")
    else:
        print(f"  All gold document IDs are present in the corpus!")

    # Step 7: Detailed structure of ONE evaluation record and ONE corpus record
    print(f"\n[7] Detailed Structure of ONE Evaluation Record:")
    print(f"  Record QID: {first_eval.get('qid')}")
    for k, v in first_eval.items():
        v_repr = repr(v)
        if len(v_repr) > 120:
            v_repr = v_repr[:120] + "... (truncated)"
        print(f"    - {k} ({type(v).__name__}): {v_repr}")

    print(f"\n[8] Detailed Structure of ONE Corpus Record:")
    print(f"  Doc ID: {first_corpus.get('doc_id')}")
    for k, v in first_corpus.items():
        if k == "text":
            text_preview = repr(v[:150] + "...")
            print(f"    - {k} ({type(v).__name__}, total length={len(v)} chars): {text_preview}")
        else:
            print(f"    - {k} ({type(v).__name__}): {repr(v)}")

    # Step 8: Question Type Distribution
    print(f"\n[9] Question Type (qtype) Distribution:")
    qtypes = [rec.get("qtype", "UNKNOWN") for rec in eval_records]
    qtype_counts = Counter(qtypes)
    for qtype, count in qtype_counts.most_common():
        percentage = (count / len(eval_records)) * 100 if eval_records else 0
        print(f"  {qtype}: {count} ({percentage:.1f}%)")

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print(f"  - Eval records:    {len(eval_records)}")
    print(f"  - Corpus records:  {len(corpus_docs)}")
    print(f"  - Eval parsing:    {'SUCCESS (0 errors)' if not eval_malformed_lines else 'FAILED'}")
    print(f"  - Corpus parsing:  {'SUCCESS (0 errors)' if not corpus_malformed_lines else 'FAILED'}")
    print(f"  - Gold doc match:  {len(found_ids)}/{len(all_gold_doc_ids)} ({100 * len(found_ids)/len(all_gold_doc_ids):.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    main()
