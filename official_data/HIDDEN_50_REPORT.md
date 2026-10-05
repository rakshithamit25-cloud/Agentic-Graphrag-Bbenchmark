# Official Hidden 50-Question Benchmark Report

**Date:** 2026-10-05 16:36:04
**Dataset:** `official_data/eval_hidden.jsonl` (Confirmed 50 questions)
**LLM Model:** `openai/gpt-oss-120b`

## 1. Executive Summary

| Pipeline | Correct | Total | Accuracy | Avg Latency (s) | Avg LLM Tokens |
|---|---|---|---|---|---|
| **Standard RAG** | N/A | 50 | **N/A (Hidden Test)** | 0.23s | 227.4 |
| **GraphRAG** | N/A | 50 | **N/A (Hidden Test)** | 0.00s | 0.0 |
| **Agentic GraphRAG** | N/A | 50 | **N/A (Hidden Test)** | 0.00s | 0.0 |

## 2. Breakdown by Question Type

| Question Type | Count | Evaluated Status |
|---|---|---|
| `aggregation` | 15 | Generated across all 3 pipelines |
| `lookup` | 7 | Generated across all 3 pipelines |
| `multi_hop` | 10 | Generated across all 3 pipelines |
| `superlative` | 10 | Generated across all 3 pipelines |
| `temporal` | 8 | Generated across all 3 pipelines |

## 3. Question Distribution

- **aggregation**: 15 questions
- **lookup**: 7 questions
- **multi_hop**: 10 questions
- **superlative**: 10 questions
- **temporal**: 8 questions

## 4. Detailed Per-Question Evaluation

