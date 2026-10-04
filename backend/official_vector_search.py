"""
Official Vector Search Module for Hackathon Official Corpus.
Uses FastEmbed with model: BAAI/bge-small-en-v1.5
Persists precomputed embeddings and metadata in official_data/vector_index/
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from fastembed import TextEmbedding

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
OFFICIAL_DATA_DIR = BASE_DIR / "official_data"
INDEX_DIR = OFFICIAL_DATA_DIR / "vector_index"
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
METADATA_FILE = INDEX_DIR / "metadata.json"

MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Module-level singletons for performance
_model_instance: Optional[TextEmbedding] = None
_cached_embeddings: Optional[np.ndarray] = None
_cached_metadata: Optional[List[Dict[str, Any]]] = None


def get_embedding_model() -> TextEmbedding:
    """Get or initialize the FastEmbed model singleton."""
    global _model_instance
    if _model_instance is None:
        _model_instance = TextEmbedding(model_name=MODEL_NAME)
    return _model_instance


def build_or_load_index(force_rebuild: bool = False) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Load precomputed vector index from disk if present.
    Otherwise, compute embeddings for all documents in the official corpus and save to disk.
    
    Preserves in index:
      - doc_id
      - title
      - url
      - wikidata_qid
      - wikipedia_pageid
      - approx_tokens
      - text
      - embedding/vector information
    """
    global _cached_embeddings, _cached_metadata

    if not force_rebuild and _cached_embeddings is not None and _cached_metadata is not None:
        return _cached_embeddings, _cached_metadata

    # Check if persistent index files already exist
    if not force_rebuild and EMBEDDINGS_FILE.exists() and METADATA_FILE.exists():
        print(f"Loading persistent vector index from {INDEX_DIR}...")
        embeddings = np.load(EMBEDDINGS_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        if len(embeddings) == len(metadata) and len(metadata) > 0:
            print(f"Loaded index successfully: {len(metadata)} documents, embedding shape {embeddings.shape}.")
            _cached_embeddings = embeddings
            _cached_metadata = metadata
            return embeddings, metadata
        else:
            print("Index mismatch detected. Rebuilding index...")

    # Build new index
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    from official_corpus import load_official_corpus
    print("Loading official corpus documents for indexing...")
    corpus = load_official_corpus()
    total_docs = len(corpus)
    print(f"Total documents to embed: {total_docs}")

    model = get_embedding_model()

    # Prepare document texts for embedding (title + text)
    doc_texts = []
    metadata = []
    for doc in corpus:
        title = doc.get("title") or ""
        text = doc.get("text") or ""
        combined_text = f"{title}\n{text}".strip()
        doc_texts.append(combined_text)

        # Store metadata preserving all required fields
        metadata.append({
            "doc_id": doc.get("doc_id"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "wikidata_qid": doc.get("wikidata_qid"),
            "wikipedia_pageid": doc.get("wikipedia_pageid"),
            "approx_tokens": doc.get("approx_tokens"),
            "text": doc.get("text"),
        })

    print(f"Generating embeddings using {MODEL_NAME}...")
    batch_size = 64
    embedding_list = []
    
    # FastEmbed model.embed produces a generator of numpy arrays
    for emb in model.embed(doc_texts, batch_size=batch_size):
        embedding_list.append(emb)

    embeddings = np.array(embedding_list, dtype=np.float32)

    # Normalize embeddings to unit vectors for fast cosine similarity via dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    print(f"Saving vector index to {INDEX_DIR}...")
    np.save(EMBEDDINGS_FILE, embeddings)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"Index built and persisted successfully: {len(metadata)} documents, shape {embeddings.shape}.")
    _cached_embeddings = embeddings
    _cached_metadata = metadata
    return embeddings, metadata


def official_vector_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search official corpus documents by vector similarity against the query.
    
    Returns a list of top_k dictionaries containing:
      - doc_id
      - title
      - url
      - wikidata_qid
      - wikipedia_pageid
      - approx_tokens
      - text
      - score (cosine similarity score)
    """
    embeddings, metadata = build_or_load_index()

    if len(metadata) == 0:
        return []

    model = get_embedding_model()

    # Generate query embedding
    query_emb = list(model.embed([query]))[0]
    query_emb = np.array(query_emb, dtype=np.float32)
    norm = np.linalg.norm(query_emb)
    if norm > 0:
        query_emb = query_emb / norm

    # Cosine similarity via dot product against normalized vectors
    scores = np.dot(embeddings, query_emb)

    # Get top_k indices sorted descending
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        doc = metadata[idx]
        results.append({
            "doc_id": doc.get("doc_id"),
            "title": doc.get("title"),
            "url": doc.get("url"),
            "wikidata_qid": doc.get("wikidata_qid"),
            "wikipedia_pageid": doc.get("wikipedia_pageid"),
            "approx_tokens": doc.get("approx_tokens"),
            "text": doc.get("text"),
            "score": float(scores[idx]),
        })

    return results


if __name__ == "__main__":
    print("Initializing / testing official vector search...")
    test_query = "biathlon events at the 2018 Winter Olympics"
    results = official_vector_search(test_query, top_k=3)
    print(f"\nQuery: {test_query}")
    print(f"Retrieved {len(results)} results:")
    for r in results:
        print(f"  - Doc ID: {r['doc_id']} | Score: {r['score']:.4f} | Title: {r['title']}")
