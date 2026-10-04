import json
import csv
import os

from pyTigerGraph import TigerGraphConnection
from config import Config


Config.validate()

conn = TigerGraphConnection(
    host=Config.TG_HOST,
    graphname=Config.TG_GRAPH_NAME,
    gsqlSecret=Config.TG_SECRET
)

conn.getToken(Config.TG_SECRET)


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json_vertices(filename, vertex_type):
    path = os.path.join(DATA_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    for record in records:
        conn.upsertVertex(
            vertex_type,
            record["id"],
            {"name": record["name"]}
        )

    print(f"Loaded {len(records)} {vertex_type} vertices")


def load_markets():
    path = os.path.join(DATA_DIR, "markets.csv")

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        count = 0

        for row in reader:
            conn.upsertVertex(
                "Market",
                row["id"],
                {"name": row["name"]}
            )
            count += 1

    print(f"Loaded {count} Market vertices")


print("Loading livestock vertices...")

load_json_vertices("symptoms.json", "Symptom")
load_json_vertices("diseases.json", "Disease")
load_json_vertices("treatments.json", "Treatment")
load_json_vertices("outbreaks.json", "Outbreak")
load_markets()

print("Vertex loading completed successfully!")