from pyTigerGraph import TigerGraphConnection
from config import Config


def connect_to_tigergraph():
    conn = TigerGraphConnection(
        host=Config.TG_HOST,
        graphname=Config.TG_GRAPH_NAME,
        gsqlSecret=Config.TG_SECRET
    )

    conn.getToken(Config.TG_SECRET)

    print("TigerGraph connection successful!")
    return conn


if __name__ == "__main__":
    Config.validate()
    connect_to_tigergraph()