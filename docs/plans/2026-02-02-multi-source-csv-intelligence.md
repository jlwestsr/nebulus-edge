# Multi-Source CSV Intelligence - Design Discussion

**Date:** 2026-02-02
**Updated:** 2026-02-02
**Status:** Customer feedback received - Hybrid approach selected
**MVP Feature:** Multi-source data correlation with domain knowledge for inventory strategy

## Product Vision

**Nebulus Edge** is a privacy-first AI appliance for small businesses handling sensitive data:
- Target hardware: Mac mini (48GB RAM)
- Target customers: Sales directors, doctors, lawyers, accountants
- Key value: On-premise, turnkey, customer owns hardware
- Business model: Sell configured hardware + software

### Initial Use Case: Car Dealership (Modern Motorcars)
- Sales director needs strategic inventory analysis, not just data queries
- Multiple data sources: inventory, service records, sales history, financing, warranties
- All sources share VIN as primary key
- Contains PII - must stay on-premise
- **Primary Question**: "Based on historical sales, help me identify the ideal used vehicle inventory"

## Customer Feedback (Received)

### Q1: Speed & Accuracy vs. Flexibility?
**Answer:** "Both equally - I need both capabilities"

### Q2: Hardest question you'd ask?
**Answer:** "Based upon our historical sales, help me identify the ideal used vehicle inventory" (Inventory Strategy)

### Domain Knowledge Requirements
The agent needs to understand variables that contribute to a "perfect sale" at Modern Motorcars:
- **Local buyer** - Higher likelihood of service revenue, referrals
- **Trade-in** - Margin opportunity, inventory acquisition
- **Financing** - Dealer profit from financing arrangements
- **Warranty purchase** - Additional revenue stream
- **Profit margins** - Per-vehicle profitability
- **Age of inventory** - Carrying costs, depreciation risk
- **Reconditioning spend** - Investment vs. sale price delta

---

## Architecture Approaches Considered

### Approach 1: SQL Database + Natural Language to SQL

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
- **Cannot handle strategic/analytical questions** like "what's ideal inventory"

---

### Approach 2: RAG-based (Vector Database)

**Implementation:**
- CSVs → Parse into vector embeddings (ChromaDB/FAISS)
- VIN used for chunking/indexing
- User asks → Semantic search finds relevant rows → LLM analyzes

**Pros:**
- More flexible for unstructured questions
- Works well with current LLM setup
- Can find patterns and similarities

**Cons:**
- Struggles with complex joins or exact filters
- Less deterministic (business users may not trust it)
- Slower for large datasets

---

### Approach 3: Hybrid (SQL + RAG + Domain Knowledge) ⭐ SELECTED

**Implementation:**
- Structured data in SQLite for precise queries
- Vector DB for semantic search and pattern matching
- **Domain Knowledge Layer** for business rules and priorities
- LLM orchestrates all three based on question type

**Pros:**
- Best of both worlds - precision AND flexibility
- Can answer strategic questions requiring reasoning
- Domain knowledge makes recommendations business-relevant
- Transparent: can show SQL queries AND reasoning

**Cons:**
- Higher complexity (justified by requirements)
- Three systems to maintain
- Requires domain knowledge capture process

---

## Selected Architecture: Hybrid with Domain Knowledge

