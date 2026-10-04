from graph_tool import get_livestock_graph


def link_entities(question):
    """
    Identify important entities from the user's question.
    """

    question_lower = question.lower()

    result = {
        "market": None,
        "location": None,
        "disease": None,
        "disease_id": None
    }

    # Market / location detection
    if "tamil nadu" in question_lower:
        result["location"] = "Tamil Nadu"
        result["market"] = "Tamil Nadu Livestock Market"

    elif "karnataka" in question_lower:
        result["location"] = "Karnataka"
        result["market"] = "Karnataka Livestock Market"

    # Disease detection
    if "foot and mouth" in question_lower or "fmd" in question_lower:
        result["disease"] = "Foot and Mouth Disease"
        result["disease_id"] = "disease_001"

    elif "pneumonia" in question_lower:
        result["disease"] = "Pneumonia"
        result["disease_id"] = "disease_002"

    return result


if __name__ == "__main__":

    questions = [
        "Which disease is associated with the Tamil Nadu livestock market?",
        "Which disease is associated with the Karnataka livestock market?",
        "What treatment is associated with Foot and Mouth Disease?"
    ]

    for question in questions:

        print("\nQuestion:")
        print(question)

        entities = link_entities(question)

        print("Entities:")
        print(entities)