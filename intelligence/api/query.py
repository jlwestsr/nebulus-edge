"""Query API endpoints.

Handles natural language questions and SQL execution.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from nebulus_core.intelligence.core.audit import AuditEvent, AuditEventType
from nebulus_core.intelligence.core.classifier import QuestionClassifier
from nebulus_core.intelligence.core.knowledge import KnowledgeManager
from nebulus_core.intelligence.core.orchestrator import IntelligenceOrchestrator
from nebulus_core.intelligence.core.scoring import SaleScorer
from nebulus_core.intelligence.core.sql_engine import SQLEngine, UnsafeQueryError
from nebulus_core.intelligence.core.vector_engine import VectorEngine
from nebulus_core.intelligence.templates import load_template

router = APIRouter(prefix="/query", tags=["query"])


class QuestionRequest(BaseModel):
    """Request to ask a natural language question."""

    question: str


class IntelligenceResponse(BaseModel):
    """Response from the intelligence engine."""

    answer: str
    supporting_data: Optional[list[dict]] = None
    reasoning: Optional[str] = None
    sql_used: Optional[str] = None
    similar_records: Optional[list[dict]] = None
    classification: Optional[str] = None
    confidence: float = 0.0


class SQLRequest(BaseModel):
    """Request to execute raw SQL."""

    sql: str


class SQLResponse(BaseModel):
    """Response from SQL execution."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    sql: str


def _get_sql_engine(request: Request) -> SQLEngine:
    """Get a SQLEngine instance."""
    db_path = request.app.state.db_path / "main.db"
    llm = request.app.state.llm
    model = request.app.state.model
    return SQLEngine(db_path, llm, model)


def _get_vector_engine(request: Request) -> VectorEngine:
    """Get a VectorEngine instance."""
    vector_client = request.app.state.vector_client
    return VectorEngine(vector_client)


def _get_orchestrator(request: Request) -> IntelligenceOrchestrator:
    """Get an IntelligenceOrchestrator instance."""
    db_path = request.app.state.db_path / "main.db"
    knowledge_path = request.app.state.knowledge_path / "knowledge.json"
    template_name = request.app.state.template
    llm = request.app.state.llm
    model = request.app.state.model
    vector_client = request.app.state.vector_client

    # Load template config
    try:
        template = load_template(template_name)
        template_config = template.config
    except Exception:
        template_config = None

    # Build component objects for the orchestrator
    classifier = QuestionClassifier(llm, model)
    sql_engine = SQLEngine(db_path, llm, model)
    vector_engine = VectorEngine(vector_client)
    knowledge = KnowledgeManager(knowledge_path, template_config)

    return IntelligenceOrchestrator(
        classifier=classifier,
        sql_engine=sql_engine,
        vector_engine=vector_engine,
        knowledge=knowledge,
        llm=llm,
        model=model,
    )


def _audit_log_query_operation(
    request: Request,
    event_type: AuditEventType,
    query: str,
    action: str,
    details: dict,
    success: bool,
    error: Optional[str] = None,
):
    """Helper to log query operations to audit log."""
    if not hasattr(request.app.state, "audit_logger"):
        return
    if not request.app.state.audit_config.enabled:
        return

    audit_logger = request.app.state.audit_logger

    # Extract context from middleware
    user_id = getattr(request.state, "user_id", "unknown")
    session_id = getattr(request.state, "session_id", None)
    ip_address = getattr(request.state, "ip_address", None)
    request_hash = getattr(request.state, "request_hash", None)
    response_hash = getattr(request.state, "response_hash", None)

    # Hash the query to avoid logging sensitive data
    query_hash = hashlib.sha256(query.encode()).hexdigest()

    # Add hashes to details
    audit_details = {**details, "query_hash": query_hash}
    if request_hash:
        audit_details["request_hash"] = request_hash
    if response_hash:
        audit_details["response_hash"] = response_hash

    # Create and log audit event
    event = AuditEvent(
        event_type=event_type,
        timestamp=datetime.now(),
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        resource="query",
        action=action,
        details=audit_details,
        success=success,
        error_message=error,
    )
    audit_logger.log(event)


