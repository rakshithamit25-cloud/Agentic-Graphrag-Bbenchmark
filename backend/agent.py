from agent_state import AgentState
from agent_router import (
    decide_next_action,
    understand_question,
    graph_has_required_information
)

from graph_tool import (
    get_livestock_graph,
    get_disease_by_market
)

from vector_tool import vector_search
from entity_linker import link_entities


def get_name(item):

    """
    Safely extract a vertex name from
    TigerGraph evidence.
    """

    if not item:
        return None

    return (
        item.get("attributes", {})
        .get("name")
    )


def build_final_answer(state):

    graph = state.graph_evidence

    question = state.question.lower()

    diseases = graph.get("diseases", [])
    treatments = graph.get("treatments", [])
    outbreaks = graph.get("outbreaks", [])
    markets = graph.get("markets", [])

    disease_name = (
        get_name(diseases[0])
        if diseases
        else None
    )

    treatment_name = (
        get_name(treatments[0])
        if treatments
        else None
    )

    outbreak_name = (
        get_name(outbreaks[0])
        if outbreaks
        else None
    )

    market_name = (
        get_name(markets[0])
        if markets
        else None
    )

    # ----------------------------------------------
    # Treatment
    # ----------------------------------------------

    if (
        "treatment" in question
        and treatment_name
        and disease_name
    ):

        state.final_answer = (
            f"The treatment associated with "
            f"{disease_name} is "
            f"{treatment_name}."
        )

        state.final_answer += (
            "\n\nEvidence path:"
            f"\n{disease_name}"
            f" → {treatment_name}"
        )

    # ----------------------------------------------
    # Outbreak
    # ----------------------------------------------

    elif (
        "which outbreak" in question
        and outbreak_name
        and disease_name
    ):

        state.final_answer = (
            f"The outbreak associated with "
            f"{disease_name} is "
            f"{outbreak_name}."
        )

        state.final_answer += (
            "\n\nEvidence path:"
            f"\n{disease_name}"
            f" → {outbreak_name}"
        )

    # ----------------------------------------------
    # Market
    # ----------------------------------------------

    elif (
        "which market" in question
        and market_name
    ):

        state.final_answer = (
            f"The market affected by "
            f"{outbreak_name} is "
            f"{market_name}."
        )

        state.final_answer += (
            "\n\nEvidence path:"
            f"\n{disease_name}"
            f" → {outbreak_name}"
            f" → {market_name}"
        )

    # ----------------------------------------------
    # Disease associated with market
    # ----------------------------------------------

    elif (
        "which disease" in question
        and disease_name
        and market_name
    ):

        state.final_answer = (
            f"The disease associated with "
            f"{market_name} is "
            f"{disease_name}."
        )

        state.final_answer += (
            "\n\nEvidence path:"
            f"\n{disease_name}"
            f" → {outbreak_name}"
            f" → {market_name}"
        )

    # ----------------------------------------------
    # Insufficient evidence
    # ----------------------------------------------

    else:

        state.final_answer = (
            "The available evidence was not "
            "sufficient to determine the answer."
        )


def evaluate_evidence(state):

    """
    Evaluate graph and vector evidence.

    This is intentionally deterministic for the
    current benchmark dataset.
    """

    graph_available = bool(
        state.graph_evidence
    )

    vector_available = bool(
        state.vector_evidence
    )

    required_found = graph_has_required_information(
        state
    )

    # Both sources support the investigation
    if (
        graph_available
        and vector_available
        and required_found
    ):

        state.evidence_agrees = True
        state.update_confidence(0.85)

    # Graph alone contains the required answer
    elif (
        graph_available
        and required_found
    ):

        state.evidence_agrees = False
        state.update_confidence(0.70)

        state.add_missing_information(
            "independent document confirmation"
        )

    # Vector evidence exists but graph does not
    elif vector_available:

        state.evidence_agrees = False
        state.update_confidence(0.40)

        state.add_missing_information(
            "graph confirmation"
        )

    else:

        state.evidence_agrees = False
        state.update_confidence(0.20)

        state.add_missing_information(
            "supporting evidence"
        )

    state.evidence_evaluated = True


