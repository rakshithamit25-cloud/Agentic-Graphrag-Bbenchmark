"""
Load Official 50-Document Sample into TigerGraph OLYMPIC_BENCHMARK graph.
Loads all 7 vertex CSVs and 9 edge CSVs generated from graph_sample.json.
Completely isolated from AGRI_EVIDENCE.
"""

import os
import csv
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))
from config import Config
import pyTigerGraph as tg

BASE_DIR = Path(__file__).resolve().parent.parent
TG_DATA_DIR = BASE_DIR / "official_data" / "tigergraph"


def load_official_sample():
    print("==================================================")
    print("LOADING 50-DOCUMENT SAMPLE INTO OLYMPIC_BENCHMARK")
    print("==================================================")

    # 1. Establish connection to OLYMPIC_BENCHMARK only
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )
    conn.getToken(Config.TG_SECRET)
    print("Connected to TigerGraph graph: OLYMPIC_BENCHMARK")

    # 2. Load Vertices
    print("\n--- Loading Vertices ---")

    # Document
    with open(TG_DATA_DIR / "documents.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        docs = [
            (
                row["doc_id"],
                {
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "url": row["url"],
                    "wikidata_qid": row["wikidata_qid"],
                    "wikipedia_pageid": row["wikipedia_pageid"],
                    "approx_tokens": int(row["approx_tokens"]) if row["approx_tokens"] else 0
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Document", docs)
        print(f"Loaded {res} Document vertices")

    # Event
    with open(TG_DATA_DIR / "events.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        evs = [
            (
                row["event_id"],
                {
                    "event_id": row["event_id"],
                    "name": row["name"],
                    "sport": row["sport"],
                    "competitors_count": int(row["competitors_count"]) if row["competitors_count"] else 0,
                    "nations_count": int(row["nations_count"]) if row["nations_count"] else 0,
                    "date_str": row["date_str"],
                    "win_value": row["win_value"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Event", evs)
        print(f"Loaded {res} Event vertices")

    # OlympicGames
    with open(TG_DATA_DIR / "games.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gms = [
            (
                row["games_id"],
                {
                    "games_id": row["games_id"],
                    "name": row["name"],
                    "year": int(row["year"]) if row["year"] else 0,
                    "season": row["season"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("OlympicGames", gms)
        print(f"Loaded {res} OlympicGames vertices")

    # Sport
    with open(TG_DATA_DIR / "sports.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sps = [
            (
                row["sport_id"],
                {
                    "sport_id": row["sport_id"],
                    "name": row["name"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Sport", sps)
        print(f"Loaded {res} Sport vertices")

    # Venue
    with open(TG_DATA_DIR / "venues.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        vns = [
            (
                row["venue_id"],
                {
                    "venue_id": row["venue_id"],
                    "name": row["name"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Venue", vns)
        print(f"Loaded {res} Venue vertices")

    # Athlete
    with open(TG_DATA_DIR / "athletes.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        aths = [
            (
                row["athlete_id"],
                {
                    "athlete_id": row["athlete_id"],
                    "name": row["name"],
                    "noc": row["noc"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Athlete", aths)
        print(f"Loaded {res} Athlete vertices")

    # Country
    with open(TG_DATA_DIR / "countries.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cnts = [
            (
                row["noc_code"],
                {
                    "noc_code": row["noc_code"],
                    "name": row["name"]
                }
            )
            for row in reader
        ]
        res = conn.upsertVertices("Country", cnts)
        print(f"Loaded {res} Country vertices")

    # 3. Load Edges
    print("\n--- Loading Edges ---")

    # DESCRIBES: Document -> Event
    with open(TG_DATA_DIR / "describes.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
        res = conn.upsertEdges("Document", "DESCRIBES", "Event", edges)
        print(f"Loaded {res} DESCRIBES edges")

    # PART_OF_GAMES: Event -> OlympicGames
    with open(TG_DATA_DIR / "part_of_games.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"year": int(row["year"]) if row["year"] else 0}
            )
            for row in reader
        ]
        res = conn.upsertEdges("Event", "PART_OF_GAMES", "OlympicGames", edges)
        print(f"Loaded {res} PART_OF_GAMES edges")

    # BELONGS_TO_SPORT: Event -> Sport
    with open(TG_DATA_DIR / "belongs_to_sport.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
        res = conn.upsertEdges("Event", "BELONGS_TO_SPORT", "Sport", edges)
        print(f"Loaded {res} BELONGS_TO_SPORT edges")

    # HELD_AT: Event -> Venue
    with open(TG_DATA_DIR / "held_at.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"date_str": row["date_str"]}
            )
            for row in reader
        ]
        res = conn.upsertEdges("Event", "HELD_AT", "Venue", edges)
        print(f"Loaded {res} HELD_AT edges")

    # WON_GOLD: Event -> Athlete
    with open(TG_DATA_DIR / "won_gold.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"], "win_value": row["win_value"]}
            )
            for row in reader
        ]
        res = conn.upsertEdges("Event", "WON_GOLD", "Athlete", edges)
        print(f"Loaded {res} WON_GOLD edges")

    # WON_SILVER: Event -> Athlete
    with open(TG_DATA_DIR / "won_silver.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"]}
            )
            for row in reader
        ]
        res = conn.upsertEdges("Event", "WON_SILVER", "Athlete", edges)
        print(f"Loaded {res} WON_SILVER edges")

    # WON_BRONZE: Event -> Athlete
    with open(TG_DATA_DIR / "won_bronze.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"]}
            )
            for row in reader
        ]
        res = conn.upsertEdges("Event", "WON_BRONZE", "Athlete", edges)
        print(f"Loaded {res} WON_BRONZE edges")

    # REPRESENTS: Athlete -> Country
    with open(TG_DATA_DIR / "represents.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
        res = conn.upsertEdges("Athlete", "REPRESENTS", "Country", edges)
        print(f"Loaded {res} REPRESENTS edges")

    # PRECEDED_BY: OlympicGames -> OlympicGames
    with open(TG_DATA_DIR / "preceded_by.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"season": row["season"]}
            )
            for row in reader
        ]
        res = conn.upsertEdges("OlympicGames", "PRECEDED_BY", "OlympicGames", edges)
        print(f"Loaded {res} PRECEDED_BY edges")

    print("\n==================================================")
    print("SAMPLE LOADING COMPLETED SUCCESSFULLY")
    print("==================================================")


if __name__ == "__main__":
    load_official_sample()
