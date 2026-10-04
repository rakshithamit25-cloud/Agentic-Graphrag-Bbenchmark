# EVIDENCE GRAPH - Agentic GraphRAG

### Three-Way Retrieval & Reasoning Benchmark on Olympic History

**EVIDENCE GRAPH** is an Agentic GraphRAG system that combines semantic document retrieval, TigerGraph knowledge-graph traversal, and adaptive agentic reasoning to answer complex Olympic-history questions with evidence.

The project evaluates three approaches on the same Olympic benchmark:

* **RAG** — Retrieval-Augmented Generation
* **GraphRAG** — Knowledge-graph-based retrieval and reasoning
* **Agentic GraphRAG** — Adaptive investigation using multiple retrieval and reasoning actions

---

## Problem Statement

Traditional RAG systems can retrieve relevant documents, but they can struggle when a question requires:

* Multiple pieces of evidence
* Relationships between entities
* Multi-hop reasoning
* Temporal reasoning
* Aggregation across events
* Superlative questions
* Connecting athletes, events, venues, sports, countries, and Olympic editions

For example:

> Who won the gold medal in the event held at
