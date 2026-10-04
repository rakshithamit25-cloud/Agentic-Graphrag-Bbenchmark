from pyTigerGraph import TigerGraphConnection
from config import Config

Config.validate()

conn = TigerGraphConnection(
    host=Config.TG_HOST,
    graphname=Config.TG_GRAPH_NAME,
    gsqlSecret=Config.TG_SECRET
)

conn.getToken(Config.TG_SECRET)


def get_livestock_graph(disease_id="disease_001"):

    result = conn.runInstalledQuery(
        "disease_market_path",
        {"disease": (disease_id,)}
    )

    output = {
        "diseases": [],
        "treatments": [],
        "outbreaks": [],
        "markets": []
    }

    for block in result:

        if "StartDisease" in block:
            output["diseases"] = block["StartDisease"]

        elif "Treatments" in block:
            output["treatments"] = block["Treatments"]

        elif "Outbreaks" in block:
            output["outbreaks"] = block["Outbreaks"]

        elif "Markets" in block:
            output["markets"] = block["Markets"]

    return output


def get_disease_by_market(market_id):

    result = conn.runInstalledQuery(
        "market_disease_path",
        {"market": (market_id,)}
    )

    for block in result:

        if "Diseases" in block:
            return block["Diseases"]

    return []


if __name__ == "__main__":

    print("\n=== TEST 1: DISEASE TO MARKET ===")

    data = get_livestock_graph("disease_001")

    print("Diseases:")
    print(data["diseases"])

    print("Markets:")
    print(data["markets"])


    print("\n=== TEST 2: MARKET TO DISEASE ===")

    diseases = get_disease_by_market("market_001")

    print("Diseases for market_001:")
    print(diseases)