# Nebulus Intelligence - Architecture Sketch

**Date:** 2026-02-02
**Status:** Draft architecture sketch
**Purpose:** Reusable data intelligence platform with vertical templates

---

## Overview

Nebulus Intelligence is a new component that sits alongside Brain and Body, providing:
- Multi-source data ingestion and storage
- Domain knowledge management
- Hybrid query engine (SQL + Semantic)
- Strategic reasoning via Brain integration

```
┌─────────────────────────────────────────────────────────────────┐
│                         User (Open WebUI)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Body (Open WebUI)                           │
│                   Port 3000 (Docker)                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│         Brain             │   │        Intelligence           │
│     (LLM Server)          │   │    (Data + Knowledge)         │
│     Port 8080             │   │       Port 8081               │
│                           │   │                               │
│  - Chat completions       │   │  - Data ingestion             │
│  - Model management       │   │  - Query execution            │
│                           │   │  - Knowledge management       │
│                           │◄──│  - Calls Brain for reasoning  │
└───────────────────────────┘   └───────────────────────────────┘
         MLX                              SQLite + ChromaDB
```

---

## Directory Structure

```
nebulus-edge/
├── brain/                      # Existing LLM server
├── body/                       # Existing Open WebUI
├── intelligence/               # NEW
│   ├── __init__.py
│   ├── server.py               # FastAPI application
│   ├── requirements.txt
│   │
│   ├── core/                   # Core engine components
│   │   ├── __init__.py
│   │   ├── ingest.py           # CSV parsing, validation, import
│   │   ├── sql_engine.py       # SQLite wrapper, text-to-SQL
│   │   ├── vector_engine.py    # ChromaDB wrapper, embeddings
│   │   ├── knowledge.py        # Domain knowledge manager
│   │   ├── classifier.py       # Question type classification
│   │   └── orchestrator.py     # Routes queries to engines
│   │
│   ├── templates/              # Vertical configurations
│   │   ├── __init__.py
│   │   ├── base.py             # Base template class
│   │   ├── dealership/
│   │   │   ├── config.yaml     # Schema, rules, prompts
│   │   │   └── scoring.py      # Custom scoring logic
│   │   ├── medical/
│   │   │   ├── config.yaml
│   │   │   └── scoring.py
│   │   └── legal/
│   │       ├── config.yaml
│   │       └── scoring.py
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── data.py             # Upload, list, delete datasets
│   │   ├── query.py            # Ask questions
│   │   ├── knowledge.py        # Manage domain knowledge
│   │   └── admin.py            # Template management, health
│   │
│   └── storage/                # Data persistence (gitignored)
│       ├── databases/          # SQLite files per customer
│       ├── vectors/            # ChromaDB collections
│       └── knowledge/          # Domain knowledge JSON
│
├── infrastructure/
│   ├── pm2_config.json         # Add intelligence process
│   └── start_intelligence.sh   # Startup script
│
└── tests/
    └── intelligence/           # Tests for new component
        ├── test_ingest.py
        ├── test_sql_engine.py
        ├── test_orchestrator.py
        └── test_templates.py
```

---

## Core Components

### 1. Ingest (`core/ingest.py`)

Handles CSV upload, validation, and import into SQLite.

```python
class DataIngestor:
    """CSV ingestion with schema inference and primary key detection."""

    def ingest_csv(
        self,
        file_path: str,
        table_name: str,
        template: str = "generic",
        primary_key_hint: str | None = None
    ) -> IngestResult:
        """
        1. Parse CSV, infer column types
        2. Detect primary key (VIN, PatientID, CaseID based on template)
        3. Create/update SQLite table
        4. Generate embeddings for semantic search
        5. Return schema and row count
        """
        pass

    def detect_primary_key(self, df: DataFrame, template: str) -> str:
        """Auto-detect primary key based on template hints."""
        # Dealership: look for VIN, Stock#, StockNumber
        # Medical: look for PatientID, MRN, Patient_ID
        # Legal: look for CaseID, Case#, MatterID
        pass

    def infer_relationships(self, tables: list[str]) -> list[Relationship]:
        """Find foreign key relationships across tables."""
        pass
```

