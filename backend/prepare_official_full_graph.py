"""
Prepare Official Full Graph Data for all 2,951 documents in corpus.jsonl.
Generates TigerGraph-compatible CSV files in official_data/tigergraph/full/
Adheres strictly to Phase 5 Safety and Schema rules.
Does NOT modify AGRI_EVIDENCE or sample data.
Uses deterministic extraction only (no LLMs, OpenAI, or Ollama).
"""

import os
import re
import csv
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
OFFICIAL_DATA_DIR = BASE_DIR / "official_data"
CORPUS_PATH = OFFICIAL_DATA_DIR / "corpus.jsonl"
TG_FULL_DIR = OFFICIAL_DATA_DIR / "tigergraph" / "full"


def clean_id(text: str) -> str:
    """Normalize text into a clean identifier string."""
    cleaned = re.sub(r"[^\w\s-]", "", text.strip()).strip().lower()
    return re.sub(r"[\s-]+", "_", cleaned)


def parse_infobox(text: str):
    """
    Parse Olympic event infobox or primary infobox from text.
    First checks if [Infobox Olympic event] is present anywhere.
    If not, falls back to the first infobox found.
    """
    m_oly = re.search(r"\[Infobox Olympic event\](.*?)(?=\n\n|\n\[|\Z)", text, re.DOTALL)
    if m_oly:
        box_type = "Olympic event"
        box_body = m_oly.group(1)
    else:
        m_first = re.search(r"\[Infobox ([^\]]+)\](.*?)(?=\n\n|\n\[|\Z)", text, re.DOTALL)
        if not m_first:
            return None
        box_type = m_first.group(1).strip()
        box_body = m_first.group(2)

    fields = {}
    for line in box_body.split("\n"):
        km = re.match(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.+)$", line)
        if km:
            k = km.group(1).strip()
            v = km.group(2).strip()
            fields[k] = {"value": v, "raw_line": line.strip()}

    return {"type": box_type, "fields": fields}


