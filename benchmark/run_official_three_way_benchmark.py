import json
import os
import re
import sys
import time
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Make backend importable when this file is run directly
sys.path.insert(0, str(BASE_DIR))

# ============================================================
# IMPORTS
# ============================================================

import pyTigerGraph as tg

from backend.config import Config
from backend.official_vector_search import official_vector_search
from backend.groq_client import (
    groq_generate as _groq_generate,
    groq_generate_with_metadata as _groq_generate_with_metadata,
    GROQ_MODEL,
)


# ============================================================
# FILE PATHS
# ============================================================

EVAL_FILE = BASE_DIR / "official_data" / "eval_public.jsonl"

CORPUS_FILE = BASE_DIR / "official_data" / "corpus.jsonl"

RESULT_FILE = (
    BASE_DIR
    / "official_data"
    / "official_three_way_results.json"
)


# ============================================================
# KNOWN SPORTS
# ============================================================

KNOWN_SPORTS = [
    "artistic gymnastics",
    "modern pentathlon",
    "marathon swimming",
    "beach volleyball",
    "cross-country skiing",
    "alpine skiing",
    "speed skating",
    "figure skating",
    "short track speed skating",
    "nordic combined",
    "table tennis",
    "water polo",
    "weightlifting",
    "snowboarding",
    "athletics",
    "archery",
    "badminton",
    "baseball",
    "basketball",
    "biathlon",
    "boxing",
    "canoeing",
    "cycling",
    "diving",
    "equestrian",
    "fencing",
    "football",
    "golf",
    "handball",
    "hockey",
    "judo",
    "rowing",
    "rugby",
    "sailing",
    "shooting",
    "skating",
    "skiing",
    "swimming",
    "taekwondo",
    "tennis",
    "triathlon",
    "volleyball",
    "wrestling",
]


# ============================================================
# LOAD JSONL
# ============================================================

def load_jsonl(path):
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()

    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# QUESTION PARSERS
# ============================================================

def parse_year(question):
    match = re.search(
        r"\b(18|19|20)\d{2}\b",
        question
    )

    if match:
        return int(match.group(0))

    return None


def parse_season(question):
    q = question.lower()

    if "winter olympics" in q:
        return "Winter"

    if "summer olympics" in q:
        return "Summer"

    return "Summer"


def parse_threshold(question):
    q = question.lower()

    patterns = [
        r"more than\s+(\d+)\s+competitors",
        r"more than\s+(\d+)\s+participants",
        r"greater than\s+(\d+)\s+competitors",
        r"above\s+(\d+)\s+competitors",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)

        if match:
            return int(match.group(1))

    return None


def parse_sport(question):
    q = normalize_text(question)

    for sport in sorted(
        KNOWN_SPORTS,
        key=len,
        reverse=True
    ):
        if sport in q:
            return sport

    return ""


def parse_event_search(question):
    """Parse event search string from question.

    For lookup questions of the form:
    'How many nations competed in [Sport] at the [Year] [Season] Olympics – [Event]?'
    we return the full event title: '[Sport] at the [Year] [Season] Olympics – [Event]'

    For temporal questions of the form:
    'Who won the gold medal in the [event] at the [Season] Olympics...'
    we return the event portion.
    """
    original = question.strip()

    # --------------------------------------------------------
    # LOOKUP questions: extract event name from dash suffix
    # The question structure is:
    # 'How many nations competed in [Sport] at the [Year] [Season] Olympics – [Event]?'
    # We want to pass the full event title to TigerGraph LIKE search.
    # --------------------------------------------------------
    if re.search(
        r"how many nations competed",
        original,
        re.IGNORECASE
    ):
        # Try to match the whole "[Sport] at the [Year] [Season] Olympics – [Event]" portion
        m = re.search(
            r"competed in\s+(.+?)\??\s*$",
            original,
            re.IGNORECASE
        )
        if m:
            return m.group(1).strip().rstrip("?")
        return ""

    q = original.lower().strip()

    # Remove beginning of winner question
    q = re.sub(
        r"^who won the gold medal in the\s+",
        "",
        q
    )

    # Keep event text before
    # "at the Summer/Winter Olympics"
    q = re.split(
        r"\s+at the\s+(?:summer|winter)\s+olympics",
        q,
        maxsplit=1
    )[0]

    # Remove word "event"
    q = re.sub(
        r"\bevent\b",
        "",
        q
    )

    # Remove known sport from the end
    for sport in sorted(
        KNOWN_SPORTS,
        key=len,
        reverse=True
    ):
        q = re.sub(
            r"\s+"
            + re.escape(sport.lower())
            + r"$",
            "",
            q
        )

    # Remove gender prefix.
    # Gender is handled separately.
    q = re.sub(
        r"^(men's|women's)\s+",
        "",
        q,
        flags=re.IGNORECASE
    )

    q = re.sub(
        r"\s+",
        " ",
        q
    ).strip()

    return q