### 2. SQL Engine (`core/sql_engine.py`)

Wraps SQLite with natural language to SQL conversion.

```python
class SQLEngine:
    """Execute SQL queries with natural language interface."""

    def __init__(self, db_path: str, brain_url: str):
        self.conn = sqlite3.connect(db_path)
        self.brain_url = brain_url

    def get_schema(self) -> dict:
        """Return all tables, columns, types, relationships."""
        pass

    def natural_to_sql(self, question: str, schema: dict) -> str:
        """
        Call Brain to convert natural language to SQL.
        Include schema context in prompt.
        """
        prompt = f"""Given this database schema:
{schema}

Convert this question to SQL:
"{question}"

Return only valid SQLite SQL, no explanation."""

        response = self._call_brain(prompt)
        return self._extract_sql(response)

    def execute(self, sql: str, safe: bool = True) -> QueryResult:
        """
        Execute SQL with safety checks.
        If safe=True, only allow SELECT statements.
        """
        if safe and not sql.strip().upper().startswith("SELECT"):
            raise UnsafeQueryError("Only SELECT allowed")

        return self.conn.execute(sql).fetchall()

    def explain_results(self, question: str, sql: str, results: list) -> str:
        """Call Brain to explain query results in natural language."""
        pass
```

### 3. Vector Engine (`core/vector_engine.py`)

ChromaDB wrapper for semantic search.

```python
class VectorEngine:
    """Semantic search over business data."""

    def __init__(self, collection_name: str):
        self.client = chromadb.PersistentClient(path="./storage/vectors")
        self.collection = self.client.get_or_create_collection(collection_name)

    def embed_records(self, records: list[dict], id_field: str):
        """
        Convert records to embeddings and store.
        Each record becomes a document with metadata.
        """
        pass

    def search_similar(
        self,
        query: str,
        n_results: int = 10,
        filters: dict | None = None
    ) -> list[SimilarRecord]:
        """Find records semantically similar to query."""
        pass

    def find_patterns(self, positive_examples: list[str]) -> PatternResult:
        """
        Given IDs of 'good' records, find what they have in common.
        Useful for "what makes a good sale" type questions.
        """
        pass
```

### 4. Knowledge Manager (`core/knowledge.py`)

Stores and retrieves domain expertise.

```python
class KnowledgeManager:
    """Manage domain knowledge for a business."""

    def __init__(self, knowledge_path: str):
        self.path = knowledge_path
        self.knowledge = self._load()

    def get_scoring_factors(self) -> list[ScoringFactor]:
        """Return weighted factors for outcome scoring."""
        return self.knowledge.get("scoring_factors", [])

    def get_business_rules(self) -> list[BusinessRule]:
        """Return business rules and constraints."""
        return self.knowledge.get("rules", [])

    def get_metrics(self) -> list[MetricDefinition]:
        """Return metric definitions (targets, thresholds)."""
        return self.knowledge.get("metrics", [])

    def add_knowledge(self, category: str, item: dict):
        """Add new knowledge from user teaching."""
        pass

    def export_for_prompt(self) -> str:
        """Format knowledge for LLM context injection."""
        return f"""
Business Rules:
{self._format_rules()}

Scoring Factors (what makes a good outcome):
{self._format_scoring()}

Key Metrics:
{self._format_metrics()}
"""
```

### 5. Question Classifier (`core/classifier.py`)

Routes questions to the right engine(s).

