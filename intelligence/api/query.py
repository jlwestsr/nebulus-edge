"""Query API endpoints.

Handles natural language questions and SQL execution.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

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


@router.post("/ask", response_model=IntelligenceResponse)
async def ask_question(
    request: Request,
    body: QuestionRequest,
) -> IntelligenceResponse:
    """
    Ask a natural language question about your data.

    The system automatically:
    1. Classifies the question type (SQL, semantic, strategic)
    2. Queries appropriate data sources
    3. Applies domain knowledge if needed
    4. Returns answer with supporting data
    """
    # TODO: Implement with orchestrator
    return IntelligenceResponse(
        answer="Question answering not yet implemented.",
        reasoning="The intelligence engine is still being built.",
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
    sql = body.sql.strip()

    # Safety check
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT statements are allowed",
        )

    # TODO: Implement with SQLEngine
    raise HTTPException(
        status_code=501,
        detail="SQL execution not yet implemented",
    )


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