```
┌─────────────────────────────────────────────────────────────┐
│                      User Question                           │
│  "What's our ideal used vehicle inventory?"                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Question Classifier (LLM)                    │
│  Determines: SQL query? Semantic search? Strategic analysis? │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│  SQL Engine     │ │ Semantic Search │ │ Domain Knowledge    │
│  (SQLite)       │ │ (ChromaDB)      │ │ Layer               │
│                 │ │                 │ │                     │
│ - Exact queries │ │ - Similar sales │ │ - "Perfect sale"    │
│ - Aggregations  │ │ - Patterns      │ │   variables         │
│ - Joins on VIN  │ │ - Anomalies     │ │ - Business rules    │
│ - Inventory age │ │ - Market comps  │ │ - Weights/priorities│
└─────────────────┘ └─────────────────┘ └─────────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Reasoning Layer                         │
│  Synthesizes data + patterns + business rules into          │
│  actionable strategic recommendations                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Response                                │
│  "Based on your sales data, ideal inventory characteristics: │
│   - SUVs under $35k (67% of profitable sales)               │
│   - < 60 days old (avg margin 12% vs 4% after 90 days)      │
│   - Local trade-ins (2.3x service revenue vs auction buys)  │
│   [Show supporting data] [Show reasoning]"                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Domain Knowledge Layer Design

### Purpose
Capture the sales director's business expertise so the AI can reason about "what's good" not just "what is."

### Knowledge Categories

**1. Sale Quality Factors** (weighted scoring)
| Factor | Description | Weight |
|--------|-------------|--------|
| Local buyer | Customer within N miles | +15 |
| Trade-in | Vehicle accepted as trade | +20 |
| Financing | Dealer-arranged financing | +25 |
| Warranty | Extended warranty sold | +15 |
| Quick turn | Sold within 30 days | +10 |
| Above-margin | Profit > target margin | +15 |

**2. Inventory Health Metrics**
- Days on lot (target: < 45 days)
- Reconditioning ROI (spend vs. margin impact)
- Category mix (SUV/Sedan/Truck ratios)
- Price band distribution

**3. Business Rules**
- "Never stock vehicles > 100k miles"
- "Prioritize trade-ins over auction"
- "Target 15% gross margin on used"

### Knowledge Capture Methods
1. **Structured interview** - One-time setup conversation
2. **Document upload** - Business rules, SOPs, pricing guides
3. **Feedback loop** - "This recommendation was good/bad" learning

---

## Implementation Phases (Revised)

### Phase 1: Foundation (MVP)
- CSV upload interface in Open WebUI
- SQLite import with VIN auto-detection
- Basic natural language to SQL
- Query execution and result formatting
- **Deliverable**: Answer "How many vehicles over 60 days on lot?"

### Phase 2: Domain Knowledge Layer
- Knowledge capture interface (structured Q&A)
- Business rules storage (JSON/YAML)
- Sale quality scoring system
- **Deliverable**: Score historical sales by "quality"

### Phase 3: Semantic Search
- ChromaDB integration for vector storage
- Embed sales records for pattern matching
- Similar vehicle/sale finder
- **Deliverable**: "Find sales similar to this successful one"

### Phase 4: Strategic Analysis
- Question classifier (SQL vs semantic vs strategic)
- Multi-source reasoning
- Recommendation generation
- **Deliverable**: "What's our ideal inventory?" with reasoning

### Phase 5: Security & Privacy
- PII detection and masking
- Data encryption at rest
- Audit logging
- Access controls

### Phase 6: Continuous Learning
- Feedback capture on recommendations
- Knowledge refinement from outcomes
- Automated insight generation

---

## Technical Considerations

### Current Stack
- Brain: FastAPI + MLX (Qwen3-Coder-30B)
- Body: Open WebUI (Docker)
- Infrastructure: PM2 + Ansible

### Additions Needed

**Data Layer:**
- SQLite for structured data
- ChromaDB for vector embeddings
- JSON/YAML for domain knowledge

**Processing:**
- CSV parsing and validation
- Schema inference
- Text-to-SQL engine
- Embedding generation
- Query sandbox for safety

**New Components:**
- Question classifier
- Domain knowledge manager
- Multi-source orchestrator
- Recommendation synthesizer

### Security Requirements
- No data leaves the Mac mini
- Encryption at rest
- PII auto-detection
- Query result sanitization
- Audit trail

---

## Open Questions

1. **Knowledge capture UX** - How does the sales director "teach" the system?
   - Wizard-style interview?
   - Upload existing documents?
   - Natural conversation?

2. **What data sources exist?**
   - DMS exports (which system?)
   - Manual spreadsheets?
   - Update frequency?

3. **How to validate recommendations?**
   - Backtest against historical outcomes?
   - A/B test suggestions?

4. **"Ideal" definition** - Is it:
   - Fastest turn rate?
   - Highest margin?
   - Balanced portfolio?
   - All of the above with weights?

5. **Schema conflicts** - How to handle mismatched CSVs?

6. **Embedding model** - Use Qwen for embeddings or separate model?

---

## Success Criteria

**For MVP (Phase 1):**
- Upload 3+ CSVs with VIN column
- Ask natural language question requiring cross-source join
- Get accurate results in <5 seconds
- Results are verifiable (show SQL)
- No data leaves the box

**For Strategic Analysis (Phase 4):**
- Ask "What's our ideal inventory?"
- Get actionable recommendations with reasoning
- Recommendations align with captured business rules
- Sales director trusts and uses insights weekly

**For Product:**
- Non-technical user can operate without training
- Handles real-world messy CSV data
- Passes security audit for PII handling
- Sales director uses it daily for decisions

---

## Related Nebulus Projects

- **Nebulus Prime**: Linux version (server/datacenter)
- **Nebulus Gantry**: Custom web UI (Open WebUI fork)
- **Nebulus Atom**: AI agent system (Claude Desktop inspired)
