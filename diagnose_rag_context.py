import json
import sys
from pathlib import Path

# Setup project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.official_vector_search import official_vector_search
from benchmark.run_official_three_way_benchmark import (
    get_rag_retrieval_settings,
    filter_rag_candidates,
)

EVAL_FILE = PROJECT_ROOT / "official_data" / "eval_public.jsonl"
CORPUS_FILE = PROJECT_ROOT / "official_data" / "corpus.jsonl"


def load_data():
    questions = []
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    corpus_by_id = {}
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                corpus_by_id[doc["doc_id"]] = doc

    return questions, corpus_by_id


def main():
    questions, corpus_by_id = load_data()

    target_qids = ["pub-001", "pub-002", "pub-004", "pub-005", "pub-009"]
    target_questions = [q for q in questions if q["qid"] in target_qids]

    print("=" * 80)
    print("ADAPTIVE RAG RETRIEVAL & CONTEXT SIZE DIAGNOSTIC")
    print("=" * 80)

    print("\nTarget Questions Adaptive Evaluation:")
    print("-" * 80)
    print(f"{'QID':<10} | {'Type':<12} | {'Settings Selected':<30} | {'Docs':<5} | {'Gold':<8} | {'Context Chars':<14} | {'Est Tokens'}")
    print("-" * 80)

    for q in target_questions:
        qid = q["qid"]
        qtype = q["qtype"]
        question = q["question"]
        gold_ids = set(q.get("gold_doc_ids", []))

        # 1. Get adaptive settings
        settings = get_rag_retrieval_settings(question, qtype)
        top_k = settings["initial_top_k"]
        max_chars = settings["max_chars_per_doc"]

        # 2. Vector search with adaptive initial_top_k
        retrieved = official_vector_search(question, top_k=top_k)
        retrieved_docs = [corpus_by_id[item["doc_id"]] for item in retrieved if item["doc_id"] in corpus_by_id]

        # 3. Adaptive candidate filtering
        if settings.get("apply_entity_filter"):
            selected_docs = filter_rag_candidates(
                question,
                retrieved_docs,
                max_docs=settings.get("max_filtered_docs", 25)
            )
        else:
            selected_docs = retrieved_docs[:top_k]

        # 4. Format evidence context
        evidence_blocks = []
        for i, d in enumerate(selected_docs, start=1):
            title = d.get("title", "").strip()
            snippet = (d.get("text", "") or "")[:max_chars]
            evidence_blocks.append(f"[Document {i}] {title}\n{snippet}")
        context_str = "\n\n".join(evidence_blocks)

        context_chars = len(context_str)
        est_tokens = context_chars / 4.0

        selected_ids = [d["doc_id"] for d in selected_docs]
        retrieved_gold = [doc_id for doc_id in selected_ids if doc_id in gold_ids]

        settings_str = f"top_k={top_k}, max_chars={max_chars}, filter={settings['apply_entity_filter']}"
        gold_str = f"{len(retrieved_gold)}/{len(gold_ids)}"

        print(f"{qid:<10} | {qtype:<12} | {settings_str:<30} | {len(selected_docs):<5} | {gold_str:<8} | {context_chars:<14} | {est_tokens:<10.1f}")

    print("-" * 80)

    # Detailed highlight for pub-001
    pub1 = next(q for q in target_questions if q["qid"] == "pub-001")
    pub1_settings = get_rag_retrieval_settings(pub1["question"], pub1["qtype"])
    pub1_retrieved = official_vector_search(pub1["question"], top_k=pub1_settings["initial_top_k"])
    pub1_docs = [corpus_by_id[item["doc_id"]] for item in pub1_retrieved if item["doc_id"] in corpus_by_id]
    pub1_selected = filter_rag_candidates(pub1["question"], pub1_docs, max_docs=pub1_settings.get("max_filtered_docs", 25))

    pub1_blocks = []
    for i, d in enumerate(pub1_selected, start=1):
        title = d.get("title", "").strip()
        snippet = (d.get("text", "") or "")[:pub1_settings["max_chars_per_doc"]]
        pub1_blocks.append(f"[Document {i}] {title}\n{snippet}")
    pub1_ctx = "\n\n".join(pub1_blocks)
    pub1_gold_set = set(pub1["gold_doc_ids"])
    pub1_matched = [d["doc_id"] for d in pub1_selected if d["doc_id"] in pub1_gold_set]

    print("\nDETAILED RESULT FOR pub-001:")
    print("  Question          :", pub1["question"])
    print("  Question Type     :", pub1["qtype"])
    print("  Selected Settings :", f"top_k={pub1_settings['initial_top_k']}, max_chars_per_doc={pub1_settings['max_chars_per_doc']}, apply_entity_filter={pub1_settings['apply_entity_filter']}")
    print("  Candidate Pool    :", len(pub1_docs), "documents retrieved from vector index")
    print("  Filtered Evidence :", len(pub1_selected), "documents preserved after entity matching")
    print(f"  Gold Docs Retrieved: {len(pub1_matched)} / {len(pub1_gold_set)} ({len(pub1_matched)/len(pub1_gold_set):.1%})")
    print(f"  Total Context Size : {len(pub1_ctx)} characters (~{len(pub1_ctx)/4.0:.1f} estimated tokens)")
    print("  Documents in Evidence:")
    for d in pub1_selected:
        is_gold = "GOLD" if d["doc_id"] in pub1_gold_set else "OTHER"
        print(f"    [{is_gold}] {d['doc_id']}: {d['title']}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
