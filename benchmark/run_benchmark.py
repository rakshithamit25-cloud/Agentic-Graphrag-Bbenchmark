import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from agent import run_agent


def load_questions():

    file_path = Path(__file__).parent / "livestock_questions.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_completeness(item, answer):

    expected = item.get("expected_disease", "").lower()

    answer_lower = answer.lower()

    if expected in answer_lower:
        return 1.0

    return 0.0


def estimate_tokens(text):

    # Approximate token count.
    # This is a local estimate, not an LLM API token count.
    words = text.split()

    return max(1, int(len(words) * 1.3))


def run_benchmark():

    questions = load_questions()

    total_questions = len(questions)

    correct = 0
    completeness_total = 0.0
    token_total = 0

    results = []

    for item in questions:

        print("\n==============================")
        print("Question:")
        print(item["question"])

        result = run_agent(item["question"])

        answer = result.final_answer or ""

        print("\nAgent Answer:")
        print(answer)

        expected = item.get("expected_disease", "")

        # -----------------------------
        # Accuracy
        # -----------------------------

        is_correct = expected.lower() in answer.lower()

        if is_correct:
            correct += 1
            print("\nResult: CORRECT")
        else:
            print("\nResult: INCORRECT")

        # -----------------------------
        # Completeness
        # -----------------------------

        completeness = calculate_completeness(
            item,
            answer
        )

        completeness_total += completeness

        # -----------------------------
        # Token efficiency
        # -----------------------------

        tokens = estimate_tokens(answer)

        token_total += tokens

        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected": expected,
            "correct": is_correct,
            "completeness": completeness,
            "estimated_tokens": tokens,
            "actions": result.actions_taken,
            "confidence": result.confidence
        })


    # -----------------------------
    # Final metrics
    # -----------------------------

    accuracy = correct / total_questions

    completeness_average = (
        completeness_total / total_questions
    )

    average_tokens = token_total / total_questions


    print("\n==============================")
    print("ROUND 1 METRICS")
    print("==============================")

    print(
        f"Accuracy: {accuracy * 100:.2f}%"
    )

    print(
        f"Completeness: "
        f"{completeness_average * 100:.2f}%"
    )

    print(
        f"Average estimated tokens: "
        f"{average_tokens:.2f}"
    )

    print(
        f"Total estimated tokens: "
        f"{token_total}"
    )


    # -----------------------------
    # Save results
    # -----------------------------

    output = {
        "benchmark_type": "Custom demo benchmark",
        "total_questions": total_questions,
        "correct": correct,
        "accuracy": accuracy,
        "completeness": completeness_average,
        "average_estimated_tokens": average_tokens,
        "total_estimated_tokens": token_total,
        "results": results
    }


    output_file = (
        Path(__file__).parent /
        "results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )


    print("\nResults saved to:")

    print(output_file)


if __name__ == "__main__":

    run_benchmark()