from pathlib import Path
from fastembed import TextEmbedding

DOCUMENTS_DIR = Path(__file__).parent / "data" / "documents"

# Local embedding model
MODEL_NAME = "BAAI/bge-small-en-v1.5"

model = TextEmbedding(model_name=MODEL_NAME)


def load_documents():
    documents = []

    for file_path in DOCUMENTS_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))

    magnitude_a = sum(x * x for x in a) ** 0.5
    magnitude_b = sum(x * x for x in b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot / (magnitude_a * magnitude_b)


def vector_search(query, top_k=3):
    documents = load_documents()

    if not documents:
        return []

    # Create query embedding
    query_embedding = list(model.embed([query]))[0]

    results = []

    for document in documents:
        document_embedding = list(model.embed([document["text"]]))[0]

        score = cosine_similarity(
            query_embedding,
            document_embedding
        )

        results.append({
            "source": document["source"],
            "score": score,
            "text": document["text"]
        })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":

    query = "Which disease is associated with the Tamil Nadu livestock market?"

    print("\n=== VECTOR SEARCH ===")
    print("Question:", query)

    results = vector_search(query)

    for result in results:
        print("\nSource:", result["source"])
        print("Similarity:", round(result["score"], 4))
        print(result["text"])