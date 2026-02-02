"""Domain knowledge management for business rules and scoring."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ScoringFactor:
    """A factor that contributes to outcome quality scoring."""

    name: str
    description: str
    weight: int
    calculation: str  # SQL-like expression or description


@dataclass
class BusinessRule:
    """A business rule or constraint."""

    name: str
    description: str
    condition: str  # SQL-like condition
    severity: str = "warning"  # warning, error, info


@dataclass
class Metric:
    """A key performance metric with targets."""

    name: str
    description: str
    target: float
    warning: float
    critical: float
    lower_is_better: bool = True


@dataclass
class DomainKnowledge:
    """Container for all domain knowledge."""

    scoring_factors: Dict[str, List[ScoringFactor]] = field(default_factory=dict)
    rules: List[BusinessRule] = field(default_factory=list)
    metrics: Dict[str, Metric] = field(default_factory=dict)
    custom_knowledge: Dict[str, Any] = field(default_factory=dict)


class KnowledgeManager:
    """Manage domain knowledge for a business."""

    def __init__(self, knowledge_path: Path, template_config: Optional[dict] = None):
        """
        Initialize the knowledge manager.

        Args:
            knowledge_path: Path to store custom knowledge JSON
            template_config: Optional template config to load defaults from
        """
        self.knowledge_path = knowledge_path
        self.knowledge = DomainKnowledge()

        # Load defaults from template if provided
        if template_config:
            self._load_from_template(template_config)

        # Load any custom overrides
        self._load_custom()

    def _load_from_template(self, config: dict) -> None:
        """Load default knowledge from template config."""
        # Load scoring factors
        scoring_config = config.get("scoring", {})
        for category, factors in scoring_config.items():
            self.knowledge.scoring_factors[category] = []
            for name, factor_data in factors.items():
                self.knowledge.scoring_factors[category].append(
                    ScoringFactor(
                        name=name,
                        description=factor_data.get("description", ""),
                        weight=factor_data.get("weight", 0),
                        calculation=factor_data.get("calculation", ""),
                    )
                )

        # Load business rules
        rules_config = config.get("rules", [])
        for rule_data in rules_config:
            self.knowledge.rules.append(
                BusinessRule(
                    name=rule_data.get("name", ""),
                    description=rule_data.get("description", ""),
                    condition=rule_data.get("condition", ""),
                    severity=rule_data.get("severity", "warning"),
                )
            )

        # Load metrics
        metrics_config = config.get("metrics", {})
        for name, metric_data in metrics_config.items():
            self.knowledge.metrics[name] = Metric(
                name=name,
                description=metric_data.get("description", ""),
                target=metric_data.get("target", 0),
                warning=metric_data.get("warning", 0),
                critical=metric_data.get("critical", 0),
                lower_is_better=metric_data.get("lower_is_better", True),
            )

    def _load_custom(self) -> None:
        """Load custom knowledge overrides from JSON file."""
        if not self.knowledge_path.exists():
            return

        try:
            with open(self.knowledge_path) as f:
                custom = json.load(f)

            # Merge custom scoring factors
            for category, factors in custom.get("scoring_factors", {}).items():
                if category not in self.knowledge.scoring_factors:
                    self.knowledge.scoring_factors[category] = []
                for factor_data in factors:
                    # Check if factor already exists and update it
                    existing = next(
                        (
                            f
                            for f in self.knowledge.scoring_factors[category]
                            if f.name == factor_data["name"]
                        ),
                        None,
                    )
                    if existing:
                        existing.weight = factor_data.get("weight", existing.weight)
                        existing.description = factor_data.get(
                            "description", existing.description
                        )
                    else:
                        self.knowledge.scoring_factors[category].append(
                            ScoringFactor(
                                name=factor_data["name"],
                                description=factor_data.get("description", ""),
                                weight=factor_data.get("weight", 0),
                                calculation=factor_data.get("calculation", ""),
                            )
                        )

            # Merge custom rules
            for rule_data in custom.get("rules", []):
                existing = next(
                    (r for r in self.knowledge.rules if r.name == rule_data["name"]),
                    None,
                )
                if not existing:
                    self.knowledge.rules.append(
                        BusinessRule(
                            name=rule_data["name"],
                            description=rule_data.get("description", ""),
                            condition=rule_data.get("condition", ""),
                            severity=rule_data.get("severity", "warning"),
                        )
                    )

            # Merge custom knowledge
            self.knowledge.custom_knowledge.update(custom.get("custom", {}))

        except (json.JSONDecodeError, KeyError):
            pass  # Ignore malformed custom knowledge

    def save_custom(self) -> None:
        """Save custom knowledge to JSON file."""
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)

        custom = {
            "scoring_factors": {},
            "rules": [],
            "custom": self.knowledge.custom_knowledge,
        }

        # Only save non-default scoring factors
        for category, factors in self.knowledge.scoring_factors.items():
            custom["scoring_factors"][category] = [
                {
                    "name": f.name,
                    "description": f.description,
                    "weight": f.weight,
                    "calculation": f.calculation,
                }
                for f in factors
            ]

        # Save rules
        custom["rules"] = [
            {
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "severity": r.severity,
            }
            for r in self.knowledge.rules
        ]

        with open(self.knowledge_path, "w") as f:
            json.dump(custom, f, indent=2)

    def get_scoring_factors(
        self, category: str = "perfect_sale"
    ) -> List[ScoringFactor]:
        """Get scoring factors for a category."""
        return self.knowledge.scoring_factors.get(category, [])

    def get_all_scoring_factors(self) -> Dict[str, List[ScoringFactor]]:
        """Get all scoring factors."""
        return self.knowledge.scoring_factors

    def update_scoring_factor(
        self,
        category: str,
        name: str,
        weight: Optional[int] = None,
        description: Optional[str] = None,
    ) -> bool:
        """Update a scoring factor's weight or description."""
        factors = self.knowledge.scoring_factors.get(category, [])
        for factor in factors:
            if factor.name == name:
                if weight is not None:
                    factor.weight = weight
                if description is not None:
                    factor.description = description
                self.save_custom()
                return True
        return False

    def get_business_rules(self) -> List[BusinessRule]:
        """Get all business rules."""
        return self.knowledge.rules

    def add_business_rule(
        self,
        name: str,
        description: str,
        condition: str,
        severity: str = "warning",
    ) -> BusinessRule:
        """Add a new business rule."""
        rule = BusinessRule(
            name=name,
            description=description,
            condition=condition,
            severity=severity,
        )
        self.knowledge.rules.append(rule)
        self.save_custom()
        return rule

    def get_metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        return self.knowledge.metrics

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a specific metric."""
        return self.knowledge.metrics.get(name)

    def add_custom_knowledge(self, key: str, value: Any) -> None:
        """Add custom knowledge."""
        self.knowledge.custom_knowledge[key] = value
        self.save_custom()

    def get_custom_knowledge(self, key: str) -> Optional[Any]:
        """Get custom knowledge by key."""
        return self.knowledge.custom_knowledge.get(key)

    def export_for_prompt(self) -> str:
        """Format knowledge for LLM context injection."""
        lines = ["## Domain Knowledge", ""]

        # Scoring factors
        if self.knowledge.scoring_factors:
            lines.append("### What Makes a Good Outcome")
            for category, factors in self.knowledge.scoring_factors.items():
                lines.append(f"\n**{category.replace('_', ' ').title()}:**")
                for f in sorted(factors, key=lambda x: -x.weight):
                    lines.append(f"- {f.description} (weight: {f.weight})")

        # Business rules
        if self.knowledge.rules:
            lines.append("\n### Business Rules")
            for rule in self.knowledge.rules:
                lines.append(f"- **{rule.name}**: {rule.description}")

        # Metrics
        if self.knowledge.metrics:
            lines.append("\n### Key Metrics")
            for name, metric in self.knowledge.metrics.items():
                direction = "lower" if metric.lower_is_better else "higher"
                lines.append(
                    f"- **{name}**: target {metric.target}, "
                    f"warning at {metric.warning}, critical at {metric.critical} "
                    f"({direction} is better)"
                )

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Export knowledge as a dictionary."""
        return {
            "scoring_factors": {
                category: [
                    {
                        "name": f.name,
                        "description": f.description,
                        "weight": f.weight,
                        "calculation": f.calculation,
                    }
                    for f in factors
                ]
                for category, factors in self.knowledge.scoring_factors.items()
            },
            "rules": [
                {
                    "name": r.name,
                    "description": r.description,
                    "condition": r.condition,
                    "severity": r.severity,
                }
                for r in self.knowledge.rules
            ],
            "metrics": {
                name: {
                    "description": m.description,
                    "target": m.target,
                    "warning": m.warning,
                    "critical": m.critical,
                    "lower_is_better": m.lower_is_better,
                }
                for name, m in self.knowledge.metrics.items()
            },
            "custom": self.knowledge.custom_knowledge,
        }
