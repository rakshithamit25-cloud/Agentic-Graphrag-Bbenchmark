# Official GraphRAG Schema Plan

## Executive Summary
This design document outlines the graph schema plan for the **Hackathon Official Corpus** (`2,951` Wikipedia-style documents) and the **Official Evaluation Benchmark** (`100` questions across 5 question types).

> [!IMPORTANT]
> **Planning & Prototype Only:**
> This document does not deploy or modify any TigerGraph schema. The existing `AGRI_EVIDENCE` graph and livestock prototype remain untouched.

---

## 1. Domain & Corpus Analysis

### Corpus Overview
- **Total documents**: 2,951 JSONL records
- **Primary domain**: Olympic Games, sports competitions, events, venues, medalists, competitor counts, and nation counts.
- **Evaluation relevance**: All 100 benchmark evaluation questions (and 100% of the 518 gold documents) pertain to Olympic sports, events, historical medal winners, venues, dates, and event statistics.
- **Corpus document types**:
  - `Olympic event` infoboxes: 2,187 documents (includes all 518 gold documents)
  - `Film` infoboxes: 546 documents
  - `Album` infoboxes: 150 documents
  - `Officeholder / Person`: 138 documents
  - Other/General: ~130 documents

---

## 2. Proposed Vertex Types

| Vertex Type | Primary ID (`PRIMARY_ID`) | Key Attributes | Attribute Types | Data Source |
|---|---|---|---|---|
| **`Document`** | `doc_id` (e.g. `"Q303623"`) | `title`, `url`, `wikidata_qid`, `wikipedia_pageid`, `approx_tokens`, `text` | `STRING`, `STRING`, `STRING`, `INT`, `INT`, `STRING` | Corpus record root fields |
| **`Event`** | `event_id` (e.g. `"event_Q303623"`) | `name`, `sport`, `competitors_count`, `nations_count`, `date_str`, `win_value` | `STRING`, `STRING`, `INT`, `INT`, `STRING`, `STRING` | Document title & `[Infobox Olympic event]` |
| **`OlympicGames`** | `games_id` (e.g. `"games_2016_summer"`) | `name`, `year`, `season` | `STRING`, `INT`, `STRING` | `games` field in Infobox & Title |
| **`Sport`** | `sport_id` (e.g. `"sport_biathlon"`) | `name` | `STRING` | Extracted from event title prefix |
| **`Venue`** | `venue_id` (e.g. `"venue_richmond_olympic_oval"`) | `name` | `STRING` | `venue` field in Infobox & body text |
| **`Athlete`** | `athlete_id` (e.g. `"athlete_chen_ding"`) | `name`, `primary_noc` | `STRING`, `STRING` | `gold`, `silver`, `bronze` fields in Infobox |
| **`Country`** | `noc_code` (e.g. `"HUN"`, `"CHN"`, `"TUR"`) | `noc`, `name` | `STRING`, `STRING` | `goldNOC`, `silverNOC`, `bronzeNOC` fields |
| **`GeneralEntity`** | `entity_id` (e.g. `"film_Q12345"`) | `name`, `entity_type` | `STRING`, `STRING` | Non-Olympic infoboxes (film, album, company) |

---

## 3. Proposed Edge Types

| Edge Type | Source Vertex | Target Vertex | Directed? | Attributes | Benchmark Target Supported |
|---|---|---|---|---|---|
| **`DESCRIBES`** | `Document` | `Event` (or `GeneralEntity`) | Directed | None | Evidence traceability & Gold Doc retrieval |
| **`PART_OF_GAMES`** | `Event` | `OlympicGames` | Directed | `year` (INT) | Temporal, Aggregation, Superlative |
| **`BELONGS_TO_SPORT`** | `Event` | `Sport` | Directed | None | Aggregation, Superlative, Lookup |
| **`HELD_AT`** | `Event` | `Venue` | Directed | `date_str` (STRING) | Multi-hop (Venue + Date -> Event -> Winner) |
| **`WON_GOLD`** | `Event` | `Athlete` | Directed | `noc` (STRING), `win_value` (STRING) | Multi-hop, Temporal, Lookup |
| **`WON_SILVER`** | `Event` | `Athlete` | Directed | `noc` (STRING) | Lookup, Multi-hop |
| **`WON_BRONZE`** | `Event` | `Athlete` | Directed | `noc` (STRING) | Lookup, Multi-hop |
| **`REPRESENTS`** | `Athlete` | `Country` | Directed | None | Multi-hop, Aggregation |
| **`PRECEDED_BY`** | `OlympicGames` | `OlympicGames` | Directed | `season` (STRING) | Temporal ("immediately before 2016") |
| **`FOLLOWED_BY`** | `OlympicGames` | `OlympicGames` | Directed | `season` (STRING) | Temporal |

---

## 4. Benchmark Question Types & Graph Support