@router.post("/ask", response_model=IntelligenceResponse)
def ask_question(
    request: Request,
    body: QuestionRequest,
) -> IntelligenceResponse:
    """
    Ask a natural language question about your data.

    The system automatically:
    1. Classifies the question (SQL, semantic, strategic, or hybrid)
    2. Gathers context from appropriate engines
    3. Injects domain knowledge for strategic questions
    4. Synthesizes a comprehensive answer

    Handles all question types:
    - Data queries: "How many vehicles over 60 days?"
    - Similarity: "Find sales like this one"
    - Strategic: "What's our ideal inventory?"
    """
    orchestrator = _get_orchestrator(request)

    try:
        # Use simple rule-based classification for faster response
        result = orchestrator.ask(body.question, use_simple_classification=True)

        # Log successful query
        _audit_log_query_operation(
            request=request,
            event_type=AuditEventType.QUERY_NATURAL,
            query=body.question,
            action="ask_question",
            details={
                "classification": result.classification,
                "sql_used": bool(result.sql_used),
                "rows_returned": len(result.supporting_data or []),
            },
            success=True,
        )

        return IntelligenceResponse(
            answer=result.answer,
            supporting_data=result.supporting_data,
            reasoning=result.reasoning,
            sql_used=result.sql_used,
            similar_records=result.similar_records,
            classification=result.classification,
            confidence=result.confidence,
        )

    except Exception as e:
        # Log failed query
        _audit_log_query_operation(
            request=request,
            event_type=AuditEventType.QUERY_NATURAL,
            query=body.question,
            action="ask_question",
            details={},
            success=False,
            error=str(e),
        )

        return IntelligenceResponse(
            answer=f"I encountered an error processing your question: {str(e)}",
            reasoning="The query could not be completed.",
            confidence=0.0,
        )


