"""Knowledge management API endpoints.

Handles domain knowledge: scoring factors, business rules, metrics.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from nebulus_core.intelligence.core.feedback import FeedbackManager
from nebulus_core.intelligence.core.knowledge import KnowledgeManager
from nebulus_core.intelligence.core.refinement import KnowledgeRefiner, WeightAdjustment
from nebulus_core.intelligence.templates import load_template

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class ScoringFactorModel(BaseModel):
    """Scoring factor model."""

    name: str
    description: str
    weight: int
    calculation: str


class BusinessRuleModel(BaseModel):
    """Business rule model."""

    name: str
    description: str
    condition: str
    severity: str = "warning"


class MetricModel(BaseModel):
    """Metric model."""

    name: str
    description: str
    target: float
    warning: float
    critical: float
    lower_is_better: bool = True


class UpdateScoringFactorRequest(BaseModel):
    """Request to update a scoring factor."""

    weight: Optional[int] = None
    description: Optional[str] = None


class AddRuleRequest(BaseModel):
    """Request to add a business rule."""

    name: str
    description: str
    condition: str
    severity: str = "warning"


class AddCustomKnowledgeRequest(BaseModel):
    """Request to add custom knowledge."""

    key: str
    value: Any


def _get_knowledge_manager(request: Request) -> KnowledgeManager:
    """Get or create a KnowledgeManager instance."""
    knowledge_path = request.app.state.knowledge_path / "knowledge.json"
    template_name = request.app.state.template

    # Load template config
    try:
        template = load_template(template_name)
        template_config = template.config
    except Exception:
        template_config = None

    return KnowledgeManager(knowledge_path, template_config)


@router.get("/")
def get_knowledge(request: Request) -> dict:
    """Get all domain knowledge."""
    km = _get_knowledge_manager(request)
    return km.to_dict()


@router.get("/scoring")
def get_scoring_factors(
    request: Request,
    category: str = "perfect_sale",
) -> List[dict]:
    """Get scoring factors for a category."""
    km = _get_knowledge_manager(request)
    factors = km.get_scoring_factors(category)
    return [
        {
            "name": f.name,
            "description": f.description,
            "weight": f.weight,
            "calculation": f.calculation,
        }
        for f in factors
    ]


@router.get("/scoring/all")
def get_all_scoring_factors(request: Request) -> Dict[str, List[dict]]:
    """Get all scoring factors for all categories."""
    km = _get_knowledge_manager(request)
    all_factors = km.get_all_scoring_factors()
    return {
        category: [
            {
                "name": f.name,
                "description": f.description,
                "weight": f.weight,
                "calculation": f.calculation,
            }
            for f in factors
        ]
        for category, factors in all_factors.items()
    }


@router.put("/scoring/{category}/{factor_name}")
def update_scoring_factor(
    request: Request,
    category: str,
    factor_name: str,
    body: UpdateScoringFactorRequest,
) -> dict:
    """Update a scoring factor's weight or description."""
    km = _get_knowledge_manager(request)

    success = km.update_scoring_factor(
        category=category,
        name=factor_name,
        weight=body.weight,
        description=body.description,
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Factor '{factor_name}' not found in category '{category}'",
        )

    return {"status": "updated", "factor": factor_name}


@router.get("/rules")
def get_business_rules(request: Request) -> List[dict]:
    """Get all business rules."""
    km = _get_knowledge_manager(request)
    rules = km.get_business_rules()
    return [
        {
            "name": r.name,
            "description": r.description,
            "condition": r.condition,
            "severity": r.severity,
        }
        for r in rules
    ]


@router.post("/rules")
def add_business_rule(
    request: Request,
    body: AddRuleRequest,
) -> dict:
    """Add a new business rule."""
    km = _get_knowledge_manager(request)

    rule = km.add_business_rule(
        name=body.name,
        description=body.description,
        condition=body.condition,
        severity=body.severity,
    )

    return {
        "status": "created",
        "rule": {
            "name": rule.name,
            "description": rule.description,
            "condition": rule.condition,
            "severity": rule.severity,
        },
    }


