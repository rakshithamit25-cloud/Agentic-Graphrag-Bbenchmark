import os
from pathlib import Path

from config import Config


DOCUMENTS_DIR = Path(__file__).parent / "data" / "documents"


def load_documents():
    """Load all text documents from the documents folder."""

    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents


def search_documents(query):
    """
    Simple keyword-based RAG search.

    This is the first working version.
    We will replace this with vector similarity search later.
    """

    documents = load_documents()

    query_words = set(query.lower().split())

    results = []

    for document in documents:
        text_lower = document["text"].lower()

        score = sum(
            1 for word in query_words
            if len(word) > 2 and word in text_lower
        )

        if score > 0:
            results.append({
                "source": document["source"],
                "score": score,
                "text": document["text"]
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results


if __name__ == "__main__":

    query = "Foot and Mouth Disease Tamil Nadu"

    results = search_documents(query)

    print("\n=== RAG SEARCH RESULTS ===")

    for result in results:
        print("\nSource:", result["source"])
        print("Score:", result["score"])
        print(result["text"])