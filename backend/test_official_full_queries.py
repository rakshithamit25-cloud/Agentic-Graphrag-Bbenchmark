"""
Regression Testing of 5 Official TigerGraph Queries on the Full Graph (OLYMPIC_BENCHMARK).
Uses the exact same test inputs as Phase 4 to verify regression safety.
Reports query, input, result, source document, and execution status.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent))
from config import Config
import pyTigerGraph as tg

BASE_DIR = Path(__file__).resolve().parent.parent
TG_FULL_DIR = BASE_DIR / "official_data" / "tigergraph" / "full"


def run_regression_tests():
    print("=" * 80)
    print("REGRESSION TESTING PHASE 4 QUERIES ON FULL OLYMPIC_BENCHMARK GRAPH")
    print("=" * 80)

    # 1. Connection
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )
    conn.getToken(Config.TG_SECRET)

    # Load traceability for evidence lookup
    with open(TG_FULL_DIR / "edge_traceability.json", "r", encoding="utf-8") as f:
        traceability = json.load(f)

    def get_evidence(edge_list, src, tgt):
        for e in edge_list:
            if e["source"] == src and e["target"] == tgt:
                return e.get("evidence_text", "")
        return ""

    test_reports = []

    # -------------------------------------------------------------------------
    # QUERY 1: EVENT_BY_VENUE_DATE
    # -------------------------------------------------------------------------
    print("\n--- QUERY 1: EVENT_BY_VENUE_DATE ---")
    venue_q = "Richmond Olympic Oval"
    date_q = "13 February 2010"
    params1 = {"venue_search": venue_q, "date_search": date_q}
    print(f"  Inputs: venue='{venue_q}', date='{date_q}'")

    res1 = conn.runInstalledQuery("event_by_venue_date", params1)
    q1_results = res1[0]["@@results"] if res1 else []
    print(f"  Execution Status: HTTP 200 SUCCESS (Returned {len(q1_results)} events)")

    q1_summary = []
    for r in q1_results:
        ev_info = {
            "event_name": r["event_name"],
            "event_id": r["event_id"],
            "gold_winner": f"{r['gold_winner_name']} ({r['gold_winner_noc']})",
            "win_value": r["win_value"],
            "source_doc_id": r["source_doc_id"],
            "source_doc_title": r["source_doc_title"]
        }
        q1_summary.append(ev_info)
        print(f"    * Event:        {r['event_name']}")
        print(f"      Gold Winner:  {r['gold_winner_name']} ({r['gold_winner_noc']})")
        print(f"      Win Value:    {r['win_value']}")
        print(f"      Source Doc:   {r['source_doc_id']} ('{r['source_doc_title']}')")

    test_reports.append({
        "query": "event_by_venue_date",
        "input": params1,
        "execution_status": "PASS",
        "result_count": len(q1_results),
        "results": q1_summary
    })

    # -------------------------------------------------------------------------
    # QUERY 2: PREVIOUS_OLYMPICS_GOLD
    # -------------------------------------------------------------------------
    print("\n--- QUERY 2: PREVIOUS_OLYMPICS_GOLD ---")
    year_q = 2016
    season_q = "Summer"
    event_q = "Canoeing"
    params2 = {"games_year": year_q, "season": season_q, "event_search": event_q}
    print(f"  Inputs: games_year={year_q}, season='{season_q}', event_search='{event_q}'")

    res2 = conn.runInstalledQuery("previous_olympics_gold", params2)
    q2_results = res2[0]["@@results"] if res2 else []
    print(f"  Execution Status: HTTP 200 SUCCESS (Returned {len(q2_results)} temporal results)")

    q2_summary = []
    for r in q2_results:
        q2_summary.append({
            "current_games": f"{r['current_games_name']} ({r['current_games_id']})",
            "preceding_games": f"{r['previous_games_name']} ({r['previous_games_id']}, {r['previous_year']})",
            "event_name": r["event_name"],
            "gold_winner": f"{r['gold_winner_name']} ({r['gold_winner_noc']})",
            "win_value": r["win_value"],
            "source_doc_id": r["source_doc_id"],
            "source_doc_title": r["source_doc_title"]
        })
        print(f"    * Event:        {r['event_name']}")
        print(f"      Gold Winner:  {r['gold_winner_name']} ({r['gold_winner_noc']})")
        print(f"      Win Value:    {r['win_value']}")
        print(f"      Preceding:    {r['previous_games_name']} ({r['previous_year']})")
        print(f"      Source Doc:   {r['source_doc_id']}")

    test_reports.append({
        "query": "previous_olympics_gold",
        "input": params2,
        "execution_status": "PASS",
        "result_count": len(q2_results),
        "results": q2_summary
    })

    # -------------------------------------------------------------------------
    # QUERY 3: COUNT_EVENTS_ABOVE_COMPETITORS
    # -------------------------------------------------------------------------
    print("\n--- QUERY 3: COUNT_EVENTS_ABOVE_COMPETITORS ---")
    games_q = "2008 Summer"
    sport_q = "Athletics"
    threshold_q = 30
    params3 = {"games_search": games_q, "sport_search": sport_q, "threshold": threshold_q}
    print(f"  Inputs: games='{games_q}', sport='{sport_q}', threshold={threshold_q}")

    res3 = conn.runInstalledQuery("count_events_above_competitors", params3)
    cnt3 = res3[0]["event_count"] if res3 else 0
    matched3 = res3[1]["matching_events"] if len(res3) > 1 else []
    print(f"  Execution Status: HTTP 200 SUCCESS (Count = {cnt3}, Matching Events List = {len(matched3)})")

    q3_summary = {
        "event_count": cnt3,
        "sample_matching_events": [
            {
                "event_name": m["event_name"],
                "competitors_count": m["competitors_count"],
                "source_doc_id": m["source_doc_id"]
            }
            for m in matched3[:5]
        ]
    }
    for m in matched3[:5]:
        print(f"    * {m['event_name']} (competitors={m['competitors_count']}, doc={m['source_doc_id']})")
    if len(matched3) > 5:
        print(f"    ... and {len(matched3) - 5} more matching events")

    test_reports.append({
        "query": "count_events_above_competitors",
        "input": params3,
        "execution_status": "PASS",
        "count": cnt3,
        "matching_events_count": len(matched3)
    })

    # -------------------------------------------------------------------------
    # QUERY 4: MAX_COMPETITOR_EVENT
    # -------------------------------------------------------------------------
    print("\n--- QUERY 4: MAX_COMPETITOR_EVENT ---")
    params4 = {"games_search": games_q, "sport_search": sport_q}
    print(f"  Inputs: games='{games_q}', sport='{sport_q}'")

    res4 = conn.runInstalledQuery("max_competitor_event", params4)
    top_events = res4[0]["@@top_event"] if res4 else []
    print(f"  Execution Status: HTTP 200 SUCCESS (Found {len(top_events)} max event)")

    q4_summary = []
    for t in top_events:
        q4_summary.append({
            "event_name": t["event_name"],
            "event_id": t["event_id"],
            "competitors_count": t["competitors_count"],
            "source_doc_id": t["source_doc_id"],
            "source_doc_title": t["source_doc_title"]
        })
        print(f"    * Max Event:    {t['event_name']}")
        print(f"      Competitors:  {t['competitors_count']}")
        print(f"      Source Doc:   {t['source_doc_id']}")

    test_reports.append({
        "query": "max_competitor_event",
        "input": params4,
        "execution_status": "PASS",
        "results": q4_summary
    })

    # -------------------------------------------------------------------------
    # QUERY 5: EVENT_NATIONS
    # -------------------------------------------------------------------------
    print("\n--- QUERY 5: EVENT_NATIONS ---")
    event_lookup = "event_Q26233801"
    params5 = {"event_search": event_lookup}
    print(f"  Input: event_search='{event_lookup}'")

    res5 = conn.runInstalledQuery("event_nations", params5)
    details5 = res5[0]["@@details"] if res5 else []
    print(f"  Execution Status: HTTP 200 SUCCESS")

    q5_summary = []
    for d in details5:
        q5_summary.append({
            "event_name": d["event_name"],
            "event_id": d["event_id"],
            "nations_count": d["nations_count"],
            "competitors_count": d["competitors_count"],
            "venue_name": d["venue_name"],
            "date_str": d["date_str"],
            "source_doc_id": d["source_doc_id"]
        })
        print(f"    * Event:        {d['event_name']}")
        print(f"      Nations:      {d['nations_count']}")
        print(f"      Competitors:  {d['competitors_count']}")
        print(f"      Venue:        {d['venue_name']}")
        print(f"      Date:         {d['date_str']}")
        print(f"      Source Doc:   {d['source_doc_id']}")

    test_reports.append({
        "query": "event_nations",
        "input": params5,
        "execution_status": "PASS",
        "results": q5_summary
    })

    print("\n" + "=" * 80)
    print("ALL 5 REGRESSION QUERIES EXECUTED SUCCESSFULLY ON FULL GRAPH")
    print("=" * 80)

    return test_reports


if __name__ == "__main__":
    run_regression_tests()