```python
class QuestionClassifier:
    """Determine how to answer a question."""

    class QueryType(Enum):
        SQL_ONLY = "sql"           # "How many cars over 60 days?"
        SEMANTIC_ONLY = "semantic"  # "Find sales like this one"
        STRATEGIC = "strategic"     # "What's ideal inventory?"
        HYBRID = "hybrid"           # Needs multiple sources

    def classify(self, question: str, schema: dict) -> ClassificationResult:
        """
        Analyze question and determine:
        - Which engine(s) to use
        - What data to retrieve
        - Whether domain knowledge is needed
        """
        # Call Brain with classification prompt
        prompt = f"""Classify this business question:
"{question}"

Available data: {schema}

Is this:
1. SQL_ONLY - Can be answered with a database query (counts, filters, joins)
2. SEMANTIC_ONLY - Needs similarity/pattern search
3. STRATEGIC - Needs reasoning about "what's best" using business rules
4. HYBRID - Needs multiple approaches combined

Return JSON: {{"type": "...", "reasoning": "..."}}"""

        return self._parse_classification(self._call_brain(prompt))
```

### 6. Orchestrator (`core/orchestrator.py`)

The main entry point that coordinates everything.

```python
class IntelligenceOrchestrator:
    """Main query orchestrator - the brain of Intelligence."""

    def __init__(
        self,
        sql_engine: SQLEngine,
        vector_engine: VectorEngine,
        knowledge: KnowledgeManager,
        classifier: QuestionClassifier,
        brain_url: str,
        template: str = "generic"
    ):
        self.sql = sql_engine
        self.vectors = vector_engine
        self.knowledge = knowledge
        self.classifier = classifier
        self.brain_url = brain_url
        self.template = self._load_template(template)

    async def ask(self, question: str) -> IntelligenceResponse:
        """
        Main entry point for all questions.

        Returns:
            IntelligenceResponse with:
            - answer: Natural language response
            - supporting_data: Tables, charts
            - reasoning: How we got here
            - sql_used: For transparency (if applicable)
            - confidence: How sure we are
        """
        # 1. Classify the question
        classification = self.classifier.classify(question, self.sql.get_schema())

        # 2. Gather data based on classification
        context = await self._gather_context(question, classification)

        # 3. If strategic, inject domain knowledge
        if classification.type in [QueryType.STRATEGIC, QueryType.HYBRID]:
            context["knowledge"] = self.knowledge.export_for_prompt()

        # 4. Call Brain for final synthesis
        answer = await self._synthesize(question, context, classification)

        return IntelligenceResponse(
            answer=answer.text,
            supporting_data=context.get("data"),
            reasoning=answer.reasoning,
            sql_used=context.get("sql"),
            confidence=answer.confidence
        )

    async def _gather_context(
        self,
        question: str,
        classification: ClassificationResult
    ) -> dict:
        """Gather relevant data from appropriate engines."""
        context = {}

        if classification.needs_sql:
            sql = self.sql.natural_to_sql(question, self.sql.get_schema())
            results = self.sql.execute(sql)
            context["sql"] = sql
            context["sql_results"] = results

        if classification.needs_semantic:
            similar = self.vectors.search_similar(question)
            context["similar_records"] = similar

        return context

    async def _synthesize(
        self,
        question: str,
        context: dict,
        classification: ClassificationResult
    ) -> SynthesisResult:
        """Call Brain to synthesize final answer."""
        prompt = self._build_synthesis_prompt(question, context, classification)
        response = await self._call_brain(prompt)
        return self._parse_synthesis(response)
```

---

## Vertical Templates

### Template Structure (`templates/dealership/config.yaml`)