### 1. Multi-Hop Questions (28% of benchmark)
* **Question pattern**: *"Who won the gold medal in the event held at [Venue] on [Date] at the [Games]?"*
* **Graph Path**:
  ```
  (v:Venue {name: "Richmond Olympic Oval"})
    <-[:HELD_AT {date_str: "14 February 2010"}]- (e:Event)
    -[:WON_GOLD]-> (a:Athlete)
    <-[:DESCRIBES]- (d:Document)
  ```
* **Execution**: Traversal directly links the venue and date constraint to the exact event, returning both the winning athlete (`Martina Sáblíková`) and the gold document (`Q580481`).

### 2. Temporal Questions (22% of benchmark)
* **Question pattern**: *"Who won the gold medal in the [Event] at the Summer Olympics held immediately before [Year]?"*
* **Graph Path**:
  ```
  (g1:OlympicGames {year: 2016, season: "Summer"})
    -[:PRECEDED_BY]-> (g2:OlympicGames {year: 2012, season: "Summer"})
    <-[:PART_OF_GAMES]- (e:Event {name: "Men's 20 kilometres walk"})
    -[:WON_GOLD]-> (a:Athlete)
  ```
* **Execution**: Resolves the previous Olympic cycle deterministically via the temporal edge `PRECEDED_BY` (e.g. 2016 -> 2012), finds the corresponding event, and fetches the winner (`Chen Ding`).

### 3. Aggregation Questions (21% of benchmark)
* **Question pattern**: *"According to the provided corpus, how many [Sport] events at the [Games] had more than [N] competitors?"*
* **Graph Path**:
  ```
  (g:OlympicGames {name: "2018 Winter Olympics"})
    <-[:PART_OF_GAMES]- (e:Event)
    -[:BELONGS_TO_SPORT]-> (s:Sport {name: "Biathlon"})
  WHERE e.competitors_count > 73
  RETURN count(e), accumulate(d:Document)
  ```
* **Execution**: Single graph traversal aggregates all sibling events for a sport and games edition, filtering on the numeric attribute `competitors_count`.

### 4. Superlative Questions (10% of benchmark)
* **Question pattern**: *"According to the provided corpus, which [Sport] event at the [Games] had the highest number of competitors?"*
* **Graph Path**:
  ```
  (g:OlympicGames {name: "2008 Summer Olympics"})
    <-[:PART_OF_GAMES]- (e:Event)
    -[:BELONGS_TO_SPORT]-> (s:Sport {name: "Athletics"})
  ORDER BY e.competitors_count DESC LIMIT 1
  ```
* **Execution**: Avoids vector search hallucinations by sorting real numeric attributes stored on the vertices.

### 5. Lookup Questions (19% of benchmark)
* **Question pattern**: *"How many nations competed in [Event]?"*
* **Graph Path**:
  ```
  (e:Event {name: "Sailing at the 2016 Summer Olympics – Women's RS:X"})
  RETURN e.nations_count, linked Document
  ```
* **Execution**: Direct attribute lookup with 100% precision.

---

## 5. Extraction Feasibility & Limitations

### Highly Reliable Extractions (Deterministic from Infobox):
1. **Event Name, Sport, Games, Year, Season**: Present in 100% of Olympic documents.
2. **Competitor Counts & Nation Counts**: Present in 98.5% of Olympic documents.
3. **Gold, Silver, Bronze Medalists**: Present in 99.7% of Olympic documents.
4. **Gold/Silver/Bronze NOC Codes**: Present in 99.6% of Olympic documents.
5. **Venues**: Present in 96.3% of Olympic documents.
6. **Previous / Next Olympic References**: Present in 93.5% of Olympic documents.

### Known Extraction Limitations & Edge Cases:
1. **Concatenated Team Names**:
   In relay and doubles events, the infobox `gold` field frequently concatenates athlete names without delimiters (e.g., `"Rudolf DombiRoland Kökény"` or `"Dani KingLaura TrottJoanna Rowsell"`).
   *Mitigation*: Retain the full raw medalist string as an attribute on `Event`, and split names using camelCase / regex boundaries when possible.
2. **Date Variations**:
   Dates appear under both `date` (57.3%) and `dates` (41.6%), and range from single dates (`"20 September 1988"`) to multiday spans (`"6 to 8 August"`).
   *Mitigation*: Capture raw string and normalize year and month tokens.
3. **Non-Olympic Documents**:
   Documents without `[Infobox Olympic event]` (films, albums, etc.) do not have sports attributes. They should be indexed with generic `Document` vertices and basic topic entities so they do not pollute the sports graph while remaining retrievable.

---

## 6. TigerGraph Schema Readiness
The proposed schema maps directly to TigerGraph GSQL constructs:
- All vertex IDs are clean alphanumeric strings.
- All edges can be defined with undirected or directed pairs.
- Multi-hop GSQL queries (`SELECT`, `ACCUM`, `ORDER BY`) will directly resolve the complex aggregation and superlative questions that traditional RAG struggles to answer.
