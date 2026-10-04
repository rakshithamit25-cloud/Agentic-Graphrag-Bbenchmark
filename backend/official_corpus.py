"""
Loader for the official hackathon corpus.
Reads official_data/corpus.jsonl and provides load_official_corpus().
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

CORPUS_PATH = Path(__file__).resolve().parent.parent / "official_data" / "corpus.jsonl"

REQUIRED_FIELDS = [
    "doc_id",
    "title",
    "url",
    "wikidata_qid",
    "wikipedia_pageid",
    "approx_tokens",
    "text",
]


def load_official_corpus(corpus_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load and parse all documents from official_data/corpus.jsonl.
    Preserves all fields: doc_id, title, url, wikidata_qid, wikipedia_pageid, approx_tokens, text.
    Does not modify the original corpus.jsonl file.
    """
    path = Path(corpus_path) if corpus_path else CORPUS_PATH
    if not path.exists():
        raise FileNotFoundError(f"Official corpus file not found at: {path}")

    documents = []
    with open(path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            record = json.loads(line_str)
            # Ensure all required fields are preserved exactly
            doc = {
                "doc_id": record.get("doc_id"),
                "title": record.get("title"),
                "url": record.get("url"),
                "wikidata_qid": record.get("wikidata_qid"),
                "wikipedia_pageid": record.get("wikipedia_pageid"),
                "approx_tokens": record.get("approx_tokens"),
                "text": record.get("text"),
            }
            # Keep any extra fields if present
            for k, v in record.items():
                if k not in doc:
                    doc[k] = v
            documents.append(doc)

    return documents


if __name__ == "__main__":
    docs = load_official_corpus()
    print(f"Loaded {len(docs)} documents from official corpus.")
    if docs:
        first = docs[0]
        print(f"First doc_id: {first.get('doc_id')}")
        print(f"Title: {first.get('title')}")
        print(f"Preserved fields: {list(first.keys())}")