def run_agent(question):

    state = AgentState(question)

    # ==================================================
    # 1. UNDERSTAND QUESTION
    # ==================================================

    entities = link_entities(question)

    understand_question(state)

    print("\n[AGENT] Entity Linking:")
    print(entities)

    print("\n[AGENT] Required Information:")
    print(state.required_information)

    # ==================================================
    # 2. ENTITY INFORMATION
    # ==================================================

    disease_id = entities.get(
        "disease_id"
    )

    market = entities.get(
        "market"
    )

    # ==================================================
    # 3. MARKET → TIGERGRAPH ID
    # ==================================================

    market_id = None

    if market == "Tamil Nadu Livestock Market":

        market_id = "market_001"

    elif market == "Karnataka Livestock Market":

        market_id = "market_002"

    # ==================================================
    # 4. AGENTIC INVESTIGATION LOOP
    # ==================================================

    while not state.should_stop():

        action = decide_next_action(state)

        # ------------------------------------------------
        # Special case:
        # Market question requires reverse graph search.
        # ------------------------------------------------

        if (
            action == "GRAPH"
            and not disease_id
            and market_id
            and not state.graph_evidence
        ):

            action = "MARKET_GRAPH"

        state.record_action(action)

        print(
            f"\n[AGENT] Action: {action}"
        )

        # ==================================================
        # GRAPH SEARCH
        # ==================================================

        if action == "GRAPH":

            print(
                "[TOOL] Querying TigerGraph..."
            )

            if disease_id:

                state.graph_evidence = (
                    get_livestock_graph(
                        disease_id
                    )
                )

            else:

                print(
                    "[AGENT] Disease entity "
                    "was not identified."
                )

                state.add_missing_information(
                    "disease"
                )

        # ==================================================
        # MARKET GRAPH SEARCH
        # ==================================================

        elif action == "MARKET_GRAPH":

            print(
                "[TOOL] Finding disease from market "
                "using TigerGraph..."
            )

            diseases = (
                get_disease_by_market(
                    market_id
                )
            )

            if diseases:

                disease = diseases[0]

                disease_id = disease.get(
                    "v_id"
                )

                print(
                    "[AGENT] Disease found:",
                    disease.get(
                        "attributes",
                        {}
                    ).get(
                        "name"
                    )
                )

                state.graph_evidence = (
                    get_livestock_graph(
                        disease_id
                    )
                )

                state.remove_missing_information(
                    "disease"
                )

            else:

                print(
                    "[AGENT] No disease found "
                    "for this market."
                )

                state.add_missing_information(
                    "disease"
                )

        # ==================================================
        # VECTOR / DOCUMENT SEARCH
        # ==================================================

        elif action == "VECTOR":

            print(
                "[TOOL] Searching documents..."
            )

            state.vector_evidence = (
                vector_search(
                    question,
                    top_k=3
                )
            )

            if state.vector_evidence:

                print(
                    "[AGENT] Document evidence found."
                )

            else:

                state.add_missing_information(
                    "document evidence"
                )

        # ==================================================
        # EVIDENCE EVALUATION
        # ==================================================

        elif action == "EVALUATE":

            print(
                "[AGENT] Evaluating evidence..."
            )

            evaluate_evidence(state)

            print(
                "[AGENT] Confidence:",
                state.confidence
            )

            print(
                "[AGENT] Evidence agrees:",
                state.evidence_agrees
            )

        # ==================================================
        # STOP
        # ==================================================

        elif action == "STOP":

            print(
                "[AGENT] Investigation stopped."
            )

            break

    # ==================================================
    # 5. BUILD FINAL ANSWER
    # ==================================================

    build_final_answer(state)

    state.stopped = True

    return state


if __name__ == "__main__":

    question = (
        "Which disease is associated with "
        "the Karnataka livestock market?"
    )

    result = run_agent(question)

    print(
        "\n=============================="
    )

    print(
        "       AGENTIC GRAPHRAG"
    )

    print(
        "=============================="
    )

    print("\nQuestion:")
    print(result.question)

    print("\nRequired Information:")

    for item in result.required_information:

        print("-", item)

    print("\nActions Taken:")

    for action in result.actions_taken:

        print("-", action)

    print("\nConfidence:")
    print(result.confidence)

    print("\nEvidence Agreement:")
    print(result.evidence_agrees)

    print("\nMissing Information:")

    if result.missing_information:

        for item in result.missing_information:

            print("-", item)

    else:

        print("None")

    print("\nFinal Answer:")
    print(result.final_answer)

    print("\nStopped:")
    print(result.stopped)