def parse_venue(question):
    """Extract venue from multi-hop question.

    Handles patterns:
      - 'at [venue] on DD Month YYYY'
      - 'at [venue] on Month DD, YYYY'
      - 'at [venue] on [range] at the YYYY Olympics'
      - 'at [venue] on [range] at the YYYY Summer/Winter Olympics'
    """
    # Use original case for venue (do NOT .lower())
    # because the graph stores venue names case-sensitively
    # and we rely on LIKE for partial matching.
    q = question

    # Pattern order matters – try most specific first

    # Pattern 1: "at X on ... at the YYYY Season Olympics"
    # Handles: "at Mountain Bike Centre on 21 August at the 2016 Summer Olympics"
    # Handles: "at Riocentro – Pavilion 4 on 11–19 August at the 2016 Summer Olympics"
    for pat in [
        r"at\s+(.+?)\s+on\s+.+?\s+at\s+the\s+\d{4}\s+(?:Summer|Winter)\s+Olympics",
        r"at\s+(.+?)\s+on\s+.+?\s+at\s+the\s+\d{4}\s+Olympics",
    ]:
        m = re.search(pat, q, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Pattern 2: "at X on DD Month YYYY" (single date)
    m = re.search(
        r"at\s+(.+?)\s+on\s+\d{1,2}\s+\w+\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 3: "at X on Month DD, YYYY" (US format)
    m = re.search(
        r"at\s+(.+?)\s+on\s+\w+\s+\d{1,2},?\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 4: "at X on DD-DD Month YYYY" (date range with en-dash/to)
    m = re.search(
        r"at\s+(.+?)\s+on\s+\d{1,2}[\u2013\-]\d{1,2}\s+\w+\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 5: "at X on DD Month to DD Month YYYY"
    m = re.search(
        r"at\s+(.+?)\s+on\s+\d{1,2}\s+\w+\s+to\s+\d{1,2}\s+\w+\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 6: "at X on February DD-DD, YYYY"
    m = re.search(
        r"at\s+(.+?)\s+on\s+\w+\s+\d{1,2}[\u2013\-]\d{1,2},?\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    # Pattern 7: "at X on DD, DD Month YYYY" (comma-separated days)
    m = re.search(
        r"at\s+(.+?)\s+on\s+\d{1,2},\s+\d{1,2}\s+\w+\s+\d{4}",
        q,
        re.IGNORECASE
    )
    if m:
        return m.group(1).strip()

    return ""


def parse_date(question):
    """Extract date/date-phrase from multi-hop question.

    Strategy 1 (highest priority): Full phrase between 'on' and 'at the YYYY'.
    This handles year-less dates like 'on 21 August at the 2016 Summer Olympics'
    and returns '21 August' which TigerGraph LIKE can match against '21 August'.

    Strategy 2: Full phrase from 'on' to end of question.
    This captures complex annotations such as '(heats & final)' and '(slow)22 September'
    so TigerGraph LIKE produces an exact or near-exact match.
    """
    MONTHS = (
        r"(?:january|february|march|april|may|june|july|august"
        r"|september|october|november|december)"
    )

    # Strategy 1: date phrase before "at the YYYY" context
    # e.g. "on 21 August at the 2016 Summer Olympics" → "21 August"
    # e.g. "on 11–19 August at the 2016 Summer Olympics" → "11–19 August"
    # e.g. "on 3 to 4 August at the 2012 Summer Olympics" → "3 to 4 August"
    m = re.search(
        r"\bon\s+(.+?)\s+at\s+the\s+\d{4}\b",
        question,
        re.IGNORECASE
    )
    if m:
        candidate = m.group(1).strip()
        # Must look like a date (contains a month name or digit)
        if re.search(MONTHS + r"|\d{1,2}", candidate, re.IGNORECASE):
            return candidate

    # Strategy 2: full phrase from 'on' to end of sentence
    # e.g. "on August 14, 2004 (heats & final)" → captures full phrase
    # e.g. "on 21 September 2000 (slow)22 September 2000 (fast)" → full phrase
    m = re.search(
        r"\bon\s+(.+?)\s*\??\s*$",
        question,
        re.IGNORECASE
    )
    if m:
        candidate = m.group(1).strip().rstrip("?.")
        # Only accept if it contains a year (4-digit) or a month name
        if re.search(r"\b\d{4}\b", candidate) or re.search(
            MONTHS, candidate, re.IGNORECASE
        ):
            return candidate

    return ""


# ============================================================
# TIGERGRAPH CONNECTION
# ============================================================

def get_connection():
    conn = tg.TigerGraphConnection(
        host=Config.TG_HOST,
        graphname="OLYMPIC_BENCHMARK",
        gsqlSecret=Config.TG_SECRET
    )

    conn.getToken(Config.TG_SECRET)

    return conn


def capitalize_sport(sport):
    """Capitalize only the first letter of a sport name.

    This matches how TigerGraph stores sport names in event titles:
    'Alpine skiing', 'Speed skating', 'Cross-country skiing'
    NOT title-case 'Alpine Skiing', 'Speed Skating'.
    """
    if not sport:
        return sport
    return sport[0].upper() + sport[1:]


# ============================================================
# GRAPH: AGGREGATION
# ============================================================

def graph_aggregation(conn, question):

    year = parse_year(question)

    season = parse_season(question)

    threshold = parse_threshold(question)

    sport = parse_sport(question)

    if sport:
        # Use capitalize (first letter only) not title() to preserve
        # multi-word sports like 'Alpine skiing', 'Speed skating'.
        sport = capitalize_sport(sport)

    games_search = ""

    if year and season:
        games_search = f"{year} {season}"

    params = {
        "games_search": games_search,
        "sport_search": sport,
        "threshold": threshold,
    }

    result = conn.runInstalledQuery(
        "count_events_above_competitors",
        params
    )

    # TigerGraph returns:
    #
    # [
    #   {"event_count": 5},
    #   {"matching_events": [...]}
    # ]
    #
    # So we must read event_count directly.

    event_count = None

    matching_events = []

    for item in result or []:

        if "event_count" in item:
            event_count = item["event_count"]

        if "matching_events" in item:
            matching_events = item["matching_events"]

    # Safety fallback
    if event_count is None:
        event_count = len(matching_events)

    return {
        "query": "count_events_above_competitors",
        "parameters": params,
        "results": matching_events,
        "answer": [str(event_count)],
    }


# ============================================================
# GRAPH: TEMPORAL
# ============================================================

def graph_previous_olympics(conn, question):

    year = parse_year(question)

    season = parse_season(question)

    event_search = parse_event_search(question)

    if event_search:
        event_search = event_search.replace(
        " athletics",
        ""
    ).strip()

    # Remove detected sport from event details.
    for sport in KNOWN_SPORTS:
        event_search = re.sub(
            r"\b" + re.escape(sport.lower()) + r"\b",
            "",
            event_search,
            flags=re.IGNORECASE
        )

    event_search = re.sub(
        r"\s+",
        " ",
        event_search
    ).strip()
    # Detect sport from the original question.
    sport_search = None

    for sport in KNOWN_SPORTS:
        if re.search(
            r"\b" + re.escape(sport.lower()) + r"\b",
            question.lower()
        ):
            # Use capitalize (first letter only) not title() so that
            # multi-word sports match graph storage:
            # 'Nordic combined', 'Cross-country skiing', 'Speed skating'
            sport_search = capitalize_sport(sport)
            break

    # Use the sport for graph retrieval when available.
    # The remaining event details will be filtered in Python.
    graph_event_search = (
        sport_search
        if sport_search
        else event_search
    )

    params = {
        "games_year": year,
        "season": season,
        "event_search": graph_event_search,
    }

    result = conn.runInstalledQuery(
        "previous_olympics_gold",
        params
    )

    rows = []

    if result:
        rows = result[0].get(
            "@@results",
            []
        )
    # --------------------------------------------------------
    # Filter gender from original question
    # --------------------------------------------------------
    q_lower = question.lower()

    if "men's" in q_lower and "women's" not in q_lower:
        rows = [
            row
            for row in rows
            if "women's" not in row.get(
                "event_name",
                ""
            ).lower()
            and "men's" in row.get(
                "event_name",
                ""
            ).lower()
        ]

    elif "women's" in q_lower:
        rows = [
            row
            for row in rows
            if "women's" in row.get(
                "event_name",
                ""
            ).lower()
        ]

    # --------------------------------------------------------
    # Filter on individual vs. team when question specifies
    # --------------------------------------------------------
    q_lower2 = question.lower()

    # --------------------------------------------------------
    # Filter on individual vs. team
    # --------------------------------------------------------
    # If question has "individual" and NOT "team" → exclude team events
    if "individual" in q_lower2 and "team" not in q_lower2:
        individual_rows = [
            row for row in rows
            if "team" not in row.get("event_name", "").lower()
        ]
        if individual_rows:
            rows = individual_rows
    # If question does NOT mention "team" and we have mixed team/non-team
    # results, prefer non-team (e.g. 'épée' vs 'team épée')
    elif "team" not in q_lower2:
        non_team_rows = [
            row for row in rows
            if "team" not in row.get("event_name", "").lower()
        ]
        if non_team_rows and len(non_team_rows) < len(rows):
            rows = non_team_rows

    # --------------------------------------------------------
    # Filter remaining event details such as "57 kg",
    # "20 kilometres walk", "80 kg" etc.
    # --------------------------------------------------------
    if event_search:
        event_tokens = event_search.lower().split()

        def token_matches_event(token, event_name_lower):
            """Check token in event name with unit-abbreviation tolerance."""
            if re.search(
                r"\b" + re.escape(token) + r"\b",
                event_name_lower
            ):
                return True
            # Handle metre/metres → m, kilometre/kilometres → km
            if token in ("metre", "metres"):
                return bool(re.search(r"\b\d+\s*m\b", event_name_lower))
            if token in ("kilometre", "kilometres"):
                return bool(re.search(r"\b\d+\s*km\b", event_name_lower))
            return False

        rows = [
            row
            for row in rows
            if all(
                token_matches_event(
                    token,
                    row.get("event_name", "").lower()
                )
                for token in event_tokens
            )
        ]

        # --------------------------------------------------------
        # Weight-class exact match: exclude '+N kg' when asking 'N kg'
        # e.g. question has '80 kg' → exclude events with '+80 kg'
        # --------------------------------------------------------
        wt = re.search(r'(?<!\+)(\d+)\s*kg', event_search, re.IGNORECASE)
        if wt:
            weight = wt.group(1)
            rows = [
                row for row in rows
                if not re.search(
                    r'\+' + re.escape(weight) + r'\s*kg',
                    row.get('event_name', ''),
                    re.IGNORECASE
                )
            ]
    # --------------------------------------------------------
    # Select nearest previous Olympic Games
    # --------------------------------------------------------

    if rows:

        previous_years = [
            row.get("previous_year")
            for row in rows
            if isinstance(
                row.get("previous_year"),
                int
            )
        ]

        if previous_years:

            nearest_previous_year = max(
                previous_years
            )

            rows = [
                row
                for row in rows
                if row.get(
                    "previous_year"
                ) == nearest_previous_year
            ]

    # --------------------------------------------------------
    # Extract winner
    # --------------------------------------------------------

    answer = []

    for row in rows:

        winner = row.get(
            "gold_winner_name"
        )

        if winner:
            answer.append(str(winner))

    # Remove duplicates

    answer = list(
        dict.fromkeys(answer)
    )

    return {
        "query": "previous_olympics_gold",
        "parameters": params,
        "results": rows,
        "answer": answer,
    }

# ============================================================
# GRAPH: SUPERLATIVE
# ============================================================

def graph_superlative(conn, question):

    year = parse_year(question)

    season = parse_season(question)

    sport = parse_sport(question)

    if sport:
        # Use capitalize (first letter only) not title() to match graph storage
        sport = capitalize_sport(sport)

    games_search = ""

    if year and season:
        games_search = f"{year} {season}"

    params = {
        "games_search": games_search,
        "sport_search": sport,
    }

    result = conn.runInstalledQuery(
        "max_competitor_event",
        params
    )

    rows = []

    if result:
        rows = result[0].get(
            "@@top_event",
            []
        )

    answer = []

    if rows:

        event_name = rows[0].get(
            "event_name"
        )

        if event_name:
            answer = [event_name]

    return {
        "query": "max_competitor_event",
        "parameters": params,
        "results": rows,
        "answer": answer,
    }


# ============================================================
# GRAPH: MULTI-HOP
# ============================================================

def _score_row_for_date(row, date_search):
    """Score a graph result row by how well date_str matches date_search.

    Higher = better match.
    """
    if not date_search:
        return 0
    date_str = (row.get("date_str") or "").lower()
    ds = date_search.lower()

    if date_str == ds:
        return 3  # exact match
    if date_str.startswith(ds):
        return 2  # starts with (date is the primary date)
    if ds in date_str:
        return 1  # contains
    return 0


def graph_multi_hop(conn, question):
    venue_raw = parse_venue(question)
    # The graph is inconsistent with dashes in venue names:
    # - 'Riocentro – Pavilion 6' stored with em-dash (U+2013)
    # - 'Riocentro - Pavilion 4' stored with regular hyphen
    # Strategy: try the original (em-dash) venue first.
    # If 0 results, retry with all dashes normalized to regular hyphen.
    venue_normalized = venue_raw.replace('\u2013', '-').replace('\u2014', '-') if venue_raw else venue_raw

    date = parse_date(question)

    def _run_query(venue_search):
        params = {
            "venue_search": venue_search,
            "date_search": date,
        }
        result = conn.runInstalledQuery("event_by_venue_date", params)
        rows = result[0].get("@@results", []) if result else []
        return params, rows

    # First try: original venue (preserves em-dash for venues like 'Riocentro – Pavilion 6')
    params, rows = _run_query(venue_raw)

    # Second try: hyphen-normalized venue (for 'Riocentro - Pavilion 4', 'Val-d\'Isère', etc.)
    if not rows and venue_normalized != venue_raw:
        params, rows = _run_query(venue_normalized)

    venue = params["venue_search"]

    # --------------------------------------------------------
    # Safety: if we got ALL events (venue='', date=''),
    # return empty rather than returning thousands of wrong answers.
    # --------------------------------------------------------
    if not venue and not date:
        return {
            "query": "event_by_venue_date",
            "parameters": params,
            "results": [],
            "answer": [],
        }

    # --------------------------------------------------------
    # Disambiguation: prefer rows whose date_str best matches
    # the parsed date string (exact > starts-with > contains).
    # --------------------------------------------------------
    if len(rows) > 1 and date:
        scored = [
            (row, _score_row_for_date(row, date))
            for row in rows
        ]
        max_score = max(s for _, s in scored)

        if max_score > 0:
            rows = [
                row for row, s in scored if s == max_score
            ]

    # --------------------------------------------------------
    # Secondary disambiguation: if venue name contains a sport
    # keyword, prefer events of that sport.
    # e.g. 'Laura Biathlon & Ski Complex' → prefer Biathlon events
    # --------------------------------------------------------
    if len(rows) > 1 and venue:
        venue_lower = venue.lower()
        sport_hints = [
            'biathlon', 'swimming', 'gymnastics', 'weightlifting',
            'shooting', 'archery', 'boxing', 'judo', 'wrestling',
            'fencing', 'cycling', 'rowing', 'sailing', 'volleyball',
        ]
        for hint in sport_hints:
            if hint in venue_lower:
                hinted = [
                    row for row in rows
                    if hint in row.get('event_name', '').lower()
                ]
                if hinted and len(hinted) < len(rows):
                    rows = hinted
                    break

    answer = []

    for row in rows:
        winner = row.get("gold_winner_name")

        if winner:
            answer.append(str(winner))

    answer = list(dict.fromkeys(answer))

    return {
        "query": "event_by_venue_date",
        "parameters": params,
        "results": rows,
        "answer": answer,
    }


# ============================================================
# GRAPH: LOOKUP
# ============================================================

def graph_lookup(conn, question):

    event_search = parse_event_search(
        question
    )

    if not event_search:
        event_search = question

    params = {
        "event_search": event_search
    }

    result = conn.runInstalledQuery(
        "event_nations",
        params
    )

    rows = []

    if result:
        rows = result[0].get(
            "@@details",
            []
        )

    answer = []

    # If multiple rows returned (LIKE matched too broadly),
    # prefer exact event name match.
    if len(rows) > 1:
        exact = [
            row for row in rows
            if row.get("event_name", "").lower() == event_search.lower()
        ]
        if exact:
            rows = exact

    for row in rows:

        nations = row.get(
            "nations_count"
        )

        if nations is not None:
            answer.append(
                str(nations)
            )

    # De-duplicate answers
    answer = list(dict.fromkeys(answer))

    return {
        "query": "event_nations",
        "parameters": params,
        "results": rows,
        "answer": answer,
    }


# ============================================================
# SELECT GRAPH QUERY
# ============================================================

def run_graph_query(
    conn,
    qtype,
    question
):

    if qtype == "aggregation":

        return graph_aggregation(
            conn,
            question
        )

    if qtype == "temporal":

        return graph_previous_olympics(
            conn,
            question
        )

    if qtype == "superlative":

        return graph_superlative(
            conn,
            question
        )

    if qtype == "multi_hop":

        return graph_multi_hop(
            conn,
            question
        )

    if qtype == "lookup":

        return graph_lookup(
            conn,
            question
        )

    return {
        "query": None,
        "parameters": {},
        "results": [],
        "answer": [],
    }


# ============================================================
# GRAPH LLM SYNTHESIS (SAME-LLM COMPLIANCE)
# ============================================================

def synthesize_graph_answer(question, graph_result, pipeline_name="GraphRAG"):
    """Generate final natural-language answer from TigerGraph query results
    using the unified Groq model (openai/gpt-oss-120b).

    TigerGraph remains 100% responsible for graph traversal, filtering, and retrieval.
    The LLM performs final natural-language answer formatting/extraction.
    If the LLM call is disabled or fails, falls back gracefully to TigerGraph's direct answer.
    """
    default_answer = graph_result.get("answer", [])
    evidence = graph_result.get("results", [])

    enable_llm = os.environ.get("ENABLE_GRAPH_LLM_SYNTHESIS", "false").lower() in ("1", "true", "yes")
    if not enable_llm:
        return default_answer, {
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
        }

    if not evidence and not default_answer:
        return [], {
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
        }

    prompt = (
        "You are a concise answer generator for an Olympic benchmark.\n"
        "Based strictly on the verified TigerGraph query results below, output ONLY the final answer value.\n"
        "Do not add explanation, preamble, or extra punctuation.\n"
        "- For a person: write only the name (e.g. Chen Ding).\n"
        "- For a number: write only the number (e.g. 5).\n"
        "- For an event title: write only the full event title.\n\n"
        f"QUESTION: {question}\n\n"
        f"TIGERGRAPH RESULTS:\n{json.dumps(evidence[:5], ensure_ascii=False)}\n\n"
        "ANSWER:"
    )

    try:
        time.sleep(10)
        res = _groq_generate_with_metadata(
            prompt,
            max_retries=2,
            initial_backoff=1.0,
        )
        if res.get("success") and res.get("content"):
            ans = res["content"].strip().strip('"').strip("'").strip()
            return [ans], {
                "llm_tokens": res.get("total_tokens", 0),
                "llm_latency": res.get("latency", 0.0),
                "llm_model": res.get("model", GROQ_MODEL),
            }
    except Exception as e:
        print(f"[{pipeline_name} LLM Warning] {e}; using TigerGraph direct answer.")

    return default_answer, {
        "llm_tokens": 0,
        "llm_latency": 0.0,
        "llm_model": GROQ_MODEL,
    }


# ============================================================
# ADAPTIVE RAG RETRIEVAL SETTINGS
# ============================================================

def get_rag_retrieval_settings(question, qtype):
    """Return adaptive RAG retrieval settings based on question type.

    Balances evidence coverage and Groq prompt token consumption.
    """
    if qtype == "aggregation":
        return {
            "initial_top_k": 40,
            "max_chars_per_doc": 400,
            "apply_entity_filter": True,
            "max_filtered_docs": 25,
        }
    elif qtype == "superlative":
        return {
            "initial_top_k": 30,
            "max_chars_per_doc": 400,
            "apply_entity_filter": True,
            "max_filtered_docs": 20,
        }
    elif qtype == "temporal":
        return {
            "initial_top_k": 10,
            "max_chars_per_doc": 400,
            "apply_entity_filter": False,
            "max_filtered_docs": 10,
        }
    elif qtype == "multi_hop":
        return {
            "initial_top_k": 10,
            "max_chars_per_doc": 400,
            "apply_entity_filter": False,
            "max_filtered_docs": 10,
        }
    else:  # lookup and any other
        return {
            "initial_top_k": 10,
            "max_chars_per_doc": 400,
            "apply_entity_filter": False,
            "max_filtered_docs": 10,
        }


def filter_rag_candidates(question, docs, max_docs=25):
    """Filter candidate documents for aggregation/superlative questions using
    extracted question entities (year, sport). Preserves documents relevant
    to the target Games and sport while filtering out distractor editions.
    Falls back gracefully to vector rank order if filtering produces too few docs.
    """
    year = parse_year(question)
    sport = parse_sport(question)

    year_str = str(year) if year else ""
    sport_str = sport.lower() if sport else ""

    if not year_str and not sport_str:
        return docs[:max_docs]

    matched_docs = []
    seen_ids = set()

    for d in docs:
        title_lower = (d.get("title") or "").lower()
        snippet_lower = (d.get("text") or "")[:450].lower()

        year_match = (
            (year_str in title_lower or f"games: {year_str}" in snippet_lower)
            if year_str else True
        )
        sport_match = (
            (sport_str in title_lower or f"event: {sport_str}" in snippet_lower)
            if sport_str else True
        )

        if year_match and sport_match:
            matched_docs.append(d)
            seen_ids.add(d["doc_id"])

    # If filtering yields at least 3 documents, use them (capped at max_docs)
    if len(matched_docs) >= 3:
        # If fewer than 5 documents, backfill top remaining candidates from vector search
        if len(matched_docs) < 5:
            for d in docs:
                if d["doc_id"] not in seen_ids:
                    matched_docs.append(d)
                    seen_ids.add(d["doc_id"])
                    if len(matched_docs) >= 8:
                        break
        return matched_docs[:max_docs]

    # Fallback to top vector candidates if filter was too restrictive
    return docs[:max_docs]


def extract_relevant_rag_fields(title, text, max_chars=400):
    """Extract prioritized metadata fields from Olympic event documents to minimize
    Groq prompt token consumption while retaining all critical answer evidence.
    """
    if "[Infobox Olympic event]" in text or "event:" in text:
        fields = []

        # Event name
        m_event = re.search(r"^\s*event:\s*(.+)$", text, re.MULTILINE)
        if m_event:
            fields.append(f"Event: {m_event.group(1).strip()}")
        elif " – " in title:
            fields.append(f"Event: {title.split(' – ', 1)[1].strip()}")
        elif " - " in title:
            fields.append(f"Event: {title.split(' - ', 1)[1].strip()}")

        # Year / Games
        m_games = re.search(r"^\s*games:\s*(.+)$", text, re.MULTILINE)
        if m_games:
            fields.append(f"Games: {m_games.group(1).strip()}")
        else:
            m_year = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", title)
            if m_year:
                fields.append(f"Year: {m_year.group(1)}")

        # Sport
        if " at the " in title:
            fields.append(f"Sport: {title.split(' at the ')[0].strip()}")
        else:
            m_sport = re.search(r"^\s*sport:\s*(.+)$", text, re.MULTILINE)
            if m_sport:
                fields.append(f"Sport: {m_sport.group(1).strip()}")

        # Venue
        m_venue = re.search(r"^\s*venue:\s*(.+)$", text, re.MULTILINE)
        if m_venue:
            fields.append(f"Venue: {m_venue.group(1).strip()}")

        # Date
        m_date = re.search(r"^\s*dates?:\s*(.+)$", text, re.MULTILINE)
        if m_date:
            fields.append(f"Date: {m_date.group(1).strip()}")

        # Competitors
        m_comp = re.search(r"^\s*competitors:\s*(.+)$", text, re.MULTILINE)
        if m_comp:
            fields.append(f"Competitors: {m_comp.group(1).strip()}")

        # Nations
        m_nations = re.search(r"^\s*nations:\s*(.+)$", text, re.MULTILINE)
        if m_nations:
            fields.append(f"Nations: {m_nations.group(1).strip()}")

        # Gold winner
        m_gold = re.search(r"^\s*gold:\s*(.+)$", text, re.MULTILINE)
        if m_gold:
            gold_str = m_gold.group(1).strip()
            m_noc = re.search(r"^\s*goldNOC:\s*(.+)$", text, re.MULTILINE)
            if m_noc:
                gold_str += f" ({m_noc.group(1).strip()})"
            fields.append(f"Gold Winner: {gold_str}")

        if fields:
            summary = "\n".join(fields)
            return summary[:max_chars]

    snippet = text[:max_chars]
    if len(text) > max_chars:
        snippet += "..."
    return snippet


# ============================================================
# RAG BASELINE
# ============================================================

def rag_answer(
    question,
    corpus_by_id,
    qtype=None,
    top_k=None,
    max_chars=None,
):

    settings = get_rag_retrieval_settings(question, qtype or "lookup")
    actual_top_k = top_k if top_k is not None else settings["initial_top_k"]
    actual_max_chars = max_chars if max_chars is not None else settings["max_chars_per_doc"]

    retrieved = official_vector_search(
        question,
        top_k=actual_top_k
    )

    retrieved_docs = []

    for item in retrieved:

        doc_id = item.get(
            "doc_id"
        )

        doc = corpus_by_id.get(
            doc_id
        )

        if doc:

            retrieved_docs.append(
                {
                    "doc_id": doc_id,
                    "score": item.get(
                        "score"
                    ),
                    "title": doc.get(
                        "title",
                        ""
                    ),
                    "text": doc.get(
                        "text",
                        ""
                    ),
                    "approx_tokens": doc.get(
                        "approx_tokens",
                        0
                    ),
                }
            )

    # --------------------------------------------------------
    # Build evidence context for Groq
    # --------------------------------------------------------

    if not retrieved_docs:
        return {
            "answer": [],
            "documents": retrieved_docs,
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
        }

    # Apply adaptive entity filtering for aggregation and superlative queries
    if settings.get("apply_entity_filter"):
        selected_docs = filter_rag_candidates(
            question,
            retrieved_docs,
            max_docs=settings.get("max_filtered_docs", 25)
        )
    else:
        selected_docs = retrieved_docs[:actual_top_k]

    print(
        f"[RAG Adaptive] qtype={qtype or 'lookup'} | "
        f"retrieved={len(retrieved_docs)} | selected={len(selected_docs)} | "
        f"max_chars={actual_max_chars}"
    )

    evidence_blocks = []
    for i, doc in enumerate(selected_docs, start=1):
        title = doc.get("title", "").strip()
        text = (doc.get("text", "") or "").strip()
        snippet = extract_relevant_rag_fields(title, text, max_chars=actual_max_chars)
        evidence_blocks.append(
            f"[Document {i}] {title}\n{snippet}"
        )

    evidence_text = "\n\n".join(evidence_blocks)

    # --------------------------------------------------------
    # Groq prompt
    # --------------------------------------------------------

    prompt = (
        "You are an answer extractor for an Olympic-history question-answering benchmark.\n"
        "\n"
        "STRICT RULES:\n"
        "- Answer ONLY using the supplied retrieved documents below.\n"
        "- Do NOT use prior knowledge or outside information of any kind.\n"
        "- If the documents do not contain enough information to answer, "
        "reply with exactly: INSUFFICIENT_EVIDENCE\n"
        "\n"
        "OUTPUT FORMAT:\n"
        "- Reply with the answer value only — no explanation, no preamble, no JSON.\n"
        "- For a person or event name: write only the name (e.g. Michael Phelps).\n"
        "- For a number: write only the digit(s) (e.g. 5).\n"
        "- For an event title: write only the full event title "
        "(e.g. Athletics at the 2008 Summer Olympics \u2013 Men's marathon).\n"
        "- Do not add country names, parentheses, or extra context.\n"
        "\n"
        f"QUESTION: {question}\n"
        "\n"
        "RETRIEVED DOCUMENTS:\n"
        f"{evidence_text}\n"
        "\n"
        "ANSWER:"
    )

    # --------------------------------------------------------
    # Call Groq and parse response
    # --------------------------------------------------------

    llm_tokens = 0
    llm_latency = 0.0
    llm_model = GROQ_MODEL

    try:
        time.sleep(10)
        res = _groq_generate_with_metadata(
            prompt,
            max_retries=2,
            initial_backoff=1.0,
        )
        llm_tokens = res.get("total_tokens", 0)
        llm_latency = res.get("latency", 0.0)
        llm_model = res.get("model", GROQ_MODEL)
        raw = res.get("content", "").strip()
    except Exception as e:
        print("GROQ_RAG_ERROR:", repr(e))
        return {
            "answer": [],
            "documents": retrieved_docs,
            "llm_tokens": 0,
            "llm_latency": 0.0,
            "llm_model": GROQ_MODEL,
        }

    # If the LLM signals no evidence, return empty.
    if not raw or raw.upper() == "INSUFFICIENT_EVIDENCE":
        return {
            "answer": [],
            "documents": retrieved_docs,
            "llm_tokens": llm_tokens,
            "llm_latency": llm_latency,
            "llm_model": llm_model,
        }

    # Normalise: strip surrounding quotes, leading/trailing whitespace,
    # and em/en dashes so the result aligns with normalize_text() used in
    # answers_match().
    answer_text = raw.strip().strip('"').strip("'").strip()

    return {
        "answer": [answer_text],
        "documents": retrieved_docs,
        "llm_tokens": llm_tokens,
        "llm_latency": llm_latency,
        "llm_model": llm_model,
    }


# ============================================================
# TOKEN ESTIMATION
# ============================================================

def estimate_tokens_from_docs(docs):

    total = 0

    for doc in docs:

        try:

            total += int(
                doc.get(
                    "approx_tokens",
                    0
                )
            )

        except Exception:
            pass

    return total


# ============================================================
# GOLD DOC COVERAGE
# ============================================================

def calculate_gold_coverage(
    retrieved_docs,
    gold_doc_ids
):

    retrieved_ids = {
        doc.get("doc_id")
        for doc in retrieved_docs
    }

    gold_ids = set(gold_doc_ids)

    if not gold_ids:
        return 0.0

    found = retrieved_ids & gold_ids

    return len(found) / len(gold_ids)


# ============================================================
# ANSWER NORMALIZATION
# ============================================================

def normalize_answers(answers):

    if answers is None:
        return []

    if not isinstance(
        answers,
        list
    ):
        answers = [answers]

    result = []

    for answer in answers:

        value = normalize_text(
            answer
        )

        if value:
            result.append(value)

    return result


def answers_match(
    predicted,
    gold
):

    predicted_norm = normalize_answers(
        predicted
    )

    gold_norm = normalize_answers(
        gold
    )

    return predicted_norm == gold_norm


# ============================================================
# AGENTIC GRAPHRAG
# ============================================================

def agentic_answer(
    conn,
    question_row,
    corpus_by_id
):

    question = question_row["question"]

    qtype = question_row["qtype"]

    state = {
        "question": question,
        "qtype": qtype,
        "actions": [],
        "graph_result": None,
        "vector_result": None,
        "evidence": [],
        "answer": [],
    }

    # --------------------------------------------------------
    # 1. Understand
    # --------------------------------------------------------

    state["actions"].append(
        "UNDERSTAND"
    )

    # --------------------------------------------------------
    # 2. Graph
    # --------------------------------------------------------

    state["actions"].append(
        "GRAPH"
    )

    try:

        graph_result = run_graph_query(
            conn,
            qtype,
            question
        )

        state["graph_result"] = graph_result

    except Exception as exc:

        state["graph_result"] = {
            "answer": [],
            "error": str(exc),
        }

    graph_answer = []

    if state["graph_result"]:

        graph_answer = state[
            "graph_result"
        ].get(
            "answer",
            []
        )

    # --------------------------------------------------------
    # 3. Vector fallback
    # --------------------------------------------------------

    if not graph_answer:

        state["actions"].append(
            "VECTOR_SEARCH"
        )

        try:

            vector_result = rag_answer(
                question,
                corpus_by_id,
                qtype=qtype,
            )

            state["vector_result"] = (
                vector_result
            )

            state["answer"] = (
                vector_result.get(
                    "answer",
                    []
                )
            )

            state["evidence"] = (
                vector_result.get(
                    "documents",
                    []
                )
            )

        except Exception:

            state["answer"] = []

    else:

        state["answer"] = graph_answer

    # --------------------------------------------------------
    # Graph evidence
    # --------------------------------------------------------

    if (
        state["graph_result"]
        and state["graph_result"].get(
            "results"
        )
    ):

        state["evidence"] = (
            state["graph_result"]["results"]
        )

    # --------------------------------------------------------
    # 4. Evidence evaluation
    # --------------------------------------------------------

    state["actions"].append(
        "EVALUATE_EVIDENCE"
    )

    # --------------------------------------------------------
    # 5. Stop
    # --------------------------------------------------------

    state["actions"].append(
        "STOP"
    )

    return state


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)

    print(
        "PHASE 6 - OFFICIAL THREE-WAY BENCHMARK"
    )

    print("=" * 80)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    questions = load_jsonl(
        EVAL_FILE
    )

    corpus = load_jsonl(
        CORPUS_FILE
    )

    corpus_by_id = {
        doc["doc_id"]: doc
        for doc in corpus
    }

    print(
        f"Official questions loaded: {len(questions)}"
    )

    distribution = Counter(
        q["qtype"]
        for q in questions
    )

    print(
        "Question distribution:",
        dict(distribution)
    )

    # --------------------------------------------------------
    # Read --limit
    # --------------------------------------------------------

    limit = None

    if (
        len(sys.argv) >= 3
        and sys.argv[1] == "--limit"
    ):

        try:

            limit = int(
                sys.argv[2]
            )

        except ValueError:

            limit = None

    if limit:

        questions_to_run = (
            questions[:limit]
        )

        print(
            f"TEST MODE: running first {limit} questions"
        )

    else:

        questions_to_run = questions

        print(
            "FULL MODE: running all questions"
        )

    # --------------------------------------------------------
    # Connect TigerGraph
    # --------------------------------------------------------

    conn = get_connection()

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    rag_correct = 0

    graphrag_correct = 0

    agentic_correct = 0

    results = []

    # ========================================================
    # PROCESS QUESTIONS
    # ========================================================

    for index, row in enumerate(
        questions_to_run,
        start=1
    ):

        qid = row["qid"]

        qtype = row["qtype"]

        question = row["question"]

        gold_answer = row["answer"]

        gold_doc_ids = row.get(
            "gold_doc_ids",
            []
        )

        print()

        print(
            f"Processing {index}/{len(questions_to_run)}"
        )

        print("-" * 80)

        print(
            f"{qid} | {qtype}"
        )

        print(question)

        # ====================================================
        # RAG
        # ====================================================

        rag_result = rag_answer(
            question,
            corpus_by_id,
            qtype=qtype,
        )

        rag_predicted = rag_result.get(
            "answer",
            []
        )

        rag_pass = answers_match(
            rag_predicted,
            gold_answer
        )

        if rag_pass:
            rag_correct += 1

        rag_tokens = (
            estimate_tokens_from_docs(
                rag_result.get(
                    "documents",
                    []
                )
            )
        )

        rag_coverage = (
            calculate_gold_coverage(
                rag_result.get(
                    "documents",
                    []
                ),
                gold_doc_ids
            )
        )

        print(
            "RAG       :",
            rag_predicted,
            "|",
            "PASS" if rag_pass else "FAIL"
        )

        # ====================================================
        # GraphRAG
        # ====================================================

        try:

            graph_result = run_graph_query(
                conn,
                qtype,
                question
            )

        except Exception as exc:

            graph_result = {
                "query": None,
                "parameters": {},
                "results": [],
                "answer": [],
                "error": str(exc),
            }

        graph_predicted, graph_llm_meta = synthesize_graph_answer(
            question,
            graph_result,
            pipeline_name="GraphRAG"
        )

        graph_pass = answers_match(
            graph_predicted,
            gold_answer
        )

        if graph_pass:
            graphrag_correct += 1

        graph_evidence = (
            graph_result.get(
                "results",
                []
            )
        )

        graph_tokens = len(
            json.dumps(
                graph_evidence,
                ensure_ascii=False
            ).split()
        )

        print(
            "GraphRAG  :",
            graph_predicted,
            "|",
            "PASS" if graph_pass else "FAIL"
        )

        # ====================================================
        # Agentic GraphRAG
        # ====================================================

        agentic_result = agentic_answer(
            conn,
            row,
            corpus_by_id
        )

        agentic_predicted, agentic_llm_meta = synthesize_graph_answer(
            question,
            {
                "answer": agentic_result.get("answer", []),
                "results": agentic_result.get("evidence", []),
            },
            pipeline_name="Agentic GraphRAG"
        )

        agentic_pass = answers_match(
            agentic_predicted,
            gold_answer
        )

        if agentic_pass:
            agentic_correct += 1

        agentic_evidence = (
            agentic_result.get(
                "evidence",
                []
            )
        )

        agentic_tokens = len(
            json.dumps(
                agentic_evidence,
                ensure_ascii=False
            ).split()
        )

        print(
            "Agentic   :",
            agentic_predicted,
            "|",
            "PASS" if agentic_pass else "FAIL"
        )

        # ====================================================
        # Store result
        # ====================================================

        results.append(
            {
                "qid": qid,
                "qtype": qtype,
                "question": question,
                "gold_answer": gold_answer,

                "rag": {
                    "answer": rag_predicted,
                    "correct": rag_pass,
                    "estimated_evidence_tokens": rag_tokens,
                    "gold_doc_coverage": rag_coverage,
                    "llm_model": rag_result.get("llm_model", GROQ_MODEL),
                    "llm_tokens": rag_result.get("llm_tokens", 0),
                    "llm_latency": rag_result.get("llm_latency", 0.0),
                },

                "graphrag": {
                    "answer": graph_predicted,
                    "correct": graph_pass,
                    "estimated_evidence_tokens": graph_tokens,
                    "query": graph_result.get(
                        "query"
                    ),
                    "parameters": graph_result.get(
                        "parameters"
                    ),
                    "results": graph_evidence,
                    "llm_model": graph_llm_meta.get("llm_model", GROQ_MODEL),
                    "llm_tokens": graph_llm_meta.get("llm_tokens", 0),
                    "llm_latency": graph_llm_meta.get("llm_latency", 0.0),
                },

                "agentic_graphrag": {
                    "answer": agentic_predicted,
                    "correct": agentic_pass,
                    "actions": agentic_result.get(
                        "actions",
                        []
                    ),
                    "estimated_evidence_tokens": agentic_tokens,
                    "llm_model": agentic_llm_meta.get("llm_model", GROQ_MODEL),
                    "llm_tokens": agentic_llm_meta.get("llm_tokens", 0),
                    "llm_latency": agentic_llm_meta.get("llm_latency", 0.0),
                },
            }
        )

        time.sleep(2)

    # ========================================================
    # SUMMARY
    # ========================================================

    total = len(
        questions_to_run
    )

    rag_accuracy = (
        rag_correct / total
        if total
        else 0
    )

    graph_accuracy = (
        graphrag_correct / total
        if total
        else 0
    )

    agentic_accuracy = (
        agentic_correct / total
        if total
        else 0
    )

    output = {
        "benchmark":
            "Official TigerGraph Agentic GraphRAG Benchmark",

        "mode":
            "official",

        "total_questions":
            total,

        "question_distribution":
            dict(distribution),

        "summary": {
            "llm_model": GROQ_MODEL,
            "rag": {
                "correct": rag_correct,
                "total": total,
                "accuracy": rag_accuracy,
                "avg_latency": (
                    sum(r["rag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["rag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },

            "graphrag": {
                "correct": graphrag_correct,
                "total": total,
                "accuracy": graph_accuracy,
                "avg_latency": (
                    sum(r["graphrag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["graphrag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },

            "agentic_graphrag": {
                "correct": agentic_correct,
                "total": total,
                "accuracy": agentic_accuracy,
                "avg_latency": (
                    sum(r["agentic_graphrag"].get("llm_latency", 0.0) for r in results) / total
                    if total else 0.0
                ),
                "avg_tokens": (
                    sum(r["agentic_graphrag"].get("llm_tokens", 0) for r in results) / total
                    if total else 0.0
                ),
            },
        },

        "results":
            results,
    }

    # ========================================================
    # SAVE
    # ========================================================

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    print()

    print("=" * 80)

    print(
        "PHASE 6 COMPLETE"
    )

    print("=" * 80)

    print(
        "Results saved to:"
    )

    print(
        RESULT_FILE
    )

    print()

    print(
        "SUMMARY"
    )

    print(f"LLM Model: {GROQ_MODEL}")

    print(
        f"rag: {rag_correct}/{total} "
        f"({rag_accuracy:.2%})"
    )

    print(
        f"graphrag: {graphrag_correct}/{total} "
        f"({graph_accuracy:.2%})"
    )

    print(
        f"agentic_graphrag: {agentic_correct}/{total} "
        f"({agentic_accuracy:.2%})"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