```yaml
# Dealership Vertical Template
name: dealership
display_name: "Auto Dealership"
version: "1.0"

# Primary key detection hints
primary_keys:
  - vin
  - VIN
  - stock_number
  - StockNumber
  - stock_no

# Expected data sources
data_sources:
  inventory:
    description: "Current vehicle inventory"
    required_columns:
      - vin
      - make
      - model
      - year
      - asking_price
    optional_columns:
      - days_on_lot
      - acquisition_cost
      - reconditioning_cost

  sales:
    description: "Historical sales records"
    required_columns:
      - vin
      - sale_date
      - sale_price
    optional_columns:
      - buyer_zip
      - trade_in
      - financing
      - warranty_sold
      - gross_profit

  service:
    description: "Service records"
    required_columns:
      - vin
      - service_date
    optional_columns:
      - service_type
      - revenue
      - customer_zip

# Default scoring factors
scoring:
  perfect_sale:
    local_buyer:
      description: "Buyer within 25 miles"
      weight: 15
      calculation: "buyer_zip proximity check"
    trade_in:
      description: "Trade-in accepted"
      weight: 20
      calculation: "trade_in IS NOT NULL"
    financing:
      description: "Dealer financing used"
      weight: 25
      calculation: "financing = true"
    warranty:
      description: "Extended warranty sold"
      weight: 15
      calculation: "warranty_sold = true"
    quick_turn:
      description: "Sold within 30 days"
      weight: 10
      calculation: "days_to_sale <= 30"
    above_margin:
      description: "Above target margin"
      weight: 15
      calculation: "gross_profit / sale_price > 0.15"

# Default business rules
rules:
  - name: "max_mileage"
    description: "Don't stock vehicles over 100k miles"
    condition: "mileage <= 100000"
  - name: "max_age"
    description: "Avoid vehicles older than 10 years"
    condition: "year >= CURRENT_YEAR - 10"
  - name: "target_margin"
    description: "Target 15% gross margin"
    value: 0.15

# Default metrics
metrics:
  days_on_lot:
    target: 45
    warning: 60
    critical: 90
  gross_margin:
    target: 0.15
    warning: 0.10
    critical: 0.05
  inventory_turn:
    target: 12  # per year
    warning: 8
    critical: 6

# Pre-built queries for this vertical
canned_queries:
  - name: "aged_inventory"
    question: "Which vehicles have been on the lot over 60 days?"
    sql: "SELECT * FROM inventory WHERE days_on_lot > 60 ORDER BY days_on_lot DESC"

  - name: "top_performers"
    question: "What were our most profitable sales last month?"
    sql: >
      SELECT * FROM sales
      WHERE sale_date >= date('now', '-30 days')
      ORDER BY gross_profit DESC LIMIT 10

  - name: "service_opportunities"
    question: "Which sold vehicles haven't returned for service?"
    sql: >
      SELECT s.* FROM sales s
      LEFT JOIN service sv ON s.vin = sv.vin
      WHERE sv.vin IS NULL
      AND s.sale_date < date('now', '-90 days')

# Prompts customized for this vertical
prompts:
  system: |
    You are an AI assistant for an auto dealership. You help analyze
    inventory, sales, and service data to make strategic business decisions.
    Always consider factors like days on lot, gross margin, and customer lifetime value.

  strategic_analysis: |
    When analyzing "ideal inventory", consider:
    1. Historical sales velocity by vehicle type
    2. Gross margin by category
    3. Customer demographics and preferences
    4. Seasonal trends
    5. Current inventory gaps
```

### Template Base Class (`templates/base.py`)

```python
from abc import ABC, abstractmethod
from pathlib import Path
import yaml

class VerticalTemplate(ABC):
    """Base class for vertical templates."""

    def __init__(self, template_dir: Path):
        self.config = self._load_config(template_dir / "config.yaml")
        self.name = self.config["name"]

    def _load_config(self, path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def get_primary_key_hints(self) -> list[str]:
        """Return column names that might be primary keys."""
        return self.config.get("primary_keys", [])

    def get_scoring_factors(self) -> dict:
        """Return scoring configuration."""
        return self.config.get("scoring", {})

    def get_business_rules(self) -> list[dict]:
        """Return business rules."""
        return self.config.get("rules", [])

    def get_metrics(self) -> dict:
        """Return metric definitions."""
        return self.config.get("metrics", {})

    def get_system_prompt(self) -> str:
        """Return customized system prompt."""
        return self.config.get("prompts", {}).get("system", "")

    @abstractmethod
    def calculate_score(self, record: dict) -> float:
        """Calculate outcome score for a record. Override per vertical."""
        pass

    @abstractmethod
    def validate_data(self, table_name: str, df) -> ValidationResult:
        """Validate uploaded data against template expectations."""
        pass
```

---

## API Endpoints

### `api/data.py` - Data Management