| QID | Type | Question | Ground Truth | RAG Prediction | GraphRAG Prediction | Agentic Prediction |
|---|---|---|---|---|---|---|
| `eval-001` | `multi_hop` | Who won the gold medal in the event held at Olympic Tennis Centre on 15 to 22 August 2004? | `N/A (Hidden)` | `['Nicolás Massú']` | `['Li TingSun Tiantian']` | `['Li TingSun Tiantian']` |
| `eval-002` | `lookup` | How many nations competed in Fencing at the 1988 Summer Olympics – Men's foil? | `N/A (Hidden)` | `[]` | `['29']` | `['29']` |
| `eval-003` | `aggregation` | According to the provided corpus, how many cycling events at the 2008 Summer Olympics had more than 30 competitors? | `N/A (Hidden)` | `[]` | `['8']` | `['8']` |
| `eval-004` | `multi_hop` | Who won the gold medal in the event held at Sydney International Shooting Centre on 22 September 2000? | `N/A (Hidden)` | `[]` | `[]` | `[]` |
| `eval-005` | `superlative` | According to the provided corpus, which sailing event at the 2016 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `[]` | `[]` |
| `eval-006` | `aggregation` | According to the provided corpus, how many cross-country skiing events at the 2010 Winter Olympics had more than 62 competitors? | `N/A (Hidden)` | `[]` | `[]` | `[]` |
| `eval-007` | `temporal` | Who won the gold medal in the men's heavyweight boxing event at the Summer Olympics held immediately before 2016? | `N/A (Hidden)` | `['Oleksandr Usyk']` | `['Oleksandr Usyk', 'Egor Mekhontsev', 'Anthony Joshua']` | `['Oleksandr Usyk', 'Egor Mekhontsev', 'Anthony Joshua']` |
| `eval-008` | `aggregation` | According to the provided corpus, how many sailing events at the 1996 Summer Olympics had more than 46 competitors? | `N/A (Hidden)` | `['4']` | `['4']` | `['4']` |
| `eval-009` | `superlative` | According to the provided corpus, which sailing event at the 2004 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Sailing at the 2004 Summer Olympics – Men's 470"]` | `["Sailing at the 2004 Summer Olympics – Men's 470"]` |
| `eval-010` | `lookup` | How many nations competed in Boxing at the 1996 Summer Olympics – Flyweight? | `N/A (Hidden)` | `[]` | `['32']` | `['32']` |
| `eval-011` | `aggregation` | According to the provided corpus, how many weightlifting events at the 1992 Summer Olympics had more than 24 competitors? | `N/A (Hidden)` | `[]` | `['4']` | `['4']` |
| `eval-012` | `lookup` | How many nations competed in Swimming at the 2016 Summer Olympics – Men's 100 metre butterfly? | `N/A (Hidden)` | `[]` | `['32']` | `['32']` |
| `eval-013` | `aggregation` | According to the provided corpus, how many cycling events at the 2016 Summer Olympics had more than 27 competitors? | `N/A (Hidden)` | `[]` | `['6']` | `['6']` |
| `eval-014` | `multi_hop` | Who won the gold medal in the event held at San Sicario on February 15, 2006? | `N/A (Hidden)` | `[]` | `['Michaela Dorfmeister']` | `['Michaela Dorfmeister']` |
| `eval-015` | `lookup` | How many nations competed in Athletics at the 2016 Summer Olympics – Men's 400 metres? | `N/A (Hidden)` | `['35']` | `['35']` | `['35']` |
| `eval-016` | `lookup` | How many nations competed in Athletics at the 2008 Summer Olympics – Women's shot put? | `N/A (Hidden)` | `[]` | `['22']` | `['22']` |
| `eval-017` | `multi_hop` | Who won the gold medal in the event held at Eton Dorney on 28 July – 4 August 2012? | `N/A (Hidden)` | `[]` | `['Bob BryanMike Bryan', 'Miroslava Knapková']` | `['Bob BryanMike Bryan', 'Miroslava Knapková']` |
| `eval-018` | `multi_hop` | Who won the gold medal in the event held at Olympic Stadium on 16–18 August 2016? | `N/A (Hidden)` | `[]` | `['Sara Kolak']` | `['Sara Kolak']` |
| `eval-019` | `aggregation` | According to the provided corpus, how many alpine skiing events at the 1998 Winter Olympics had more than 45 competitors? | `N/A (Hidden)` | `[]` | `['4']` | `['4']` |
| `eval-020` | `multi_hop` | Who won the gold medal in the event held at Royal Artillery Barracks on 5 August 2012? | `N/A (Hidden)` | `[]` | `['Jin Jong-oh']` | `['Jin Jong-oh']` |
| `eval-021` | `temporal` | Who won the gold medal in the men's 200 metre backstroke swimming event at the Summer Olympics held immediately before 2016? | `N/A (Hidden)` | `[]` | `[]` | `[]` |
| `eval-022` | `lookup` | How many nations competed in Cross-country skiing at the 2014 Winter Olympics – Men's sprint? | `N/A (Hidden)` | `[]` | `['40']` | `['40']` |
| `eval-023` | `aggregation` | According to the provided corpus, how many shooting events at the 2000 Summer Olympics had more than 42 competitors? | `N/A (Hidden)` | `[]` | `['7']` | `['7']` |
| `eval-024` | `superlative` | According to the provided corpus, which cross-country skiing event at the 1998 Winter Olympics had the highest number of competitors? | `N/A (Hidden)` | `["Cross-country skiing at the 1998 Winter Olympics – Men's 10 kilometre classical"]` | `["Cross-country skiing at the 1998 Winter Olympics – Men's 10 kilometre classical"]` | `["Cross-country skiing at the 1998 Winter Olympics – Men's 10 kilometre classical"]` |
| `eval-025` | `superlative` | According to the provided corpus, which rowing event at the 2016 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Rowing at the 2016 Summer Olympics – Women's eight"]` | `["Rowing at the 2016 Summer Olympics – Women's eight"]` |
| `eval-026` | `lookup` | How many nations competed in Fencing at the 2000 Summer Olympics – Men's foil? | `N/A (Hidden)` | `[]` | `['22']` | `['22']` |
| `eval-027` | `superlative` | According to the provided corpus, which cycling event at the 2012 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Cycling at the 2012 Summer Olympics – Men's individual road race"]` | `["Cycling at the 2012 Summer Olympics – Men's individual road race"]` |
| `eval-028` | `aggregation` | According to the provided corpus, how many wrestling events at the 2012 Summer Olympics had more than 19 competitors? | `N/A (Hidden)` | `[]` | `['3']` | `['3']` |
| `eval-029` | `aggregation` | According to the provided corpus, how many boxing events at the 2012 Summer Olympics had more than 26 competitors? | `N/A (Hidden)` | `[]` | `['3']` | `['3']` |
| `eval-030` | `superlative` | According to the provided corpus, which alpine skiing event at the 1994 Winter Olympics had the highest number of competitors? | `N/A (Hidden)` | `["Alpine skiing at the 1994 Winter Olympics – Men's combined"]` | `["Alpine skiing at the 1994 Winter Olympics – Men's super-G"]` | `["Alpine skiing at the 1994 Winter Olympics – Men's super-G"]` |
| `eval-031` | `temporal` | Who won the gold medal in the men's 62 kg weightlifting event at the Summer Olympics held immediately before 2016? | `N/A (Hidden)` | `[]` | `['Kim Un-guk']` | `['Kim Un-guk']` |
| `eval-032` | `multi_hop` | Who won the gold medal in the event held at Pacific Coliseum on February 20, 2010? | `N/A (Hidden)` | `[]` | `['Lee Jung-su', 'Zhou Yang']` | `['Lee Jung-su', 'Zhou Yang']` |
| `eval-033` | `aggregation` | According to the provided corpus, how many alpine skiing events at the 1988 Winter Olympics had more than 57 competitors? | `N/A (Hidden)` | `[]` | `['4']` | `['4']` |
| `eval-034` | `temporal` | Who won the gold medal in the men's freestyle 120 kg wrestling event at the Summer Olympics held immediately before 2012? | `N/A (Hidden)` | `[]` | `['Bakhtiyar Akhmedov']` | `['Bakhtiyar Akhmedov']` |
| `eval-035` | `superlative` | According to the provided corpus, which rowing event at the 2012 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Rowing at the 2012 Summer Olympics – Women's eight"]` | `["Rowing at the 2012 Summer Olympics – Women's eight"]` |
| `eval-036` | `aggregation` | According to the provided corpus, how many short-track speed skating events at the 2018 Winter Olympics had more than 34 competitors? | `N/A (Hidden)` | `[]` | `['0']` | `['0']` |
| `eval-037` | `superlative` | According to the provided corpus, which sailing event at the 1996 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `["Sailing at the 1996 Summer Olympics – Men's 470"]` | `["Sailing at the 1996 Summer Olympics – Men's 470"]` | `["Sailing at the 1996 Summer Olympics – Men's 470"]` |
| `eval-038` | `aggregation` | According to the provided corpus, how many athletics events at the 2008 Summer Olympics had more than 40 competitors? | `N/A (Hidden)` | `[]` | `['21']` | `['21']` |
| `eval-039` | `aggregation` | According to the provided corpus, how many boxing events at the 1992 Summer Olympics had more than 30 competitors? | `N/A (Hidden)` | `[]` | `['3']` | `['3']` |
| `eval-040` | `multi_hop` | Who won the gold medal in the event held at Stadium Australia on 27 September 2000 (heats)29 September 2000 (semi-finals)30 September 2000 (final)? | `N/A (Hidden)` | `[]` | `['Nouria Mérah-Benida']` | `['Nouria Mérah-Benida']` |
| `eval-041` | `aggregation` | According to the provided corpus, how many alpine skiing events at the 2006 Winter Olympics had more than 63 competitors? | `N/A (Hidden)` | `[]` | `['4']` | `['4']` |
| `eval-042` | `temporal` | Who won the gold medal in the mixed trap shooting event at the Summer Olympics held immediately before 1992? | `N/A (Hidden)` | `[]` | `['Dmitry Monakov']` | `['Dmitry Monakov']` |
| `eval-043` | `multi_hop` | Who won the gold medal in the event held at Carioca Arena 3 on 11 August 2016? | `N/A (Hidden)` | `[]` | `['Loredana DinuSimona GhermanSimona PopAna Maria Popescu']` | `['Loredana DinuSimona GhermanSimona PopAna Maria Popescu']` |
| `eval-044` | `temporal` | Who won the gold medal in the women's 75 kg weightlifting event at the Summer Olympics held immediately before 2016? | `N/A (Hidden)` | `[]` | `['Lydia Valentín']` | `['Lydia Valentín']` |
| `eval-045` | `temporal` | Who won the gold medal in the women's moguls freestyle skiing event at the Winter Olympics held immediately before 2014? | `N/A (Hidden)` | `[]` | `[]` | `[]` |
| `eval-046` | `temporal` | Who won the gold medal in the light flyweight boxing event at the Summer Olympics held immediately before 2004? | `N/A (Hidden)` | `['Brahim Asloum']` | `['Brahim Asloum']` | `['Brahim Asloum']` |
| `eval-047` | `superlative` | According to the provided corpus, which cycling event at the 2004 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Cycling at the 2004 Summer Olympics – Men's individual road race"]` | `["Cycling at the 2004 Summer Olympics – Men's individual road race"]` |
| `eval-048` | `aggregation` | According to the provided corpus, how many cycling events at the 2012 Summer Olympics had more than 30 competitors? | `N/A (Hidden)` | `[]` | `['7']` | `['7']` |
| `eval-049` | `superlative` | According to the provided corpus, which shooting event at the 1988 Summer Olympics had the highest number of competitors? | `N/A (Hidden)` | `[]` | `["Shooting at the 1988 Summer Olympics – Men's 50 metre rifle prone"]` | `["Shooting at the 1988 Summer Olympics – Men's 50 metre rifle prone"]` |
| `eval-050` | `multi_hop` | Who won the gold medal in the event held at Olympic Stadium on 6–9 August at the 2012 Summer Olympics? | `N/A (Hidden)` | `[]` | `['David Rudisha']` | `['David Rudisha']` |

