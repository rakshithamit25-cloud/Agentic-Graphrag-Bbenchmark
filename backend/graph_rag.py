from graph_tool import get_livestock_graph, get_disease_by_market
from vector_tool import vector_search
from entity_linker import link_entities


def run_graphrag(question):

    # Detect entities in the question
    entities = link_entities(question)

    disease_id = entities.get("disease_id")
    market = entities.get("market")

    # Convert market name to graph ID
    market_id = None

    if market == "Tamil Nadu Livestock Market":
        market_id = "market_001"

    elif market == "Karnataka Livestock Market":
        market_id = "market_002"

    # If disease is known, query the disease graph
    if disease_id:

        graph_data = get_livestock_graph(disease_id)

    # If only market is known, find disease from market
    elif market_id:

        diseases = get_disease_by_market(market_id)

        if diseases:

            found_disease_id = diseases[0].get("v_id")

            graph_data = get_livestock_graph(
                found_disease_id
            )

        else:

            graph_data = {
                "diseases": [],
                "treatments": [],
                "outbreaks": [],
                "markets": []
            }

    else:

        graph_data = {
            "diseases": [],
            "treatments": [],
            "outbreaks": [],
            "markets": []
        }

    # Vector evidence
    vector_results = vector_search(
        question,
        top_k=3
    )

    return {
        "question": question,
        "graph_evidence": graph_data,
        "vector_evidence": vector_results
    }


if __name__ == "__main__":

    question = (
        "Which treatment is associated with "
        "Pneumonia?"
    )

    result = run_graphrag(question)

    print("\nGraph Evidence:")
    print(result["graph_evidence"])

    print("\nVector Evidence:")
    print(result["vector_evidence"])