"""Query API endpoints.

Handles natural language questions and SQL execution.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from intelligence.core.knowledge import KnowledgeManager
from intelligence.core.scoring import SaleScorer
from intelligence.core.sql_engine import SQLEngine, UnsafeQueryError
from intelligence.templates import load_template

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
    brain_url = request.app.state.brain_url
    return SQLEngine(db_path, brain_url)


@router.post("/ask", response_model=IntelligenceResponse)
async def ask_question(
    request: Request,
    body: QuestionRequest,
) -> IntelligenceResponse:
    """
    Ask a natural language question about your data.

    The system automatically:
    1. Converts the question to SQL using the Brain LLM
    2. Executes the query
    3. Explains the results in natural language
    """
    sql_engine = _get_sql_engine(request)

    try:
        # Convert question to SQL
        sql = await sql_engine.natural_to_sql(body.question)

        # Execute the SQL
        result = sql_engine.execute(sql)

        # Convert rows to list of dicts for supporting_data
        supporting_data = None
        if result.rows:
            supporting_data = [
                dict(zip(result.columns, row)) for row in result.rows[:20]
            ]

        # Get explanation from Brain
        explanation = await sql_engine.explain_results(body.question, sql, result)

        return IntelligenceResponse(
            answer=explanation,
            supporting_data=supporting_data,
            reasoning=f"Executed SQL query against {result.row_count} matching rows.",
            sql_used=sql,
            confidence=0.85,
        )

    except UnsafeQueryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return IntelligenceResponse(
            answer=f"I encountered an error processing your question: {str(e)}",
            reasoning="The query could not be completed.",
            confidence=0.0,
        )


@router.post("/sql", response_model=SQLResponse)
async def execute_sql(
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
        return SQLResponse(
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            sql=result.sql,
        )
    except UnsafeQueryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/similar")
async def find_similar(
    request: Request,
    record_id: str,
    table_name: str,
    limit: int = 10,
) -> list[dict]:
    """
    Find records similar to a given example.

    Use cases:
    - "Find sales like this one"
    - "Find vehicles similar to VIN X"
    """
    # TODO: Implement with VectorEngine
    raise HTTPException(
        status_code=501,
        detail="Similarity search not yet implemented",
    )


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
async def score_records(
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
