"""Query API endpoints.

Handles natural language questions and SQL execution.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from intelligence.core.sql_engine import SQLEngine, UnsafeQueryError

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