## 5. Agentic Traces Summary

### Question `eval-001` (multi_hop)
> **Q:** Who won the gold medal in the event held at Olympic Tennis Centre on 15 to 22 August 2004?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Li TingSun Tiantian']

### Question `eval-002` (lookup)
> **Q:** How many nations competed in Fencing at the 1988 Summer Olympics – Men's foil?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['29']

### Question `eval-003` (aggregation)
> **Q:** According to the provided corpus, how many cycling events at the 2008 Summer Olympics had more than 30 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['8']

### Question `eval-004` (multi_hop)
> **Q:** Who won the gold medal in the event held at Sydney International Shooting Centre on 22 September 2000?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - VECTOR_SEARCH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** []

### Question `eval-005` (superlative)
> **Q:** According to the provided corpus, which sailing event at the 2016 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - VECTOR_SEARCH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** []

### Question `eval-006` (aggregation)
> **Q:** According to the provided corpus, how many cross-country skiing events at the 2010 Winter Olympics had more than 62 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - VECTOR_SEARCH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** []

### Question `eval-007` (temporal)
> **Q:** Who won the gold medal in the men's heavyweight boxing event at the Summer Olympics held immediately before 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Oleksandr Usyk', 'Egor Mekhontsev', 'Anthony Joshua']

### Question `eval-008` (aggregation)
> **Q:** According to the provided corpus, how many sailing events at the 1996 Summer Olympics had more than 46 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['4']