@router.get("/metrics")
def get_metrics(request: Request) -> Dict[str, dict]:
    """Get all metrics."""
    km = _get_knowledge_manager(request)
    metrics = km.get_metrics()
    return {
        name: {
            "description": m.description,
            "target": m.target,
            "warning": m.warning,
            "critical": m.critical,
            "lower_is_better": m.lower_is_better,
        }
        for name, m in metrics.items()
    }


@router.get("/metrics/{metric_name}")
def get_metric(request: Request, metric_name: str) -> dict:
    """Get a specific metric."""
    km = _get_knowledge_manager(request)
    metric = km.get_metric(metric_name)

    if not metric:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found",
        )

    return {
        "name": metric.name,
        "description": metric.description,
        "target": metric.target,
        "warning": metric.warning,
        "critical": metric.critical,
        "lower_is_better": metric.lower_is_better,
    }


@router.post("/custom")
def add_custom_knowledge(
    request: Request,
    body: AddCustomKnowledgeRequest,
) -> dict:
    """Add custom knowledge."""
    km = _get_knowledge_manager(request)
    km.add_custom_knowledge(body.key, body.value)
    return {"status": "added", "key": body.key}


@router.get("/custom/{key}")
def get_custom_knowledge(request: Request, key: str) -> dict:
    """Get custom knowledge by key."""
    km = _get_knowledge_manager(request)
    value = km.get_custom_knowledge(key)

    if value is None:
        raise HTTPException(
            status_code=404,
            detail=f"Custom knowledge '{key}' not found",
        )

    return {"key": key, "value": value}


@router.get("/prompt")
def get_knowledge_prompt(request: Request) -> dict:
    """Get domain knowledge formatted for LLM prompt injection."""
    km = _get_knowledge_manager(request)
    return {"prompt": km.export_for_prompt()}


def _get_refiner(request: Request) -> KnowledgeRefiner:
    """Get a KnowledgeRefiner instance."""
    km = _get_knowledge_manager(request)
    feedback_path = request.app.state.feedback_path / "feedback.db"
    fm = FeedbackManager(feedback_path)
    return KnowledgeRefiner(km, fm)


@router.get("/refinement/analyze")
def analyze_for_refinement(
    request: Request,
    days: int = 30,
) -> dict:
    """
    Analyze feedback and suggest knowledge refinements.

    Returns suggestions for:
    - Scoring weight adjustments
    - Business rule modifications
    - General improvements
    """
    refiner = _get_refiner(request)
    report = refiner.analyze_and_suggest(days=days)
    return report.to_dict()


@router.get("/refinement/priorities")
def get_improvement_priorities(request: Request) -> List[dict]:
    """
    Get prioritized list of improvement areas.

    Returns areas sorted by priority based on negative feedback patterns.
    """
    refiner = _get_refiner(request)
    return refiner.get_improvement_priorities()


@router.get("/refinement/report")
def get_refinement_report(request: Request) -> dict:
    """
    Get a human-readable refinement summary report.

    Returns a formatted text report summarizing all suggestions.
    """
    refiner = _get_refiner(request)
    return {"report": refiner.generate_summary_report()}


class ApplyAdjustmentsRequest(BaseModel):
    """Request to apply weight adjustments."""

    adjustments: List[dict]
    min_confidence: float = 0.7


@router.post("/refinement/apply")
def apply_refinement_adjustments(
    request: Request,
    body: ApplyAdjustmentsRequest,
) -> dict:
    """
    Apply suggested weight adjustments.

    Only applies adjustments above the minimum confidence threshold.
    """
    refiner = _get_refiner(request)

    # Convert dict to WeightAdjustment objects
    adjustments = [
        WeightAdjustment(
            category=adj["category"],
            factor_name=adj["factor_name"],
            current_weight=adj["current_weight"],
            suggested_weight=adj["suggested_weight"],
            confidence=adj["confidence"],
            reasoning=adj.get("reasoning", ""),
        )
        for adj in body.adjustments
    ]

    results = refiner.apply_weight_adjustments(
        adjustments=adjustments,
        min_confidence=body.min_confidence,
    )

    return {
        "applied": sum(1 for v in results.values() if v),
        "skipped": sum(1 for v in results.values() if not v),
        "details": results,
    }