def generate_full_graph_data():
    TG_FULL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading official corpus from: {CORPUS_PATH}")

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

    # Dedup sets for edges to ensure zero duplicates
    seen_describes = set()
    seen_part_of_games = set()
    seen_belongs_to_sport = set()
    seen_held_at = set()
    seen_won_gold = set()
    seen_won_silver = set()
    seen_won_bronze = set()
    seen_represents = set()
    seen_preceded_by = set()

    total_docs = 0
    olympic_docs = 0
    non_olympic_docs = 0

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_docs += 1
            doc = json.loads(line)
            doc_id = doc.get("doc_id")
            title = doc.get("title", "")
            text = doc.get("text", "")

            # 1. Base Document Entity for ALL documents
            documents[doc_id] = {
                "doc_id": doc_id,
                "title": title,
                "url": doc.get("url", "") or "",
                "wikidata_qid": doc.get("wikidata_qid", "") or "",
                "wikipedia_pageid": str(doc.get("wikipedia_pageid", "") or ""),
                "approx_tokens": doc.get("approx_tokens", 0) or 0
            }

            # 2. Check for Olympic event infobox
            infobox = parse_infobox(text)
            if not infobox or infobox["type"] != "Olympic event":
                non_olympic_docs += 1
                continue

            olympic_docs += 1
            fields = infobox["fields"]

            # 3. Extract Event Entity
            event_id = f"event_{doc_id}"
            event_name = fields.get("event", {}).get("value", title)
            sport_name = title.split(" at the ")[0].strip() if " at the " in title else "Olympic Sport"

            comp_str = fields.get("competitors", {}).get("value", "")
            comp_count = 0
            if comp_str:
                cm = re.search(r"\d+", comp_str)
                if cm:
                    comp_count = int(cm.group(0))

            nat_str = fields.get("nations", {}).get("value", "")
            nat_count = 0
            if nat_str:
                nm = re.search(r"\d+", nat_str)
                if nm:
                    nat_count = int(nm.group(0))

            date_val = fields.get("date", {}).get("value") or fields.get("dates", {}).get("value") or ""
            win_val = fields.get("win_value", {}).get("value", "")

            events[event_id] = {
                "event_id": event_id,
                "name": title,
                "sport": sport_name,
                "competitors_count": comp_count if comp_count > 0 else "",
                "nations_count": nat_count if nat_count > 0 else "",
                "date_str": date_val,
                "win_value": win_val
            }

            # Edge: Document -> DESCRIBES -> Event
            edge_key = (doc_id, event_id)
            if edge_key not in seen_describes:
                seen_describes.add(edge_key)
                describes_edges.append({
                    "source": doc_id,
                    "target": event_id,
                    "source_doc_id": doc_id,
                    "evidence_text": f"Document '{title}' describes event '{event_name}'"
                })

            # 4. Extract Sport Entity & BELONGS_TO_SPORT Edge
            sport_id = f"sport_{clean_id(sport_name)}"
            if sport_id not in sports:
                sports[sport_id] = {
                    "sport_id": sport_id,
                    "name": sport_name
                }
            sport_edge_key = (event_id, sport_id)
            if sport_edge_key not in seen_belongs_to_sport:
                seen_belongs_to_sport.add(sport_edge_key)
                belongs_to_sport_edges.append({
                    "source": event_id,
                    "target": sport_id,
                    "source_doc_id": doc_id,
                    "evidence_text": f"Title '{title}' establishes sport '{sport_name}'"
                })

            # 5. Extract OlympicGames Entity & PART_OF_GAMES Edge
            games_val = fields.get("games", {}).get("value", "")
            cur_games_id = None
            cur_season = ""
            cur_year = 0
            if games_val:
                cur_games_id = f"games_{clean_id(games_val)}"
                ym = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", games_val)
                cur_year = int(ym.group(0)) if ym else 0
                cur_season = "Winter" if "winter" in games_val.lower() else "Summer" if "summer" in games_val.lower() else ""
                games_name = f"{games_val} Olympics" if "olympic" not in games_val.lower() else games_val

                if cur_games_id not in games:
                    games[cur_games_id] = {
                        "games_id": cur_games_id,
                        "name": games_name,
                        "year": cur_year,
                        "season": cur_season
                    }

                pog_edge_key = (event_id, cur_games_id)
                if pog_edge_key not in seen_part_of_games:
                    seen_part_of_games.add(pog_edge_key)
                    part_of_games_edges.append({
                        "source": event_id,
                        "target": cur_games_id,
                        "year": cur_year,
                        "source_doc_id": doc_id,
                        "evidence_text": fields["games"]["raw_line"]
                    })

            # 6. Extract Venue Entity & HELD_AT Edge
            venue_val = fields.get("venue", {}).get("value") or fields.get("venues", {}).get("value")
            if venue_val:
                venue_id = f"venue_{clean_id(venue_val)}"
                if venue_id not in venues:
                    venues[venue_id] = {
                        "venue_id": venue_id,
                        "name": venue_val
                    }

                ha_edge_key = (event_id, venue_id)
                if ha_edge_key not in seen_held_at:
                    seen_held_at.add(ha_edge_key)
                    raw_venue_line = fields.get("venue", {}).get("raw_line") or fields.get("venues", {}).get("raw_line", "")
                    held_at_edges.append({
                        "source": event_id,
                        "target": venue_id,
                        "date_str": date_val,
                        "source_doc_id": doc_id,
                        "evidence_text": raw_venue_line
                    })

            # 7. Extract Medalists (Gold, Silver, Bronze)
            for m_type, edge_list, seen_set in [
                ("gold", won_gold_edges, seen_won_gold),
                ("silver", won_silver_edges, seen_won_silver),
                ("bronze", won_bronze_edges, seen_won_bronze)
            ]:
                for suffix in ["", "2", "3"]:
                    f_key = f"{m_type}{suffix}"
                    if f_key in fields:
                        med_val = fields[f_key]["value"].strip()
                        if not med_val:
                            continue
                        noc_key = f"{m_type}NOC{suffix}"
                        noc_val = fields.get(noc_key, {}).get("value", "").strip()

                        ath_id = f"athlete_{clean_id(med_val)}"
                        if ath_id in athletes:
                            if not athletes[ath_id]["noc"] and noc_val:
                                athletes[ath_id]["noc"] = noc_val
                        else:
                            athletes[ath_id] = {
                                "athlete_id": ath_id,
                                "name": med_val,
                                "noc": noc_val
                            }

                        med_edge_key = (event_id, ath_id)
                        if med_edge_key not in seen_set:
                            seen_set.add(med_edge_key)
                            edge_payload = {
                                "source": event_id,
                                "target": ath_id,
                                "noc": noc_val,
                                "source_doc_id": doc_id,
                                "evidence_text": fields[f_key]["raw_line"]
                            }
                            if m_type == "gold":
                                edge_payload["win_value"] = win_val
                            edge_list.append(edge_payload)

                        # Country & REPRESENTS Edge
                        if noc_val:
                            noc_id = f"noc_{clean_id(noc_val)}"
                            if noc_id not in countries:
                                countries[noc_id] = {
                                    "noc_code": noc_id,
                                    "name": noc_val
                                }
                            rep_edge_key = (ath_id, noc_id)
                            if rep_edge_key not in seen_represents:
                                seen_represents.add(rep_edge_key)
                                raw_noc_line = fields.get(noc_key, {}).get("raw_line", "")
                                represents_edges.append({
                                    "source": ath_id,
                                    "target": noc_id,
                                    "source_doc_id": doc_id,
                                    "evidence_text": raw_noc_line
                                })

            # 8. Predecessor Reference: OlympicGames -> PRECEDED_BY -> OlympicGames
            prev_val = fields.get("prev", {}).get("value")
            if prev_val and cur_games_id:
                pym = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", prev_val)
                if pym:
                    prev_year = int(pym.group(0))
                    prev_games_id = f"games_{prev_year}_{cur_season.lower()}"
                    if prev_games_id not in games:
                        games[prev_games_id] = {
                            "games_id": prev_games_id,
                            "name": f"{prev_year} {cur_season} Olympics",
                            "year": prev_year,
                            "season": cur_season
                        }

                    prec_edge_key = (cur_games_id, prev_games_id)
                    if prec_edge_key not in seen_preceded_by:
                        seen_preceded_by.add(prec_edge_key)
                        preceded_by_edges.append({
                            "source": cur_games_id,
                            "target": prev_games_id,
                            "season": cur_season,
                            "source_doc_id": doc_id,
                            "evidence_text": fields["prev"]["raw_line"]
                        })

    # Helper function to write CSV
    def write_csv(filename, fieldnames, rows):
        filepath = TG_FULL_DIR / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"  Wrote {len(rows):>5} rows -> {filename}")
        return len(rows)

    print("\n--- Generating Full Vertex CSVs ---")
    write_csv("documents.csv", ["doc_id", "title", "url", "wikidata_qid", "wikipedia_pageid", "approx_tokens"], list(documents.values()))
    write_csv("events.csv", ["event_id", "name", "sport", "competitors_count", "nations_count", "date_str", "win_value"], list(events.values()))
    write_csv("games.csv", ["games_id", "name", "year", "season"], list(games.values()))
    write_csv("sports.csv", ["sport_id", "name"], list(sports.values()))
    write_csv("venues.csv", ["venue_id", "name"], list(venues.values()))
    write_csv("athletes.csv", ["athlete_id", "name", "noc"], list(athletes.values()))
    write_csv("countries.csv", ["noc_code", "name"], list(countries.values()))

    print("\n--- Generating Full Edge CSVs ---")
    write_csv("describes.csv", ["source", "target"], describes_edges)
    write_csv("part_of_games.csv", ["source", "target", "year"], part_of_games_edges)
    write_csv("belongs_to_sport.csv", ["source", "target"], belongs_to_sport_edges)
    write_csv("held_at.csv", ["source", "target", "date_str"], held_at_edges)
    write_csv("won_gold.csv", ["source", "target", "noc", "win_value"], won_gold_edges)
    write_csv("won_silver.csv", ["source", "target", "noc"], won_silver_edges)
    write_csv("won_bronze.csv", ["source", "target", "noc"], won_bronze_edges)
    write_csv("represents.csv", ["source", "target"], represents_edges)
    write_csv("preceded_by.csv", ["source", "target", "season"], preceded_by_edges)

    # Save Traceability Log with source_doc_id and evidence_text
    traceability_path = TG_FULL_DIR / "edge_traceability.json"
    trace_payload = {
        "metadata": {
            "total_documents": total_docs,
            "olympic_documents": olympic_docs,
            "non_olympic_documents": non_olympic_docs
        },
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

    print("\n=== Full Graph Preparation Summary ===")
    print(f"Total documents processed: {total_docs}")
    print(f"Olympic documents:        {olympic_docs}")
    print(f"Non-Olympic documents:    {non_olympic_docs}")
    print(f"Vertices generated:       {len(documents) + len(events) + len(games) + len(sports) + len(venues) + len(athletes) + len(countries)}")
    print(f"Edges generated:          {len(describes_edges) + len(part_of_games_edges) + len(belongs_to_sport_edges) + len(held_at_edges) + len(won_gold_edges) + len(won_silver_edges) + len(won_bronze_edges) + len(represents_edges) + len(preceded_by_edges)}")


if __name__ == "__main__":
    generate_full_graph_data()