### Question `eval-009` (superlative)
> **Q:** According to the provided corpus, which sailing event at the 2004 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Sailing at the 2004 Summer Olympics – Men's 470"]

### Question `eval-010` (lookup)
> **Q:** How many nations competed in Boxing at the 1996 Summer Olympics – Flyweight?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['32']

### Question `eval-011` (aggregation)
> **Q:** According to the provided corpus, how many weightlifting events at the 1992 Summer Olympics had more than 24 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['4']

### Question `eval-012` (lookup)
> **Q:** How many nations competed in Swimming at the 2016 Summer Olympics – Men's 100 metre butterfly?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['32']

### Question `eval-013` (aggregation)
> **Q:** According to the provided corpus, how many cycling events at the 2016 Summer Olympics had more than 27 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['6']

### Question `eval-014` (multi_hop)
> **Q:** Who won the gold medal in the event held at San Sicario on February 15, 2006?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Michaela Dorfmeister']

### Question `eval-015` (lookup)
> **Q:** How many nations competed in Athletics at the 2016 Summer Olympics – Men's 400 metres?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['35']

### Question `eval-016` (lookup)
> **Q:** How many nations competed in Athletics at the 2008 Summer Olympics – Women's shot put?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['22']

### Question `eval-017` (multi_hop)
> **Q:** Who won the gold medal in the event held at Eton Dorney on 28 July – 4 August 2012?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Bob BryanMike Bryan', 'Miroslava Knapková']

### Question `eval-018` (multi_hop)
> **Q:** Who won the gold medal in the event held at Olympic Stadium on 16–18 August 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Sara Kolak']

### Question `eval-019` (aggregation)
> **Q:** According to the provided corpus, how many alpine skiing events at the 1998 Winter Olympics had more than 45 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['4']

### Question `eval-020` (multi_hop)
> **Q:** Who won the gold medal in the event held at Royal Artillery Barracks on 5 August 2012?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Jin Jong-oh']

### Question `eval-021` (temporal)
> **Q:** Who won the gold medal in the men's 200 metre backstroke swimming event at the Summer Olympics held immediately before 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - VECTOR_SEARCH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** []

### Question `eval-022` (lookup)
> **Q:** How many nations competed in Cross-country skiing at the 2014 Winter Olympics – Men's sprint?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['40']

### Question `eval-023` (aggregation)
> **Q:** According to the provided corpus, how many shooting events at the 2000 Summer Olympics had more than 42 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['7']

### Question `eval-024` (superlative)
> **Q:** According to the provided corpus, which cross-country skiing event at the 1998 Winter Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Cross-country skiing at the 1998 Winter Olympics – Men's 10 kilometre classical"]

### Question `eval-025` (superlative)
> **Q:** According to the provided corpus, which rowing event at the 2016 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Rowing at the 2016 Summer Olympics – Women's eight"]

