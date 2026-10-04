import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from rag_tool import search_documents


def load_questions():

    file_path = Path(__file__).parent / "livestock_questions.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_rag_benchmark():

    questions = load_questions()

    correct = 0

    for item in questions:

        print("\n==============================")
        print("Question:")
        print(item["question"])

        results = search_documents(item["question"])

        if results:

            answer_text = results[0]["text"]

        else:

            answer_text = "No relevant evidence found."

        print("\nRAG Evidence:")
        print(answer_text)

        expected = item.get("expected_disease", "")

        if expected.lower() in answer_text.lower():

            correct += 1
            print("\nResult: CORRECT")

        else:

            print("\nResult: INCORRECT")

    print("\n==============================")
    print("RAG BENCHMARK RESULT")
    print("==============================")

    print(f"Correct: {correct}/{len(questions)}")


if __name__ == "__main__":

    run_rag_benchmark()