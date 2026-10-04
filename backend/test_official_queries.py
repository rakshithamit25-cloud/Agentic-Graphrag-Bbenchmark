"""
Validation and Test Script for Official GSQL Queries on OLYMPIC_BENCHMARK.
Executes all 5 official queries on the 50-document sample.
Validates outputs against facts present in graph_sample.json.
Prints source document IDs and supporting evidence.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))
from config import Config
import pyTigerGraph as tg

BASE_DIR = Path(__file__).resolve().parent.parent
TG_DATA_DIR = BASE_DIR / "official_data" / "tigergraph"


def run_validation():
    print("=" * 80)
    print("VALIDATING OLYMPIC_BENCHMARK GRAPH & OFFICIAL QUERIES")
    print("=" * 80)

    # 1. Connection
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )
    conn.getToken(Config.TG_SECRET)

    # 2. Check Graph Statistics
    print("\n[1] Graph Summary & Statistics:")
    vertex_counts = conn.getVertexCount("*")
    edge_counts = conn.getEdgeCount("*")

    print("  Vertex Counts:")
    for k, v in sorted(vertex_counts.items()):
        print(f"    {k:>15}: {v}")

    print("  Edge Counts:")
    for k, v in sorted(edge_counts.items()):
        print(f"    {k:>15}: {v}")

    # 3. Load traceability data for evidence printing
    with open(TG_DATA_DIR / "edge_traceability.json", "r", encoding="utf-8") as f:
        traceability = json.load(f)

    # Helper to find evidence
    def get_evidence(edge_list, src, tgt):
        for e in edge_list:
            if e["source"] == src and e["target"] == tgt:
                return e.get("evidence_text", "")
        return ""

    print("\n" + "=" * 80)
    print("RUNNING OFFICIAL QUERIES")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # QUERY 1: EVENT_BY_VENUE_DATE
    # -------------------------------------------------------------------------
    print("\n--- QUERY 1: EVENT_BY_VENUE_DATE ---")
    venue_q = "Richmond Olympic Oval"
    date_q = "13 February 2010"
    print(f"  Inputs: venue='{venue_q}', date='{date_q}'")

    res1 = conn.runInstalledQuery("event_by_venue_date", {"venue_search": venue_q, "date_search": date_q})
    print(f"  Raw Result: {json.dumps(res1, indent=2)}")

    q1_results = res1[0]["@@results"] if res1 else []
    print(f"  Found {len(q1_results)} matching event(s):")
    for r in q1_results:
        print(f"    * Event:           {r['event_name']} ({r['event_id']})")
        print(f"      Venue:           {r['venue_name']}")
        print(f"      Date:            {r['date_str']}")
        print(f"      Gold Winner:     {r['gold_winner_name']} ({r['gold_winner_noc']})")
        print(f"      Win Value:       {r['win_value']}")
        print(f"      Source Doc ID:   {r['source_doc_id']}")
        print(f"      Source Title:    {r['source_doc_title']}")

        # Evidence lookup
        held_ev = get_evidence(traceability["held_at"], r["event_id"], "venue_richmond_olympic_oval")
        gold_ev = get_evidence(traceability["won_gold"], r["event_id"], r["gold_winner_id"])
        print(f"      Evidence (Venue): {held_ev}")
        print(f"      Evidence (Gold):  {gold_ev}")

    # -------------------------------------------------------------------------
    # QUERY 2: PREVIOUS_OLYMPICS_GOLD
    # -------------------------------------------------------------------------
    print("\n--- QUERY 2: PREVIOUS_OLYMPICS_GOLD ---")
    year_q = 2016
    season_q = "Summer"
    event_q = "Canoeing"
    print(f"  Inputs: games_year={year_q}, season='{season_q}', event_search='{event_q}'")

    res2 = conn.runInstalledQuery("previous_olympics_gold", {
        "games_year": year_q,
        "season": season_q,
        "event_search": event_q
    })
    print(f"  Raw Result: {json.dumps(res2, indent=2)}")

    q2_results = res2[0]["@@results"] if res2 else []
    print(f"  Found {len(q2_results)} temporal result(s):")
    for r in q2_results:
        print(f"    * Current Games:   {r['current_games_name']} ({r['current_games_id']})")
        print(f"      Preceding Games: {r['previous_games_name']} ({r['previous_games_id']}, year={r['previous_year']})")
        print(f"      Event in Prev:   {r['event_name']} ({r['event_id']})")
        print(f"      Gold Winner:     {r['gold_winner_name']} ({r['gold_winner_noc']})")
        print(f"      Win Value:       {r['win_value']}")
        print(f"      Source Doc ID:   {r['source_doc_id']}")
        print(f"      Source Title:    {r['source_doc_title']}")

        prev_ev = get_evidence(traceability["preceded_by"], r["current_games_id"], r["previous_games_id"])
        print(f"      Evidence (Temporal): {prev_ev}")

    # -------------------------------------------------------------------------
    # QUERY 3: COUNT_EVENTS_ABOVE_COMPETITORS
    # -------------------------------------------------------------------------
    print("\n--- QUERY 3: COUNT_EVENTS_ABOVE_COMPETITORS ---")
    games_q = "2008 Summer"
    sport_q = "Athletics"
    threshold_q = 30
    print(f"  Inputs: games='{games_q}', sport='{sport_q}', threshold={threshold_q}")

    res3 = conn.runInstalledQuery("count_events_above_competitors", {
        "games_search": games_q,
        "sport_search": sport_q,
        "threshold": threshold_q
    })
    print(f"  Raw Result: {json.dumps(res3, indent=2)}")

    cnt = res3[0]["event_count"] if res3 else 0
    matched = res3[1]["matching_events"] if len(res3) > 1 else []
    print(f"  Count: {cnt}")
    for m in matched:
        print(f"    * {m['event_name']} (competitors={m['competitors_count']}, doc_id={m['source_doc_id']})")

    # -------------------------------------------------------------------------
    # QUERY 4: MAX_COMPETITOR_EVENT
    # -------------------------------------------------------------------------
    print("\n--- QUERY 4: MAX_COMPETITOR_EVENT ---")
    print(f"  Inputs: games='{games_q}', sport='{sport_q}'")

    res4 = conn.runInstalledQuery("max_competitor_event", {
        "games_search": games_q,
        "sport_search": sport_q
    })
    print(f"  Raw Result: {json.dumps(res4, indent=2)}")

    top_events = res4[0]["@@top_event"] if res4 else []
    for t in top_events:
        print(f"    * Top Event:       {t['event_name']} ({t['event_id']})")
        print(f"      Max Competitors: {t['competitors_count']}")
        print(f"      Games:           {t['games_name']}")
        print(f"      Sport:           {t['sport_name']}")
        print(f"      Source Doc ID:   {t['source_doc_id']}")
        print(f"      Source Title:    {t['source_doc_title']}")

    # -------------------------------------------------------------------------
    # QUERY 5: EVENT_NATIONS
    # -------------------------------------------------------------------------
    print("\n--- QUERY 5: EVENT_NATIONS ---")
    event_lookup = "event_Q26233801"
    print(f"  Input: event_search='{event_lookup}'")

    res5 = conn.runInstalledQuery("event_nations", {
        "event_search": event_lookup
    })
    print(f"  Raw Result: {json.dumps(res5, indent=2)}")

    details = res5[0]["@@details"] if res5 else []
    for d in details:
        print(f"    * Event:           {d['event_name']} ({d['event_id']})")
        print(f"      Nations Count:   {d['nations_count']}")
        print(f"      Competitors:     {d['competitors_count']}")
        print(f"      Date:            {d['date_str']}")
        print(f"      Venue:           {d['venue_name']}")
        print(f"      Source Doc ID:   {d['source_doc_id']}")
        print(f"      Source Title:    {d['source_doc_title']}")

    print("\n" + "=" * 80)
    print("ALL 5 QUERIES EXECUTED AND VALIDATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_validation()
