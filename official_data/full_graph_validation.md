# FULL GRAPH CSV VALIDATION REPORT

**Validation Status**: **PASS**  
**Corpus Source**: `official_data/corpus.jsonl` (2,951 documents)  
**Target Directory**: `official_data/tigergraph/full/`  

## 1. Summary of Processed Documents and Entities

- **Total Documents in Corpus**: 2,951
- **Olympic Documents (with infobox)**: 2187
- **Non-Olympic Documents (retained as Document vertices)**: 764

### Vertex Counts (Generated CSVs)

| Vertex Type | Primary ID Field | Row Count | Duplicate Count | Invalid Records |
|:---|:---|:---:|:---:|:---:|
| **Document** | `doc_id` | **2951** | 0 | 0 |
| **Event** | `event_id` | **2187** | 0 | 0 |
| **OlympicGames** | `games_id` | **26** | 0 | 0 |
| **Sport** | `sport_id` | **42** | 0 | 0 |
| **Venue** | `venue_id` | **322** | 0 | 0 |
| **Athlete** | `athlete_id` | **5324** | 0 | 0 |
| **Country** | `noc_code` | **136** | 0 | 0 |
| **Total Vertices** | | **10988** | **0** | **0** |

### Edge Counts (Generated CSVs)

| Edge Type | Directed Path | Row Count | Duplicate Count | Dangling References |
|:---|:---|:---:|:---:|:---:|
| **DESCRIBES** | `Document -> Event` | **2187** | 0 | 0 |
| **PART_OF_GAMES** | `Event -> OlympicGames` | **2187** | 0 | 0 |
| **BELONGS_TO_SPORT** | `Event -> Sport` | **2187** | 0 | 0 |
| **HELD_AT** | `Event -> Venue` | **2125** | 0 | 0 |
| **WON_GOLD** | `Event -> Athlete` | **2194** | 0 | 0 |
| **WON_SILVER** | `Event -> Athlete` | **2188** | 0 | 0 |
| **WON_BRONZE** | `Event -> Athlete` | **2464** | 0 | 0 |
| **REPRESENTS** | `Athlete -> Country` | **5355** | 0 | 0 |
| **PRECEDED_BY** | `OlympicGames -> OlympicGames` | **36** | 0 | 0 |
| **Total Edges** | | **20923** | **0** | **0** |

## 2. Validation Checks Results

| Check # | Validation Rule | Status | Details |
|:---:|:---|:---:|:---|
| 1 | CSV Syntax & RFC 4180 Format | **PASS** | All 16 CSV files parsed cleanly without syntax or quoting errors |
| 2 | Header Alignment with GSQL Schema | **PASS** | 100% match on all expected column names and order |
| 3 | Duplicate Primary IDs | **PASS** | 0 duplicate primary IDs across all 7 vertex files |
| 4 | Invalid / Empty Primary IDs | **PASS** | 0 empty or whitespace primary IDs |
| 5 | Integer Value Validation | **PASS** | All integer fields (`approx_tokens`, `competitors_count`, `nations_count`, `year`) valid |
| 6 | Dangling Edge References | **PASS** | 0 dangling source or target references; all foreign keys resolve |
| 7 | Duplicate Directed Edges | **PASS** | 0 duplicate `(source, target)` edges across all 9 edge files |
| 8 | Missing Source Document IDs | **PASS** | 100% of 20,923 edges have explicit `source_doc_id` and raw evidence |

## 3. Discrepancies and Rejections

- **Duplicate Records Found**: 0
- **Invalid Records Found**: 0
- **Rejected Records**: 0
- **Corrupt Lines**: 0

## 4. Conclusion & Readiness

The generated dataset is **100% mathematically and structurally valid**. All primary keys, foreign keys, integer values, and headers comply with `backend/official_tigergraph_schema.gsql` and `backend/official_tigergraph_loading.gsql`.
The dataset is approved for loading into `OLYMPIC_BENCHMARK`.
