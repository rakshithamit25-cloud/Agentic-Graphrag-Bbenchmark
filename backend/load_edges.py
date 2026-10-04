from pyTigerGraph import TigerGraphConnection
from config import Config

Config.validate()

conn = TigerGraphConnection(
    host=Config.TG_HOST,
    graphname=Config.TG_GRAPH_NAME,
    gsqlSecret=Config.TG_SECRET
)

edges = [
    # Animal -> Symptom
    ("Animal", "animal_001", "HAS_SYMPTOM", "Symptom", "symptom_001"),
    ("Animal", "animal_001", "HAS_SYMPTOM", "Symptom", "symptom_002"),
    ("Animal", "animal_002", "HAS_SYMPTOM", "Symptom", "symptom_003"),

    # Disease -> Treatment
    ("Disease", "disease_001", "HAS_TREATMENT", "Treatment", "treatment_001"),
    ("Disease", "disease_002", "HAS_TREATMENT", "Treatment", "treatment_002"),

    # Disease -> Outbreak
    ("Disease", "disease_001", "ASSOCIATED_WITH", "Outbreak", "outbreak_001"),
    ("Disease", "disease_002", "ASSOCIATED_WITH", "Outbreak", "outbreak_002"),

    # Outbreak -> Market
    ("Outbreak", "outbreak_001", "AFFECTS", "Market", "market_001"),
    ("Outbreak", "outbreak_002", "AFFECTS", "Market", "market_002"),

    # FactVersion -> FactVersion
    ("FactVersion", "fact_002", "SUPERSEDES", "FactVersion", "fact_001"),
]

for source_type, source_id, edge_type, target_type, target_id in edges:
    conn.upsertEdge(
        source_type,
        source_id,
        edge_type,
        target_type,
        target_id,
        {}
    )

print("Edge data loaded successfully!")