```python
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/data", tags=["data"])

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    table_name: str = None,
    template: str = "generic"
) -> IngestResult:
    """
    Upload a CSV file for analysis.

    - Auto-detects schema and primary key
    - Creates SQLite table
    - Generates embeddings for semantic search
    """
    pass

@router.get("/tables")
async def list_tables() -> list[TableInfo]:
    """List all uploaded data tables with schema info."""
    pass

@router.get("/tables/{table_name}/schema")
async def get_schema(table_name: str) -> SchemaInfo:
    """Get detailed schema for a table."""
    pass

@router.get("/tables/{table_name}/preview")
async def preview_data(table_name: str, limit: int = 10) -> list[dict]:
    """Preview rows from a table."""
    pass

@router.delete("/tables/{table_name}")
async def delete_table(table_name: str) -> dict:
    """Delete a table and its embeddings."""
    pass

@router.get("/relationships")
async def get_relationships() -> list[Relationship]:
    """Get detected relationships between tables."""
    pass
```

### `api/query.py` - Query Interface

```python
router = APIRouter(prefix="/query", tags=["query"])

@router.post("/ask")
async def ask_question(request: QuestionRequest) -> IntelligenceResponse:
    """
    Ask a natural language question about your data.

    The system automatically:
    1. Classifies the question type
    2. Queries appropriate data sources
    3. Applies domain knowledge if needed
    4. Returns answer with supporting data
    """
    return await orchestrator.ask(request.question)

@router.post("/sql")
async def execute_sql(request: SQLRequest) -> SQLResponse:
    """
    Execute raw SQL (for power users).
    Only SELECT statements allowed.
    """
    pass

@router.post("/similar")
async def find_similar(request: SimilarityRequest) -> list[SimilarRecord]:
    """
    Find records similar to a given example.

    Use cases:
    - "Find sales like this one"
    - "Find vehicles similar to VIN X"
    """
    pass

@router.get("/canned")
async def list_canned_queries() -> list[CannedQuery]:
    """List pre-built queries for current template."""
    pass

@router.post("/canned/{query_name}")
async def run_canned_query(query_name: str) -> QueryResult:
    """Run a pre-built query."""
    pass
```

### `api/knowledge.py` - Knowledge Management

```python
router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.get("/")
async def get_knowledge() -> KnowledgeBase:
    """Get all domain knowledge."""
    pass

@router.get("/scoring")
async def get_scoring_factors() -> list[ScoringFactor]:
    """Get outcome scoring factors and weights."""
    pass

@router.put("/scoring")
async def update_scoring(factors: list[ScoringFactor]) -> dict:
    """Update scoring factors (teach the system what's good)."""
    pass

@router.get("/rules")
async def get_business_rules() -> list[BusinessRule]:
    """Get business rules."""
    pass

@router.post("/rules")
async def add_rule(rule: BusinessRule) -> dict:
    """Add a new business rule."""
    pass

@router.get("/metrics")
async def get_metrics() -> list[MetricDefinition]:
    """Get metric definitions."""
    pass

@router.post("/teach")
async def teach(session: TeachingSession) -> dict:
    """
    Interactive teaching session.

    User provides examples of good/bad outcomes,
    system learns patterns.
    """
    pass

@router.post("/feedback")
async def record_feedback(feedback: RecommendationFeedback) -> dict:
    """
    Record feedback on a recommendation.
    Used to improve future suggestions.
    """
    pass
```

### `api/admin.py` - Administration

```python
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "running",
        "template": current_template,
        "tables": len(get_tables()),
        "brain_connected": check_brain_connection()
    }

@router.get("/templates")
async def list_templates() -> list[TemplateInfo]:
    """List available vertical templates."""
    pass

@router.post("/templates/{template_name}/activate")
async def activate_template(template_name: str) -> dict:
    """Switch to a different vertical template."""
    pass

@router.post("/export")
async def export_config() -> dict:
    """Export current configuration (for backup/migration)."""
    pass

@router.post("/import")
async def import_config(config: dict) -> dict:
    """Import configuration."""
    pass
```

---

## Server Entry Point (`server.py`)

