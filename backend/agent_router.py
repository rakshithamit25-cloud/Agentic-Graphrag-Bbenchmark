from agent_state import AgentState


def understand_question(state):

    """
    Determine what information is required
    to answer the user's question.
    """

    question = state.question.lower()

    state.required_information = []

    if "which disease" in question:
        state.set_required_information("disease")

    if "which outbreak" in question:
        state.set_required_information("outbreak")

    if "which market" in question:
        state.set_required_information("market")

    if "treatment" in question:
        state.set_required_information("treatment")

    return state.required_information


def graph_has_required_information(state):

    """
    Check whether the graph already contains
    the information required by the question.
    """

    graph = state.graph_evidence

    if not graph:
        return False

    required = state.required_information

    if "disease" in required:
        if graph.get("diseases"):
            return True

    if "outbreak" in required:
        if graph.get("outbreaks"):
            return True

    if "market" in required:
        if graph.get("markets"):
            return True

    if "treatment" in required:
        if graph.get("treatments"):
            return True

    return False


def vector_has_evidence(state):

    """
    Check whether document/vector evidence
    has been retrieved.
    """

    return bool(state.vector_evidence)


def decide_next_action(state):

    """
    Adaptive Agentic GraphRAG router.

    The agent chooses the next action according to:

    1. What the question requires
    2. What evidence already exists
    3. Which tools were already used
    4. Whether evidence needs evaluation
    5. Whether the agent has enough confidence
    """

    # --------------------------------------------------
    # STEP 1: Understand the question
    # --------------------------------------------------

    if not state.required_information:

        understand_question(state)

    # --------------------------------------------------
    # STEP 2: Stop if enough evidence exists
    # --------------------------------------------------

    if state.should_stop():

        return "STOP"

    # --------------------------------------------------
    # STEP 3: If graph has not been investigated,
    # investigate the graph.
    # --------------------------------------------------

    if not state.has_action("GRAPH") and not state.has_action(
        "MARKET_GRAPH"
    ):

        return "GRAPH"

    # --------------------------------------------------
    # STEP 4: If graph was searched but required
    # information is still missing, use vector evidence.
    # --------------------------------------------------

    graph_sufficient = graph_has_required_information(state)

    if (
        not graph_sufficient
        and not vector_has_evidence(state)
    ):

        return "VECTOR"

    # --------------------------------------------------
    # STEP 5: If graph evidence exists but document
    # evidence has not been checked, retrieve documents.
    # --------------------------------------------------

    if (
        graph_sufficient
        and not vector_has_evidence(state)
    ):

        return "VECTOR"

    # --------------------------------------------------
    # STEP 6: If both evidence sources exist,
    # evaluate them.
    # --------------------------------------------------

    if (
        state.graph_evidence
        and state.vector_evidence
        and not state.evidence_evaluated
    ):

        return "EVALUATE"

    # --------------------------------------------------
    # STEP 7: If information is still missing,
    # perform another investigation.
    # --------------------------------------------------

    if state.missing_information:

        if not state.has_action("VECTOR"):

            return "VECTOR"

    # --------------------------------------------------
    # STEP 8: Final fallback
    # --------------------------------------------------

    if state.graph_evidence or state.vector_evidence:

        return "EVALUATE"

    return "STOP"


if __name__ == "__main__":

    state = AgentState(
        "Which disease is associated with "
        "the Tamil Nadu livestock market?"
    )

    print("Required information:")

    understand_question(state)

    print(state.required_information)

    print("\nFirst action:")
    print(decide_next_action(state))