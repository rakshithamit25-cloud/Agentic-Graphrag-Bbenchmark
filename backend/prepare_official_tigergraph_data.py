"""
Prepare Official TigerGraph Data from graph_sample.json.
Converts the deterministic extraction sample (50 documents) into TigerGraph-compatible CSV files.
Strictly adheres to Phase 4 Safety and Schema rules.
Does NOT modify graph_sample.json or corpus.jsonl.
"""

import os
import re
import csv
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
OFFICIAL_DATA_DIR = BASE_DIR / "official_data"
SAMPLE_JSON_PATH = OFFICIAL_DATA_DIR / "graph_sample.json"
TG_DATA_DIR = OFFICIAL_DATA_DIR / "tigergraph"


def clean_val(val):
    """Normalize None to empty string or appropriate representation."""
    if val is None:
        return ""
    return str(val).strip()


def prepare_csv_data():
    TG_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading extraction sample from: {SAMPLE_JSON_PATH}")
    with open(SAMPLE_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Collections for unique vertices and edges
    documents = {}
    events = {}
    games = {}
    sports = {}
    venues = {}
    athletes = {}
    countries = {}

    describes_edges = []
    part_of_games_edges = []
    belongs_to_sport_edges = []
    held_at_edges = []
    won_gold_edges = []
    won_silver_edges = []
    won_bronze_edges = []
    represents_edges = []
    preceded_by_edges = []

    # Map event_id to win_value
    event_win_values = {}

    # 1. Process documents and vertices
    for doc_item in data.get("documents", []):
        doc_id = doc_item["doc_id"]

        for ent in doc_item.get("entities", []):
            eid = ent["id"]
            etype = ent["type"]
            name = ent.get("name", "")
            attrs = ent.get("attributes", {})

            if etype == "Document":
                documents[eid] = {
                    "doc_id": eid,
                    "title": attrs.get("title", name),
                    "url": attrs.get("url", ""),
                    "wikidata_qid": attrs.get("wikidata_qid", ""),
                    "wikipedia_pageid": str(attrs.get("wikipedia_pageid", "")),
                    "approx_tokens": attrs.get("approx_tokens", 0) or 0
                }
            elif etype == "Event":
                w_val = attrs.get("win_value", "")
                event_win_values[eid] = w_val
                events[eid] = {
                    "event_id": eid,
                    "name": name,
                    "sport": attrs.get("sport", ""),
                    "competitors_count": attrs.get("competitors_count", "") if attrs.get("competitors_count") is not None else "",
                    "nations_count": attrs.get("nations_count", "") if attrs.get("nations_count") is not None else "",
                    "date_str": attrs.get("date_str", ""),
                    "win_value": w_val
                }
            elif etype == "OlympicGames":
                games[eid] = {
                    "games_id": eid,
                    "name": name,
                    "year": attrs.get("year", 0) or 0,
                    "season": attrs.get("season", "")
                }
            elif etype == "Sport":
                sports[eid] = {
                    "sport_id": eid,
                    "name": name
                }
            elif etype == "Venue":
                venues[eid] = {
                    "venue_id": eid,
                    "name": name
                }
            elif etype == "Athlete":
                # If already seen, preserve or augment noc
                noc = attrs.get("noc", "")
                if eid in athletes:
                    if not athletes[eid]["noc"] and noc:
                        athletes[eid]["noc"] = noc
                else:
                    athletes[eid] = {
                        "athlete_id": eid,
                        "name": name,
                        "noc": noc
                    }
            elif etype == "Country":
                noc_code = eid  # e.g. "noc_hun"
                country_name = name if name else attrs.get("noc_code", "")
                countries[eid] = {
                    "noc_code": eid,
                    "name": country_name
                }

    # 2. Process relationships
    for doc_item in data.get("documents", []):
        doc_id = doc_item["doc_id"]
        doc_games = None
        doc_prev_year = None

        for rel in doc_item.get("relationships", []):
            rtype = rel.get("relation")
            src = rel.get("source")
            tgt = rel.get("target")
            attrs = rel.get("attributes", {})
            evidence = rel.get("evidence_text", "")

            if rtype == "DESCRIBES":
                # Only load into DESCRIBES if target is an Event
                if tgt in events:
                    describes_edges.append({
                        "source": src,
                        "target": tgt,
                        "source_doc_id": doc_id,
                        "evidence_text": evidence
                    })

            elif rtype == "PART_OF_GAMES":
                year_val = attrs.get("year", 0) or 0
                season_val = attrs.get("season", "")
                doc_games = (tgt, year_val, season_val)
                part_of_games_edges.append({
                    "source": src,
                    "target": tgt,
                    "year": year_val,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "BELONGS_TO_SPORT":
                belongs_to_sport_edges.append({
                    "source": src,
                    "target": tgt,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "HELD_AT":
                date_val = attrs.get("date_str", "")
                held_at_edges.append({
                    "source": src,
                    "target": tgt,
                    "date_str": date_val,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "WON_GOLD":
                noc_val = attrs.get("noc", "")
                win_val = event_win_values.get(src, "")
                won_gold_edges.append({
                    "source": src,
                    "target": tgt,
                    "noc": noc_val,
                    "win_value": win_val,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "WON_SILVER":
                noc_val = attrs.get("noc", "")
                won_silver_edges.append({
                    "source": src,
                    "target": tgt,
                    "noc": noc_val,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "WON_BRONZE":
                noc_val = attrs.get("noc", "")
                won_bronze_edges.append({
                    "source": src,
                    "target": tgt,
                    "noc": noc_val,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "REPRESENTS":
                represents_edges.append({
                    "source": src,
                    "target": tgt,
                    "source_doc_id": doc_id,
                    "evidence_text": evidence
                })

            elif rtype == "PRECEDED_BY_YEAR":
                doc_prev_year = attrs.get("prev_year")

        # Map PRECEDED_BY_YEAR to PRECEDED_BY: OlympicGames -> OlympicGames
        if doc_games and doc_prev_year:
            cur_games_id, cur_year, cur_season = doc_games
            prev_games_id = f"games_{doc_prev_year}_{cur_season.lower()}"
            
            # Ensure target games vertex exists in games dictionary
            if prev_games_id not in games:
                games[prev_games_id] = {
                    "games_id": prev_games_id,
                    "name": f"{doc_prev_year} {cur_season} Olympics",
                    "year": doc_prev_year,
                    "season": cur_season
                }

            preceded_by_edges.append({
                "source": cur_games_id,
                "target": prev_games_id,
                "season": cur_season,
                "source_doc_id": doc_id,
                "evidence_text": f"prev: {doc_prev_year}"
            })

    # Helper function to write CSV
    def write_csv(filename, fieldnames, rows):
        filepath = TG_DATA_DIR / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"  Wrote {len(rows):>4} rows -> {filename}")
        return len(rows)

    print("\n--- Generating Vertex CSVs ---")
    write_csv("documents.csv", ["doc_id", "title", "url", "wikidata_qid", "wikipedia_pageid", "approx_tokens"], list(documents.values()))
    write_csv("events.csv", ["event_id", "name", "sport", "competitors_count", "nations_count", "date_str", "win_value"], list(events.values()))
    write_csv("games.csv", ["games_id", "name", "year", "season"], list(games.values()))
    write_csv("sports.csv", ["sport_id", "name"], list(sports.values()))
    write_csv("venues.csv", ["venue_id", "name"], list(venues.values()))
    write_csv("athletes.csv", ["athlete_id", "name", "noc"], list(athletes.values()))
    write_csv("countries.csv", ["noc_code", "name"], list(countries.values()))

    print("\n--- Generating Edge CSVs ---")
    write_csv("describes.csv", ["source", "target"], describes_edges)
    write_csv("part_of_games.csv", ["source", "target", "year"], part_of_games_edges)
    write_csv("belongs_to_sport.csv", ["source", "target"], belongs_to_sport_edges)
    write_csv("held_at.csv", ["source", "target", "date_str"], held_at_edges)
    write_csv("won_gold.csv", ["source", "target", "noc", "win_value"], won_gold_edges)
    write_csv("won_silver.csv", ["source", "target", "noc"], won_silver_edges)
    write_csv("won_bronze.csv", ["source", "target", "noc"], won_bronze_edges)
    write_csv("represents.csv", ["source", "target"], represents_edges)
    write_csv("preceded_by.csv", ["source", "target", "season"], preceded_by_edges)

    # Traceability export (retains evidence and source_doc_id for auditing)
    traceability_path = TG_DATA_DIR / "edge_traceability.json"
    trace_payload = {
        "describes": describes_edges,
        "part_of_games": part_of_games_edges,
        "belongs_to_sport": belongs_to_sport_edges,
        "held_at": held_at_edges,
        "won_gold": won_gold_edges,
        "won_silver": won_silver_edges,
        "won_bronze": won_bronze_edges,
        "represents": represents_edges,
        "preceded_by": preceded_by_edges
    }
    with open(traceability_path, "w", encoding="utf-8") as f:
        json.dump(trace_payload, f, indent=2, ensure_ascii=False)
    print(f"\nTraceability log saved to: {traceability_path}")

    print("\nCSV generation complete!")


if __name__ == "__main__":
    prepare_csv_data()