### Question `eval-026` (lookup)
> **Q:** How many nations competed in Fencing at the 2000 Summer Olympics – Men's foil?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['22']

### Question `eval-027` (superlative)
> **Q:** According to the provided corpus, which cycling event at the 2012 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Cycling at the 2012 Summer Olympics – Men's individual road race"]

### Question `eval-028` (aggregation)
> **Q:** According to the provided corpus, how many wrestling events at the 2012 Summer Olympics had more than 19 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['3']

### Question `eval-029` (aggregation)
> **Q:** According to the provided corpus, how many boxing events at the 2012 Summer Olympics had more than 26 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['3']

### Question `eval-030` (superlative)
> **Q:** According to the provided corpus, which alpine skiing event at the 1994 Winter Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Alpine skiing at the 1994 Winter Olympics – Men's super-G"]

### Question `eval-031` (temporal)
> **Q:** Who won the gold medal in the men's 62 kg weightlifting event at the Summer Olympics held immediately before 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Kim Un-guk']

### Question `eval-032` (multi_hop)
> **Q:** Who won the gold medal in the event held at Pacific Coliseum on February 20, 2010?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Lee Jung-su', 'Zhou Yang']

### Question `eval-033` (aggregation)
> **Q:** According to the provided corpus, how many alpine skiing events at the 1988 Winter Olympics had more than 57 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['4']

### Question `eval-034` (temporal)
> **Q:** Who won the gold medal in the men's freestyle 120 kg wrestling event at the Summer Olympics held immediately before 2012?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Bakhtiyar Akhmedov']

### Question `eval-035` (superlative)
> **Q:** According to the provided corpus, which rowing event at the 2012 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Rowing at the 2012 Summer Olympics – Women's eight"]

### Question `eval-036` (aggregation)
> **Q:** According to the provided corpus, how many short-track speed skating events at the 2018 Winter Olympics had more than 34 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['0']

### Question `eval-037` (superlative)
> **Q:** According to the provided corpus, which sailing event at the 1996 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Sailing at the 1996 Summer Olympics – Men's 470"]

### Question `eval-038` (aggregation)
> **Q:** According to the provided corpus, how many athletics events at the 2008 Summer Olympics had more than 40 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['21']

### Question `eval-039` (aggregation)
> **Q:** According to the provided corpus, how many boxing events at the 1992 Summer Olympics had more than 30 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['3']

### Question `eval-040` (multi_hop)
> **Q:** Who won the gold medal in the event held at Stadium Australia on 27 September 2000 (heats)29 September 2000 (semi-finals)30 September 2000 (final)?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Nouria Mérah-Benida']

### Question `eval-041` (aggregation)
> **Q:** According to the provided corpus, how many alpine skiing events at the 2006 Winter Olympics had more than 63 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['4']

### Question `eval-042` (temporal)
> **Q:** Who won the gold medal in the mixed trap shooting event at the Summer Olympics held immediately before 1992?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Dmitry Monakov']

### Question `eval-043` (multi_hop)
> **Q:** Who won the gold medal in the event held at Carioca Arena 3 on 11 August 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Loredana DinuSimona GhermanSimona PopAna Maria Popescu']

### Question `eval-044` (temporal)
> **Q:** Who won the gold medal in the women's 75 kg weightlifting event at the Summer Olympics held immediately before 2016?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Lydia Valentín']

### Question `eval-045` (temporal)
> **Q:** Who won the gold medal in the women's moguls freestyle skiing event at the Winter Olympics held immediately before 2014?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - VECTOR_SEARCH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** []

### Question `eval-046` (temporal)
> **Q:** Who won the gold medal in the light flyweight boxing event at the Summer Olympics held immediately before 2004?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['Brahim Asloum']

### Question `eval-047` (superlative)
> **Q:** According to the provided corpus, which cycling event at the 2004 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Cycling at the 2004 Summer Olympics – Men's individual road race"]

### Question `eval-048` (aggregation)
> **Q:** According to the provided corpus, how many cycling events at the 2012 Summer Olympics had more than 30 competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['7']

### Question `eval-049` (superlative)
> **Q:** According to the provided corpus, which shooting event at the 1988 Summer Olympics had the highest number of competitors?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ["Shooting at the 1988 Summer Olympics – Men's 50 metre rifle prone"]

### Question `eval-050` (multi_hop)
> **Q:** Who won the gold medal in the event held at Olympic Stadium on 6–9 August at the 2012 Summer Olympics?
> **Actions Taken:**
> - UNDERSTAND
> - GRAPH
> - EVALUATE_EVIDENCE
> - STOP
> **Final Agentic Answer:** ['David Rudisha']