```python
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.sql_engine import SQLEngine
from core.vector_engine import VectorEngine
from core.knowledge import KnowledgeManager
from core.classifier import QuestionClassifier
from core.orchestrator import IntelligenceOrchestrator
from api import data, query, knowledge, admin

# Configuration
BRAIN_URL = "http://localhost:8080"
TEMPLATE = "dealership"
DB_PATH = "./storage/databases/main.db"
VECTOR_PATH = "./storage/vectors"
KNOWLEDGE_PATH = "./storage/knowledge/knowledge.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup."""
    global orchestrator

    # Initialize engines
    sql_engine = SQLEngine(DB_PATH, BRAIN_URL)
    vector_engine = VectorEngine("main")
    knowledge_mgr = KnowledgeManager(KNOWLEDGE_PATH)
    classifier = QuestionClassifier(BRAIN_URL)

    # Create orchestrator
    orchestrator = IntelligenceOrchestrator(
        sql_engine=sql_engine,
        vector_engine=vector_engine,
        knowledge=knowledge_mgr,
        classifier=classifier,
        brain_url=BRAIN_URL,
        template=TEMPLATE
    )

    print(f"Intelligence ready with template: {TEMPLATE}")
    yield

    # Cleanup
    sql_engine.close()


app = FastAPI(
    title="Nebulus Intelligence",
    version="0.1.0",
    lifespan=lifespan
)

# Register routers
app.include_router(data.router)
app.include_router(query.router)
app.include_router(knowledge.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "service": "nebulus-intelligence",
        "status": "running",
        "template": TEMPLATE
    }


def main():
    uvicorn.run(app, host="0.0.0.0", port=8081)


if __name__ == "__main__":
    main()
```

---

## PM2 Configuration Update

```json
{
    "apps": [
        {
            "name": "nebulus-brain",
            "script": "./infrastructure/start_brain.sh",
            "interpreter": "none"
        },
        {
            "name": "nebulus-intelligence",
            "script": "./infrastructure/start_intelligence.sh",
            "interpreter": "none"
        }
    ]
}
```

---

## Integration with Open WebUI

### Option A: Custom Tool/Function
Open WebUI supports custom tools. Create a tool that calls Intelligence API:

```python
# Tool definition for Open WebUI
{
    "name": "query_business_data",
    "description": "Query your business data with natural language",
    "parameters": {
        "question": {
            "type": "string",
            "description": "Your question about the data"
        }
    }
}
```

### Option B: Proxy Through Brain
Add an endpoint in Brain that proxies to Intelligence:

```python
# In brain/server.py
@app.post("/v1/intelligence/ask")
async def intelligence_proxy(request: QuestionRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/query/ask",
            json=request.dict()
        )
        return response.json()
```

### Option C: Direct Integration (Nebulus Gantry)
When building Nebulus Gantry (custom UI), integrate Intelligence natively with dedicated data analysis views.

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
- [ ] Basic directory structure
- [ ] SQLite engine with text-to-SQL
- [ ] CSV ingestion
- [ ] Simple API endpoints
- [ ] Dealership template (config only)

### Phase 2: Knowledge Layer (Week 3-4)
- [ ] Knowledge manager
- [ ] Scoring system
- [ ] Business rules engine
- [ ] Teaching interface

### Phase 3: Semantic Search (Week 5-6)
- [ ] ChromaDB integration
- [ ] Embedding generation
- [ ] Similarity search
- [ ] Pattern detection

### Phase 4: Orchestration (Week 7-8)
- [ ] Question classifier
- [ ] Full orchestrator
- [ ] Strategic analysis
- [ ] Response synthesis

### Phase 5: Polish (Week 9-10)
- [ ] Open WebUI integration
- [ ] Additional templates
- [ ] Testing & documentation
- [ ] Security hardening

---

## Open Questions

1. **Embedding model**: Use Qwen via Brain, or dedicated embedding model?
2. **Multi-tenancy**: One instance per customer, or multi-tenant?
3. **UI for knowledge capture**: Build custom, or use Open WebUI chat?
4. **Data refresh**: Manual re-upload, or watch folder/API push?
