"""Feedback API endpoints.

Handles feedback submission and retrieval for continuous learning.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from nebulus_core.intelligence.core.feedback import (
    FeedbackManager,
    FeedbackRating,
    FeedbackType,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackSubmission(BaseModel):
    """Request to submit feedback."""

    feedback_type: str = Field(
        ...,
        description="Type: query_result, recommendation, scoring, insight",
    )
    rating: int = Field(
        ...,
        ge=-2,
        le=2,
        description="Rating: -2 (very negative) to +2 (very positive)",
    )
    query: Optional[str] = Field(None, description="The original query")
    response: Optional[str] = Field(None, description="The system response")
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context (table name, SQL used, etc.)",
    )
    comment: Optional[str] = Field(None, description="Optional user comment")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    feedback_id: int
    message: str


class OutcomeSubmission(BaseModel):
    """Request to record an outcome."""

    feedback_id: int
    outcome: str = Field(..., description="Description of the actual outcome")


class FeedbackSummaryResponse(BaseModel):
    """Summary of feedback statistics."""

    total_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_rating: float
    satisfaction_rate: float
    by_type: Dict[str, int]
    recent_comments: List[str]


class RefinementSuggestions(BaseModel):
    """Suggestions for knowledge refinement."""

    total_feedback: int
    satisfaction_rate: float
    positive_count: int
    negative_count: int
    scoring_feedback: Dict[str, Dict[str, Any]]
    outcome_tracking: Dict[str, Any]
    suggestions: List[str]


def _get_feedback_manager(request: Request) -> FeedbackManager:
    """Get or create a FeedbackManager instance."""
    feedback_path = request.app.state.feedback_path / "feedback.db"
    return FeedbackManager(feedback_path)


@router.post("/submit", response_model=FeedbackResponse)
def submit_feedback(
    request: Request,
    body: FeedbackSubmission,
) -> FeedbackResponse:
    """
    Submit feedback on a query result or recommendation.

    Use this to rate the helpfulness of system responses:
    - rating: -2 (very unhelpful) to +2 (very helpful)
    - Include context to help identify patterns
    - Optional comment for detailed feedback
    """
    manager = _get_feedback_manager(request)

    try:
        feedback_type = FeedbackType(body.feedback_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback type. Must be one of: "
            f"{[t.value for t in FeedbackType]}",
        )

    try:
        rating = FeedbackRating(body.rating)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid rating. Must be between -2 and +2",
        )

    feedback_id = manager.submit_feedback(
        feedback_type=feedback_type,
        rating=rating,
        query=body.query,
        response=body.response,
        context=body.context,
        comment=body.comment,
    )

    return FeedbackResponse(
        feedback_id=feedback_id,
        message="Thank you for your feedback!",
    )


@router.post("/outcome", response_model=dict)
def record_outcome(
    request: Request,
    body: OutcomeSubmission,
) -> dict:
    """
    Record the actual outcome for a previous recommendation.

    This helps track whether recommendations led to good results,
    enabling the system to learn from real-world outcomes.
    """
    manager = _get_feedback_manager(request)

    success = manager.record_outcome(body.feedback_id, body.outcome)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Feedback entry {body.feedback_id} not found",
        )

    return {
        "status": "recorded",
        "feedback_id": body.feedback_id,
        "message": "Outcome recorded successfully",
    }


@router.get("/summary", response_model=FeedbackSummaryResponse)
def get_feedback_summary(
    request: Request,
    feedback_type: Optional[str] = None,
    days: int = 30,
) -> FeedbackSummaryResponse:
    """
    Get summary statistics for feedback.

    Returns:
    - Total feedback count
    - Positive/negative/neutral breakdown
    - Average rating and satisfaction rate
    - Breakdown by feedback type
    - Recent comments
    """
    manager = _get_feedback_manager(request)

    fb_type = None
    if feedback_type:
        try:
            fb_type = FeedbackType(feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type: {feedback_type}",
            )

    summary = manager.get_summary(feedback_type=fb_type, days=days)

    satisfaction_rate = (
        summary.positive_count / summary.total_count if summary.total_count > 0 else 0.0
    )

    return FeedbackSummaryResponse(
        total_count=summary.total_count,
        positive_count=summary.positive_count,
        negative_count=summary.negative_count,
        neutral_count=summary.neutral_count,
        average_rating=summary.average_rating,
        satisfaction_rate=satisfaction_rate,
        by_type=summary.by_type,
        recent_comments=summary.recent_comments,
    )


@router.get("/patterns")
def get_negative_patterns(
    request: Request,
    feedback_type: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get patterns in negative feedback.

    Identifies queries or contexts that received negative feedback,
    helping to pinpoint areas for improvement.
    """
    manager = _get_feedback_manager(request)

    fb_type = None
    if feedback_type:
        try:
            fb_type = FeedbackType(feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type: {feedback_type}",
            )

    return manager.get_negative_feedback_patterns(
        feedback_type=fb_type,
        limit=limit,
    )


@router.get("/refinement", response_model=RefinementSuggestions)
def get_refinement_suggestions(
    request: Request,
) -> RefinementSuggestions:
    """
    Get suggestions for knowledge refinement based on feedback.

    Analyzes feedback patterns to suggest:
    - Scoring weight adjustments
    - Business rule modifications
    - Areas needing attention
    """
    manager = _get_feedback_manager(request)
    analysis = manager.get_feedback_for_refinement()

    return RefinementSuggestions(
        total_feedback=analysis["total_feedback"],
        satisfaction_rate=analysis["satisfaction_rate"],
        positive_count=analysis["positive_count"],
        negative_count=analysis["negative_count"],
        scoring_feedback=analysis["scoring_feedback"],
        outcome_tracking=analysis["outcome_tracking"],
        suggestions=analysis["suggestions"],
    )


@router.get("/history")
def get_feedback_history(
    request: Request,
    feedback_type: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get feedback history with optional filters.

    Allows reviewing past feedback for analysis.
    """
    manager = _get_feedback_manager(request)

    fb_type = None
    if feedback_type:
        try:
            fb_type = FeedbackType(feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type: {feedback_type}",
            )

    min_rat = FeedbackRating(min_rating) if min_rating is not None else None
    max_rat = FeedbackRating(max_rating) if max_rating is not None else None

    feedback_list = manager.get_feedback(
        feedback_type=fb_type,
        min_rating=min_rat,
        max_rating=max_rat,
        limit=limit,
        offset=offset,
    )

    return [fb.to_dict() for fb in feedback_list]
