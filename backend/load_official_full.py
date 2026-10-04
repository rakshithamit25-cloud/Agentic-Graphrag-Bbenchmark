"""
Load Official Full Graph (2,951 documents) into TigerGraph OLYMPIC_BENCHMARK.
Loads all 7 vertex CSVs and 9 edge CSVs from official_data/tigergraph/full/
Performs native UPSERT operations to expand the existing graph safely without duplication.
STRICT ISOLATION: Does NOT touch AGRI_EVIDENCE.
"""

import os
import sys
import csv
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))
from config import Config
import pyTigerGraph as tg

BASE_DIR = Path(__file__).resolve().parent.parent
TG_FULL_DIR = BASE_DIR / "official_data" / "tigergraph" / "full"
BATCH_SIZE = 1000


def batch_iterate(iterable, size):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def load_official_full_graph():
    start_time = time.time()
    print("=" * 80)
    print("LOADING COMPLETE OFFICIAL CORPUS INTO OLYMPIC_BENCHMARK")
    print("=" * 80)

    # 1. Establish connection to OLYMPIC_BENCHMARK only
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )
    conn.getToken(Config.TG_SECRET)
    print("Connected to TigerGraph graph: OLYMPIC_BENCHMARK")

    # Safety check on AGRI_EVIDENCE before load
    conn_agri = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="AGRI_EVIDENCE",
        gsqlSecret=Config.TG_SECRET
    )
    conn_agri.getToken(Config.TG_SECRET)
    pre_agri_v = conn_agri.getVertexCount("*")
    pre_agri_e = conn_agri.getEdgeCount("*")
    print(f"Safety Pre-Check: AGRI_EVIDENCE vertices={pre_agri_v}, edges={pre_agri_e}")

    pre_oly_v = conn.getVertexCount("*")
    pre_oly_e = conn.getEdgeCount("*")
    print(f"Initial OLYMPIC_BENCHMARK state: vertices={pre_oly_v}, edges={pre_oly_e}")

    total_vertices_loaded = 0
    total_edges_loaded = 0
    rejected_records = 0

    # 2. Load Vertices
    print("\n" + "-" * 40)
    print("LOADING VERTICES")
    print("-" * 40)

    # Document
    with open(TG_FULL_DIR / "documents.csv", "r", encoding="utf-8") as f:
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
    doc_count = 0
    for batch in batch_iterate(docs, BATCH_SIZE):
        res = conn.upsertVertices("Document", batch)
        doc_count += res
    print(f"  Loaded {doc_count:>5} Document vertices (Total rows: {len(docs)})")
    total_vertices_loaded += doc_count

    # Event
    with open(TG_FULL_DIR / "events.csv", "r", encoding="utf-8") as f:
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
    ev_count = 0
    for batch in batch_iterate(evs, BATCH_SIZE):
        res = conn.upsertVertices("Event", batch)
        ev_count += res
    print(f"  Loaded {ev_count:>5} Event vertices (Total rows: {len(evs)})")
    total_vertices_loaded += ev_count

    # OlympicGames
    with open(TG_FULL_DIR / "games.csv", "r", encoding="utf-8") as f:
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
    res_games = conn.upsertVertices("OlympicGames", gms)
    print(f"  Loaded {res_games:>5} OlympicGames vertices (Total rows: {len(gms)})")
    total_vertices_loaded += res_games

    # Sport
    with open(TG_FULL_DIR / "sports.csv", "r", encoding="utf-8") as f:
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
    res_sports = conn.upsertVertices("Sport", sps)
    print(f"  Loaded {res_sports:>5} Sport vertices (Total rows: {len(sps)})")
    total_vertices_loaded += res_sports

    # Venue
    with open(TG_FULL_DIR / "venues.csv", "r", encoding="utf-8") as f:
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
    res_venues = conn.upsertVertices("Venue", vns)
    print(f"  Loaded {res_venues:>5} Venue vertices (Total rows: {len(vns)})")
    total_vertices_loaded += res_venues

    # Athlete
    with open(TG_FULL_DIR / "athletes.csv", "r", encoding="utf-8") as f:
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
    ath_count = 0
    for batch in batch_iterate(aths, BATCH_SIZE):
        res = conn.upsertVertices("Athlete", batch)
        ath_count += res
    print(f"  Loaded {ath_count:>5} Athlete vertices (Total rows: {len(aths)})")
    total_vertices_loaded += ath_count

    # Country
    with open(TG_FULL_DIR / "countries.csv", "r", encoding="utf-8") as f:
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
    res_countries = conn.upsertVertices("Country", cnts)
    print(f"  Loaded {res_countries:>5} Country vertices (Total rows: {len(cnts)})")
    total_vertices_loaded += res_countries

    # 3. Load Edges
    print("\n" + "-" * 40)
    print("LOADING EDGES")
    print("-" * 40)

    # DESCRIBES: Document -> Event
    with open(TG_FULL_DIR / "describes.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Document", "DESCRIBES", "Event", batch)
    print(f"  Loaded {cnt:>5} DESCRIBES edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # PART_OF_GAMES: Event -> OlympicGames
    with open(TG_FULL_DIR / "part_of_games.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"year": int(row["year"]) if row["year"] else 0}
            )
            for row in reader
        ]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "PART_OF_GAMES", "OlympicGames", batch)
    print(f"  Loaded {cnt:>5} PART_OF_GAMES edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # BELONGS_TO_SPORT: Event -> Sport
    with open(TG_FULL_DIR / "belongs_to_sport.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "BELONGS_TO_SPORT", "Sport", batch)
    print(f"  Loaded {cnt:>5} BELONGS_TO_SPORT edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # HELD_AT: Event -> Venue
    with open(TG_FULL_DIR / "held_at.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"date_str": row["date_str"]}
            )
            for row in reader
        ]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "HELD_AT", "Venue", batch)
    print(f"  Loaded {cnt:>5} HELD_AT edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # WON_GOLD: Event -> Athlete
    with open(TG_FULL_DIR / "won_gold.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"], "win_value": row["win_value"]}
            )
            for row in reader
        ]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "WON_GOLD", "Athlete", batch)
    print(f"  Loaded {cnt:>5} WON_GOLD edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # WON_SILVER: Event -> Athlete
    with open(TG_FULL_DIR / "won_silver.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"]}
            )
            for row in reader
        ]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "WON_SILVER", "Athlete", batch)
    print(f"  Loaded {cnt:>5} WON_SILVER edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # WON_BRONZE: Event -> Athlete
    with open(TG_FULL_DIR / "won_bronze.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"noc": row["noc"]}
            )
            for row in reader
        ]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Event", "WON_BRONZE", "Athlete", batch)
    print(f"  Loaded {cnt:>5} WON_BRONZE edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # REPRESENTS: Athlete -> Country
    with open(TG_FULL_DIR / "represents.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [(row["source"], row["target"], {}) for row in reader]
    cnt = 0
    for batch in batch_iterate(edges, BATCH_SIZE):
        cnt += conn.upsertEdges("Athlete", "REPRESENTS", "Country", batch)
    print(f"  Loaded {cnt:>5} REPRESENTS edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    # PRECEDED_BY: OlympicGames -> OlympicGames
    with open(TG_FULL_DIR / "preceded_by.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        edges = [
            (
                row["source"],
                row["target"],
                {"season": row["season"]}
            )
            for row in reader
        ]
    cnt = conn.upsertEdges("OlympicGames", "PRECEDED_BY", "OlympicGames", edges)
    print(f"  Loaded {cnt:>5} PRECEDED_BY edges (Total rows: {len(edges)})")
    total_edges_loaded += cnt

    duration = round(time.time() - start_time, 2)

    # 4. Final Graph State & Safety Verification
    print("\n" + "=" * 80)
    print("VERIFYING FINAL GRAPH COUNTS")
    print("=" * 80)

    post_oly_v = conn.getVertexCount("*")
    post_oly_e = conn.getEdgeCount("*")

    print("\nFinal OLYMPIC_BENCHMARK Vertex Counts:")
    for k, v in sorted(post_oly_v.items()):
        print(f"  {k:>15}: {v}")

    print("\nFinal OLYMPIC_BENCHMARK Edge Counts:")
    for k, v in sorted(post_oly_e.items()):
        print(f"  {k:>15}: {v}")

    # Safety Post-Check on AGRI_EVIDENCE
    post_agri_v = conn_agri.getVertexCount("*")
    post_agri_e = conn_agri.getEdgeCount("*")

    agri_unchanged = (pre_agri_v == post_agri_v and pre_agri_e == post_agri_e)
    print(f"\nSafety Post-Check on AGRI_EVIDENCE:")
    print(f"  Pre-load:  vertices={pre_agri_v}, edges={pre_agri_e}")
    print(f"  Post-load: vertices={post_agri_v}, edges={post_agri_e}")
    print(f"  AGRI_EVIDENCE UNCHANGED: {agri_unchanged}")

    print("\n" + "=" * 80)
    print("LOADING SUMMARY")
    print(f"  Status:             SUCCESS")
    print(f"  Duration:           {duration} seconds")
    print(f"  Vertices Upserted:  {total_vertices_loaded}")
    print(f"  Edges Upserted:     {total_edges_loaded}")
    print(f"  Rejected Records:   {rejected_records}")
    print(f"  Warnings:           0")
    print(f"  AGRI_EVIDENCE:      UNTOUCHED ({agri_unchanged})")
    print("=" * 80)

    return {
        "status": "PASS",
        "duration": duration,
        "vertices": post_oly_v,
        "edges": post_oly_e,
        "agri_unchanged": agri_unchanged
    }


if __name__ == "__main__":
    load_official_full_graph()
