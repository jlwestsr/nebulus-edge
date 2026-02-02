"""Base template class for vertical configurations."""

from pathlib import Path
from typing import Any, Optional

import yaml


class VerticalTemplate:
    """Base class for loading and accessing vertical template configurations."""

    def __init__(self, template_name: str):
        """
        Load a vertical template by name.

        Args:
            template_name: Name of the template (e.g., 'dealership')
        """
        self.name = template_name
        self.config = self._load_config(template_name)

    def _load_config(self, template_name: str) -> dict:
        """Load the config.yaml for a template."""
        template_dir = Path(__file__).parent / template_name
        config_path = template_dir / "config.yaml"

        if not config_path.exists():
            raise ValueError(f"Template '{template_name}' not found at {config_path}")

        with open(config_path) as f:
            return yaml.safe_load(f)

    @property
    def display_name(self) -> str:
        """Human-readable template name."""
        return self.config.get("display_name", self.name.title())

    @property
    def description(self) -> str:
        """Template description."""
        return self.config.get("description", "")

    def get_primary_key_hints(self) -> list[str]:
        """Return column names that might be primary keys."""
        return self.config.get("primary_keys", [])

    def get_data_sources(self) -> dict:
        """Return expected data source definitions."""
        return self.config.get("data_sources", {})

    def get_scoring_factors(self) -> dict:
        """Return scoring configuration for outcome quality."""
        return self.config.get("scoring", {})

    def get_business_rules(self) -> list[dict]:
        """Return business rules and constraints."""
        return self.config.get("rules", [])

    def get_metrics(self) -> dict:
        """Return metric definitions with targets and thresholds."""
        return self.config.get("metrics", {})

    def get_canned_queries(self) -> list[dict]:
        """Return pre-built queries for common questions."""
        return self.config.get("canned_queries", [])

    def get_system_prompt(self) -> str:
        """Return customized system prompt for this vertical."""
        prompts = self.config.get("prompts", {})
        return prompts.get("system", "")

    def get_strategic_prompt(self) -> str:
        """Return prompt for strategic analysis questions."""
        prompts = self.config.get("prompts", {})
        return prompts.get("strategic_analysis", "")

    def find_canned_query(self, name: str) -> Optional[dict]:
        """Find a canned query by name."""
        for query in self.get_canned_queries():
            if query.get("name") == name:
                return query
        return None

    def validate_data_source(
        self,
        source_name: str,
        columns: list[str],
    ) -> dict[str, Any]:
        """
        Validate uploaded data against expected schema.

        Args:
            source_name: Name of the data source (e.g., 'inventory')
            columns: List of column names in the uploaded data

        Returns:
            Dict with validation results:
            - valid: bool
            - missing_required: list of missing required columns
            - matched_optional: list of matched optional columns
            - unknown_columns: list of columns not in schema
        """
        sources = self.get_data_sources()

        if source_name not in sources:
            return {
                "valid": True,  # Unknown source type, allow anything
                "missing_required": [],
                "matched_optional": [],
                "unknown_columns": columns,
                "warning": f"Unknown data source type: {source_name}",
            }

        source_def = sources[source_name]
        required = set(source_def.get("required_columns", []))
        optional = set(source_def.get("optional_columns", []))
        all_expected = required | optional

        columns_lower = {c.lower(): c for c in columns}

        # Check required columns (case-insensitive)
        missing_required = []
        for req in required:
            if req.lower() not in columns_lower:
                missing_required.append(req)

        # Check optional columns
        matched_optional = []
        for opt in optional:
            if opt.lower() in columns_lower:
                matched_optional.append(opt)

        # Find unknown columns
        unknown = []
        for col in columns:
            if col.lower() not in {c.lower() for c in all_expected}:
                unknown.append(col)

        return {
            "valid": len(missing_required) == 0,
            "missing_required": missing_required,
            "matched_optional": matched_optional,
            "unknown_columns": unknown,
        }


def list_templates() -> list[str]:
    """List all available templates."""
    templates_dir = Path(__file__).parent
    templates = []

    for item in templates_dir.iterdir():
        if item.is_dir() and (item / "config.yaml").exists():
            templates.append(item.name)

    return templates


def load_template(name: str) -> VerticalTemplate:
    """Load a template by name."""
    return VerticalTemplate(name)
