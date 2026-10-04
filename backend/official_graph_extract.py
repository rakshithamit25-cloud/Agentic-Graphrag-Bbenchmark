"""
Prototype Deterministic Graph Extraction for Hackathon Official Corpus.
Reads corpus.jsonl and extracts entities and relationships based on structured corpus content.
Retains source document IDs and supporting evidence text for every relationship.
Does NOT use LLMs, OpenAI, or Ollama.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
OFFICIAL_DATA_DIR = BASE_DIR / "official_data"
CORPUS_PATH = OFFICIAL_DATA_DIR / "corpus.jsonl"
SAMPLE_OUTPUT_PATH = OFFICIAL_DATA_DIR / "graph_sample.json"


def clean_id(text: str) -> str:
    """Normalize text into a clean identifier string."""
    cleaned = re.sub(r"[^\w\s-]", "", text.strip()).strip().lower()
    return re.sub(r"[\s-]+", "_", cleaned)


def parse_infobox(text: str) -> Optional[Dict[str, Any]]:
    """Parse infobox type and key-value lines from text."""
    m = re.search(r"\[Infobox ([^\]]+)\](.*?)(?=\n\n|\n\[|\Z)", text, re.DOTALL)
    if not m:
        return None

    box_type = m.group(1).strip()
    box_body = m.group(2)
    fields = {}
    lines = box_body.split("\n")
    for line in lines:
        km = re.match(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.+)$", line)
        if km:
            k = km.group(1).strip()
            v = km.group(2).strip()
            fields[k] = {"value": v, "raw_line": line.strip()}

    return {"type": box_type, "fields": fields}


def extract_graph_from_sample(
    sample_size: int = 50,
    corpus_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Extract entities and relationships deterministically from a sample of corpus documents.
    """
    path = Path(corpus_path) if corpus_path else CORPUS_PATH
    out_file = Path(output_path) if output_path else SAMPLE_OUTPUT_PATH

    documents_data = []
    all_entities = {}
    all_relationships = []

    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= sample_size:
                break
            line_str = line.strip()
            if not line_str:
                continue
            doc = json.loads(line_str)

            doc_id = doc.get("doc_id")
            title = doc.get("title", "")
            text = doc.get("text", "")

            doc_entities = []
            doc_relationships = []

            # 1. Base Document Entity
            doc_ent = {
                "id": doc_id,
                "type": "Document",
                "name": title,
                "attributes": {
                    "doc_id": doc_id,
                    "title": title,
                    "url": doc.get("url"),
                    "wikidata_qid": doc.get("wikidata_qid"),
                    "wikipedia_pageid": doc.get("wikipedia_pageid"),
                    "approx_tokens": doc.get("approx_tokens"),
                }
            }
            doc_entities.append(doc_ent)
            all_entities[doc_id] = doc_ent

            # 2. Infobox-driven extraction
            infobox = parse_infobox(text)

            if infobox and infobox["type"] == "Olympic event":
                fields = infobox["fields"]

                # Extract Event Entity
                event_name = fields.get("event", {}).get("value", title)
                sport_name = title.split(" at the ")[0].strip() if " at the " in title else "Olympic Sport"

                # Parse competitors and nations counts
                comp_str = fields.get("competitors", {}).get("value", "")
                nat_str = fields.get("nations", {}).get("value", "")
                
                comp_count = None
                if comp_str:
                    comp_match = re.search(r"\d+", comp_str)
                    if comp_match:
                        comp_count = int(comp_match.group(0))

                nat_count = None
                if nat_str:
                    nat_match = re.search(r"\d+", nat_str)
                    if nat_match:
                        nat_count = int(nat_match.group(0))

                date_val = fields.get("date", {}).get("value") or fields.get("dates", {}).get("value") or ""

                event_id = f"event_{doc_id}"
                event_ent = {
                    "id": event_id,
                    "type": "Event",
                    "name": title,
                    "attributes": {
                        "sub_event": event_name,
                        "sport": sport_name,
                        "competitors_count": comp_count,
                        "nations_count": nat_count,
                        "date_str": date_val,
                        "venue": fields.get("venue", {}).get("value", ""),
                        "win_value": fields.get("win_value", {}).get("value", ""),
                    }
                }
                doc_entities.append(event_ent)
                all_entities[event_id] = event_ent

                # Relationship: Document -> DESCRIBES -> Event
                doc_rel = {
                    "source_doc_id": doc_id,
                    "source": doc_id,
                    "source_type": "Document",
                    "relation": "DESCRIBES",
                    "target": event_id,
                    "target_type": "Event",
                    "attributes": {},
                    "evidence_text": f"Document '{title}' describes event '{event_name}'"
                }
                doc_relationships.append(doc_rel)
                all_relationships.append(doc_rel)

                # Extract OlympicGames Entity & Relationship
                games_val = fields.get("games", {}).get("value", "")
                if games_val:
                    games_id = f"games_{clean_id(games_val)}"
                    year_match = re.search(r"\b(19\d\d|20\d\d)\b", games_val)
                    year = int(year_match.group(0)) if year_match else None
                    season = "Winter" if "winter" in games_val.lower() else "Summer" if "summer" in games_val.lower() else ""

                    games_ent = {
                        "id": games_id,
                        "type": "OlympicGames",
                        "name": f"{games_val} Olympics" if "olympic" not in games_val.lower() else games_val,
                        "attributes": {"year": year, "season": season, "raw_games": games_val}
                    }
                    doc_entities.append(games_ent)
                    all_entities[games_id] = games_ent

                    rel_games = {
                        "source_doc_id": doc_id,
                        "source": event_id,
                        "source_type": "Event",
                        "relation": "PART_OF_GAMES",
                        "target": games_id,
                        "target_type": "OlympicGames",
                        "attributes": {"year": year, "season": season},
                        "evidence_text": fields["games"]["raw_line"]
                    }
                    doc_relationships.append(rel_games)
                    all_relationships.append(rel_games)

                # Extract Sport Entity & Relationship
                sport_id = f"sport_{clean_id(sport_name)}"
                sport_ent = {
                    "id": sport_id,
                    "type": "Sport",
                    "name": sport_name,
                    "attributes": {}
                }
                doc_entities.append(sport_ent)
                all_entities[sport_id] = sport_ent

                rel_sport = {
                    "source_doc_id": doc_id,
                    "source": event_id,
                    "source_type": "Event",
                    "relation": "BELONGS_TO_SPORT",
                    "target": sport_id,
                    "target_type": "Sport",
                    "attributes": {},
                    "evidence_text": f"Title '{title}' establishes sport '{sport_name}'"
                }
                doc_relationships.append(rel_sport)
                all_relationships.append(rel_sport)

                # Extract Venue Entity & Relationship
                venue_val = fields.get("venue", {}).get("value")
                if venue_val:
                    venue_id = f"venue_{clean_id(venue_val)}"
                    venue_ent = {
                        "id": venue_id,
                        "type": "Venue",
                        "name": venue_val,
                        "attributes": {}
                    }
                    doc_entities.append(venue_ent)
                    all_entities[venue_id] = venue_ent

                    rel_venue = {
                        "source_doc_id": doc_id,
                        "source": event_id,
                        "source_type": "Event",
                        "relation": "HELD_AT",
                        "target": venue_id,
                        "target_type": "Venue",
                        "attributes": {"date_str": date_val},
                        "evidence_text": fields["venue"]["raw_line"]
                    }
                    doc_relationships.append(rel_venue)
                    all_relationships.append(rel_venue)

                # Extract Medalists (Gold, Silver, Bronze)
                for medal_type in ["gold", "silver", "bronze"]:
                    med_field = fields.get(medal_type)
                    if med_field:
                        raw_med = med_field["value"]
                        noc_field = fields.get(f"{medal_type}NOC")
                        noc_code = noc_field["value"] if noc_field else ""

                        athlete_id = f"athlete_{clean_id(raw_med)}"
                        ath_ent = {
                            "id": athlete_id,
                            "type": "Athlete",
                            "name": raw_med,
                            "attributes": {"noc": noc_code}
                        }
                        doc_entities.append(ath_ent)
                        all_entities[athlete_id] = ath_ent

                        rel_med = {
                            "source_doc_id": doc_id,
                            "source": event_id,
                            "source_type": "Event",
                            "relation": f"WON_{medal_type.upper()}",
                            "target": athlete_id,
                            "target_type": "Athlete",
                            "attributes": {"medal": medal_type, "noc": noc_code},
                            "evidence_text": med_field["raw_line"]
                        }
                        doc_relationships.append(rel_med)
                        all_relationships.append(rel_med)

                        # Country Entity & Relationship
                        if noc_code:
                            noc_id = f"noc_{clean_id(noc_code)}"
                            noc_ent = {
                                "id": noc_id,
                                "type": "Country",
                                "name": noc_code,
                                "attributes": {"noc_code": noc_code}
                            }
                            doc_entities.append(noc_ent)
                            all_entities[noc_id] = noc_ent

                            rel_noc = {
                                "source_doc_id": doc_id,
                                "source": athlete_id,
                                "source_type": "Athlete",
                                "relation": "REPRESENTS",
                                "target": noc_id,
                                "target_type": "Country",
                                "attributes": {},
                                "evidence_text": noc_field["raw_line"] if noc_field else ""
                            }
                            doc_relationships.append(rel_noc)
                            all_relationships.append(rel_noc)

                # Previous / Next references for Temporal Links
                prev_val = fields.get("prev", {}).get("value")
                if prev_val and prev_val.isdigit():
                    rel_prev = {
                        "source_doc_id": doc_id,
                        "source": event_id,
                        "source_type": "Event",
                        "relation": "PRECEDED_BY_YEAR",
                        "target": f"year_{prev_val}",
                        "target_type": "TemporalReference",
                        "attributes": {"prev_year": int(prev_val)},
                        "evidence_text": fields["prev"]["raw_line"]
                    }
                    doc_relationships.append(rel_prev)
                    all_relationships.append(rel_prev)

            elif infobox:
                # Other Infobox types (e.g. film, album, company)
                btype = infobox["type"]
                fields = infobox["fields"]
                entity_id = f"{clean_id(btype)}_{doc_id}"
                gen_ent = {
                    "id": entity_id,
                    "type": btype.title().replace(" ", ""),
                    "name": title,
                    "attributes": {k: v["value"] for k, v in fields.items()}
                }
                doc_entities.append(gen_ent)
                all_entities[entity_id] = gen_ent

                doc_rel = {
                    "source_doc_id": doc_id,
                    "source": doc_id,
                    "source_type": "Document",
                    "relation": "DESCRIBES",
                    "target": entity_id,
                    "target_type": btype.title().replace(" ", ""),
                    "attributes": {},
                    "evidence_text": f"Document '{title}' describes {btype} entity"
                }
                doc_relationships.append(doc_rel)
                all_relationships.append(doc_rel)

            documents_data.append({
                "doc_id": doc_id,
                "title": title,
                "entities_count": len(doc_entities),
                "relationships_count": len(doc_relationships),
                "entities": doc_entities,
                "relationships": doc_relationships,
            })

    output_payload = {
        "metadata": {
            "sample_size": len(documents_data),
            "total_unique_entities": len(all_entities),
            "total_relationships": len(all_relationships),
        },
        "documents": documents_data
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    return output_payload


if __name__ == "__main__":
    print("Running official graph extraction prototype on 50 documents...")
    res = extract_graph_from_sample(sample_size=50)
    meta = res["metadata"]
    print(f"Extraction Complete!")
    print(f"  Documents inspected:    {meta['sample_size']}")
    print(f"  Total unique entities:  {meta['total_unique_entities']}")
    print(f"  Total relationships:    {meta['total_relationships']}")
    print(f"  Output saved to:        {SAMPLE_OUTPUT_PATH}")