@router.post("/sql", response_model=SQLResponse)
def execute_sql(
    request: Request,
    body: SQLRequest,
) -> SQLResponse:
    """
    Execute raw SQL (for power users).

    Only SELECT statements are allowed for safety.
    """
    sql_engine = _get_sql_engine(request)

    try:
        result = sql_engine.execute(body.sql, safe=True)

        # Log successful SQL execution
        _audit_log_query_operation(
            request=request,
            event_type=AuditEventType.QUERY_SQL,
            query=body.sql,
            action="execute_sql",
            details={"rows_returned": result.row_count},
            success=True,
        )

        return SQLResponse(
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            sql=result.sql,
        )
    except UnsafeQueryError as e:
        # Log unsafe query attempt
        _audit_log_query_operation(
            request=request,
            event_type=AuditEventType.QUERY_SQL,
            query=body.sql,
            action="execute_sql",
            details={},
            success=False,
            error=f"Unsafe query: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log failed query
        _audit_log_query_operation(
            request=request,
            event_type=AuditEventType.QUERY_SQL,
            query=body.sql,
            action="execute_sql",
            details={},
            success=False,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


class SimilarityRequest(BaseModel):
    """Request for similarity search."""

    table_name: str
    query: Optional[str] = None
    record_id: Optional[str] = None
    limit: int = 10


class SimilarRecordResponse(BaseModel):
    """A similar record with similarity score."""

    id: str
    record: Dict[str, Any]
    similarity: float


@router.post("/similar")
def find_similar(
    request: Request,
    body: SimilarityRequest,
) -> List[SimilarRecordResponse]:
    """
    Find records similar to a query or an existing record.

    Provide either:
    - query: Natural language description to match against
    - record_id: ID of an existing record to find similar ones

    Use cases:
    - "Find sales like this one" (by record_id)
    - "Find vehicles similar to: low mileage SUV under $30k" (by query)
    """
    vector_engine = _get_vector_engine(request)

    # Check if collection exists
    if body.table_name not in vector_engine.list_collections():
        raise HTTPException(
            status_code=404,
            detail=f"No embeddings found for table '{body.table_name}'. "
            "Re-upload the CSV to generate embeddings.",
        )

    if body.record_id:
        # Search by example record
        results = vector_engine.search_by_example(
            table_name=body.table_name,
            record_id=body.record_id,
            n_results=body.limit,
        )
        query_str = f"record_id:{body.record_id}"
    elif body.query:
        # Search by natural language query
        results = vector_engine.search_similar(
            table_name=body.table_name,
            query=body.query,
            n_results=body.limit,
        )
        query_str = body.query
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'query' or 'record_id' must be provided",
        )

    # Log semantic search
    _audit_log_query_operation(
        request=request,
        event_type=AuditEventType.QUERY_SEMANTIC,
        query=query_str,
        action="find_similar",
        details={
            "table_name": body.table_name,
            "rows_returned": len(results),
        },
        success=True,
    )

    return [
        SimilarRecordResponse(
            id=r.id,
            record=r.record,
            similarity=r.similarity,
        )
        for r in results
    ]


class ScoreRequest(BaseModel):
    """Request to score records."""

    table_name: str
    category: str = "perfect_sale"
    limit: Optional[int] = None


class ScoredRecordResponse(BaseModel):
    """A single scored record."""

    record: Dict[str, Any]
    total_score: float
    max_possible: float
    percentage: float
    factor_scores: Dict[str, float]
    factor_details: Dict[str, str]


class ScoreResponse(BaseModel):
    """Response from scoring operation."""

    records: List[ScoredRecordResponse]
    distribution: Dict[str, Any]
    factor_performance: Dict[str, Dict[str, Any]]
    category: str
    total_records: int


def _get_knowledge_manager(request: Request) -> KnowledgeManager:
    """Get or create a KnowledgeManager instance."""
    knowledge_path = request.app.state.knowledge_path / "knowledge.json"
    template_name = request.app.state.template

    try:
        template = load_template(template_name)
        template_config = template.config
    except Exception:
        template_config = None

    return KnowledgeManager(knowledge_path, template_config)


@router.post("/score", response_model=ScoreResponse)
def score_records(
    request: Request,
    body: ScoreRequest,
) -> ScoreResponse:
    """
    Score records in a table based on domain knowledge criteria.

    Uses the "perfect sale" scoring factors (or custom category) to
    evaluate each record and provide quality scores.

    Returns:
    - Scored records sorted by quality (highest first)
    - Score distribution statistics
    - Factor performance analysis
    """
    db_path = request.app.state.db_path / "main.db"

    if not db_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No database found. Upload data first.",
        )

    km = _get_knowledge_manager(request)
    scorer = SaleScorer(db_path, km, category=body.category)

    try:
        # Score all records in the table
        scored = scorer.score_table(
            body.table_name,
            limit=body.limit,
            order_by_score=True,
        )

        # Get distribution and factor performance
        distribution = scorer.get_score_distribution(body.table_name)
        factor_performance = scorer.get_factor_performance(body.table_name)

        return ScoreResponse(
            records=[
                ScoredRecordResponse(
                    record=s.record,
                    total_score=s.total_score,
                    max_possible=s.max_possible,
                    percentage=s.percentage,
                    factor_scores=s.factor_scores,
                    factor_details=s.factor_details,
                )
                for s in scored
            ],
            distribution=distribution,
            factor_performance=factor_performance,
            category=body.category,
            total_records=len(scored),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}",
        )


class PatternRequest(BaseModel):
    """Request to find patterns in records."""

    table_name: str
    record_ids: List[str]


class PatternResponse(BaseModel):
    """Response with detected patterns."""

    sample_count: int
    frequent_values: Dict[str, Dict[str, int]]
    numeric_ranges: Dict[str, Dict[str, float]]


@router.post("/patterns")
def find_patterns(
    request: Request,
    body: PatternRequest,
) -> PatternResponse:
    """
    Analyze what a set of records have in common.

    Useful for questions like:
    - "What do our best sales have in common?"
    - "What patterns exist in high-margin vehicles?"

    Provide IDs of "good" example records to analyze.
    """
    vector_engine = _get_vector_engine(request)

    if body.table_name not in vector_engine.list_collections():
        raise HTTPException(
            status_code=404,
            detail=f"No embeddings found for table '{body.table_name}'. "
            "Re-upload the CSV to generate embeddings.",
        )

    if not body.record_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one record_id must be provided",
        )

    result = vector_engine.find_patterns(
        table_name=body.table_name,
        positive_ids=body.record_ids,
    )

    return PatternResponse(
        sample_count=result.sample_count,
        frequent_values=result.frequent_values,
        numeric_ranges=result.numeric_ranges,
    )
