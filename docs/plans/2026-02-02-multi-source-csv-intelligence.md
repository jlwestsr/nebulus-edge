# Multi-Source CSV Intelligence - Design Discussion

**Date:** 2026-02-02
**Status:** Awaiting user feedback from end customer (sales director)
**MVP Feature:** Multi-source data correlation using VIN as primary key

## Product Vision

**Nebulus Edge** is a privacy-first AI appliance for small businesses handling sensitive data:
- Target hardware: Mac mini (48GB RAM)
- Target customers: Sales directors, doctors, lawyers, accountants
- Key value: On-premise, turnkey, customer owns hardware
- Business model: Sell configured hardware + software

### Initial Use Case: Car Dealership
- Sales director needs to analyze data from multiple sources (inventory, service records, sales)
- All sources share VIN as primary key
- Contains PII - must stay on-premise
- Need to answer cross-source questions like "Which vehicles serviced 3+ times are still on lot?"

## Architecture Approaches Considered

### Approach 1: SQL Database + Natural Language to SQL ⭐ (Recommended)

**Implementation:**
- User uploads CSVs → Import into SQLite database
- VIN becomes foreign key linking tables
- User asks question → LLM generates SQL → Execute → Return results + explanation

**Pros:**
- Dealership data is naturally tabular
- SQL joins on VIN are what it's designed for
- Deterministic results (critical for business decisions)
- Can show generated SQL for transparency/trust
- Fast execution even with large datasets

**Cons:**
- Requires schema management (can be automated)
- SQL generation can fail on ambiguous questions

**Tech Stack:**
- SQLite for data storage
- Text-to-SQL model or prompt engineering with Qwen3-Coder-30B
- Schema introspection for auto-discovery
- Query validation and error handling

---

### Approach 2: RAG-based (Vector Database)

**Implementation:**
- CSVs → Parse into vector embeddings (ChromaDB/FAISS)
- VIN used for chunking/indexing
- User asks → Semantic search finds relevant rows → LLM analyzes

**Pros:**
- More flexible for unstructured questions
- Works well with current LLM setup

**Cons:**
- Struggles with complex joins or exact filters
- Less deterministic (business users may not trust it)
- Slower for large datasets

---

### Approach 3: Hybrid (SQL + RAG)

**Implementation:**
- Structured data in SQLite, metadata in vector DB
- LLM decides which system to query based on question type

**Pros:**
- Best of both worlds
- Handles both structured queries and semantic search

**Cons:**
- 2x the complexity
- Overkill for MVP
- Two systems to maintain

## Next Steps

### Awaiting Customer Feedback
Email sent to sales director (end user) asking:
1. Speed & Accuracy vs. Flexibility preference
2. Real example of hardest question they'd ask

### Implementation Phases (Post-Feedback)

**Phase 1: Core CSV Intelligence (MVP)**
- CSV upload interface in Open WebUI
- SQLite import with VIN auto-detection
- Basic natural language to SQL
- Query execution and result formatting

**Phase 2: Multi-Source Correlation**
- Auto-detect relationships across tables
- Schema visualization
- Join optimization

**Phase 3: Security & Privacy**
- PII detection and masking
- Data encryption at rest
- Audit logging
- Access controls

**Phase 4: Business Analytics**
- Pre-built industry-specific queries
- Scheduled reports
- Alert system

**Phase 5: Autonomous Agent**
- Slack integration for remote monitoring
- Scheduled analysis tasks
- Proactive insights

## Related Nebulus Projects

- **Nebulus Prime**: Linux version (server/datacenter)
- **Nebulus Gantry**: Custom web UI (Open WebUI fork)
- **Nebulus Atom**: AI agent system (Claude Desktop inspired)

## Technical Considerations

### Current Stack
- Brain: FastAPI + MLX (Qwen3-Coder-30B)
- Body: Open WebUI (Docker)
- Infrastructure: PM2 + Ansible

### Additions Needed for CSV Intelligence
- Database layer (SQLite initially, PostgreSQL for production?)
- File upload handling
- CSV parsing and validation
- Schema inference
- Text-to-SQL engine
- Query sandbox for safety

### Security Requirements
- No data leaves the Mac mini
- Encryption at rest
- PII auto-detection
- Query result sanitization
- Audit trail

## Open Questions

1. How do we handle schema conflicts across CSVs?
2. What level of SQL complexity do we support?
3. How do we validate generated SQL is safe?
4. Do we need a visual query builder as fallback?
5. How do we handle data updates (new CSVs)?

## Success Criteria

**For MVP:**
- Upload 3+ CSVs with VIN column
- Ask natural language question requiring cross-source join
- Get accurate results in <5 seconds
- Results are verifiable (show SQL)
- No data leaves the box

**For Product:**
- Non-technical user can operate without training
- Handles real-world messy CSV data
- Passes security audit for PII handling
- Brother (sales director) uses it daily
