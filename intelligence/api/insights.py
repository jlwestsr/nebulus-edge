"""Insights API endpoints.

Provides automated insight generation and retrieval.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from nebulus_core.intelligence.core.insights import InsightGenerator
from nebulus_core.intelligence.core.knowledge import KnowledgeManager
from nebulus_core.intelligence.templates import load_template

router = APIRouter(prefix="/insights", tags=["insights"])


class InsightResponse(BaseModel):
    """A single insight."""

    insight_type: str
    priority: str
    title: str
    description: str
    data_points: Dict[str, Any]
    recommendations: List[str]
    generated_at: str
    table_name: Optional[str] = None
    category: Optional[str] = None


class InsightReportResponse(BaseModel):
    """Full insight report."""

    generated_at: str
    tables_analyzed: List[str]
    insights: List[InsightResponse]
    summary: str
    insight_count: int
    by_priority: Dict[str, int]
    by_type: Dict[str, int]


def _get_insight_generator(request: Request) -> InsightGenerator:
    """Get an InsightGenerator instance."""
    db_path = request.app.state.db_path / "main.db"
    knowledge_path = request.app.state.knowledge_path / "knowledge.json"
    template_name = request.app.state.template

    # Load knowledge manager
    try:
        template = load_template(template_name)
        km = KnowledgeManager(knowledge_path, template.config)
    except Exception:
        km = None

    return InsightGenerator(db_path, km)


@router.get("/generate", response_model=InsightReportResponse)
def generate_insights(
    request: Request,
    tables: Optional[str] = None,
) -> InsightReportResponse:
    """
    Generate insights from data analysis.

    Analyzes all tables (or specified ones) to identify:
    - Trends and patterns
    - Anomalies and outliers
    - Opportunities
    - Risks requiring attention

    Args:
        tables: Comma-separated list of table names (optional)
    """
    generator = _get_insight_generator(request)

    table_list = None
    if tables:
        table_list = [t.strip() for t in tables.split(",")]

    report = generator.generate_insights(table_list)
    data = report.to_dict()

    return InsightReportResponse(
        generated_at=data["generated_at"],
        tables_analyzed=data["tables_analyzed"],
        insights=[
            InsightResponse(
                insight_type=i["insight_type"],
                priority=i["priority"],
                title=i["title"],
                description=i["description"],
                data_points=i["data_points"],
                recommendations=i["recommendations"],
                generated_at=i["generated_at"],
                table_name=i.get("table_name"),
                category=i.get("category"),
            )
            for i in data["insights"]
        ],
        summary=data["summary"],
        insight_count=data["insight_count"],
        by_priority=data["by_priority"],
        by_type=data["by_type"],
    )


@router.get("/high-priority", response_model=List[InsightResponse])
def get_high_priority_insights(
    request: Request,
    tables: Optional[str] = None,
) -> List[InsightResponse]:
    """
    Get only high and critical priority insights.

    Use this for a quick overview of items requiring immediate attention.
    """
    generator = _get_insight_generator(request)

    table_list = None
    if tables:
        table_list = [t.strip() for t in tables.split(",")]

    insights = generator.get_high_priority_insights(table_list)

    return [
        InsightResponse(
            insight_type=i.insight_type.value,
            priority=i.priority.value,
            title=i.title,
            description=i.description,
            data_points=i.data_points,
            recommendations=i.recommendations,
            generated_at=i.generated_at.isoformat(),
            table_name=i.table_name,
            category=i.category,
        )
        for i in insights
    ]


@router.get("/category/{category}", response_model=List[InsightResponse])
def get_insights_by_category(
    request: Request,
    category: str,
    tables: Optional[str] = None,
) -> List[InsightResponse]:
    """
    Get insights for a specific category.

    Categories include:
    - inventory_health
    - sales_performance
    - pricing
    - etc.
    """
    generator = _get_insight_generator(request)

    table_list = None
    if tables:
        table_list = [t.strip() for t in tables.split(",")]

    insights = generator.get_insights_by_category(category, table_list)

    return [
        InsightResponse(
            insight_type=i.insight_type.value,
            priority=i.priority.value,
            title=i.title,
            description=i.description,
            data_points=i.data_points,
            recommendations=i.recommendations,
            generated_at=i.generated_at.isoformat(),
            table_name=i.table_name,
            category=i.category,
        )
        for i in insights
    ]


@router.get("/summary")
def get_insight_summary(request: Request) -> dict:
    """
    Get a quick summary of insights.

    Returns counts by priority and type without full insight details.
    """
    generator = _get_insight_generator(request)
    report = generator.generate_insights()

    return {
        "summary": report.summary,
        "total_insights": len(report.insights),
        "by_priority": report._count_by_priority(),
        "by_type": report._count_by_type(),
        "tables_analyzed": report.tables_analyzed,
    }
