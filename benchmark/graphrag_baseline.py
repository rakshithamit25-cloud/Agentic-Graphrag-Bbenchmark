import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from graph_rag import run_graphrag


def load_questions():

    file_path = Path(__file__).parent / "livestock_questions.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_graphrag_benchmark():

    questions = load_questions()

    correct = 0

    for item in questions:

        print("\n==============================")
        print("Question:")
        print(item["question"])

        result = run_graphrag(item["question"])

        print("\nGraph Evidence:")
        print(result["graph_evidence"])

        print("\nVector Evidence:")
        print(result["vector_evidence"])

        expected = item.get("expected_disease", "")

        graph_text = str(result["graph_evidence"])

        vector_text = str(result["vector_evidence"])

        evidence_text = graph_text + " " + vector_text

        if expected.lower() in evidence_text.lower():

            correct += 1
            print("\nResult: CORRECT")

        else:

            print("\nResult: INCORRECT")

    print("\n==============================")
    print("GRAPHRAG BENCHMARK RESULT")
    print("==============================")

    print(f"Correct: {correct}/{len(questions)}")


if __name__ == "__main__":

    run_graphrag_benchmark()