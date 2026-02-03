"""Tests for the vertical templates module."""

import pytest

from nebulus_core.intelligence.templates import (
    VerticalTemplate,
    list_templates,
    load_template,
)


class TestListTemplates:
    """Tests for list_templates function."""

    def test_list_templates(self):
        """Test that all expected templates are found."""
        templates = list_templates()

        assert "dealership" in templates
        assert "medical" in templates
        assert "legal" in templates

    def test_list_templates_returns_list(self):
        """Test that list_templates returns a list."""
        templates = list_templates()
        assert isinstance(templates, list)


class TestLoadTemplate:
    """Tests for load_template function."""

    def test_load_dealership_template(self):
        """Test loading the dealership template."""
        template = load_template("dealership")

        assert isinstance(template, VerticalTemplate)
        assert template.name == "dealership"

    def test_load_medical_template(self):
        """Test loading the medical template."""
        template = load_template("medical")

        assert template.name == "medical"
        assert template.display_name == "Medical Practice"

    def test_load_legal_template(self):
        """Test loading the legal template."""
        template = load_template("legal")

        assert template.name == "legal"
        assert template.display_name == "Law Firm"

    def test_load_nonexistent_template(self):
        """Test that loading nonexistent template raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            load_template("nonexistent")


class TestVerticalTemplate:
    """Tests for VerticalTemplate class."""

    @pytest.fixture
    def dealership_template(self):
        """Load dealership template."""
        return load_template("dealership")

    @pytest.fixture
    def medical_template(self):
        """Load medical template."""
        return load_template("medical")

    @pytest.fixture
    def legal_template(self):
        """Load legal template."""
        return load_template("legal")

    def test_display_name(self, dealership_template):
        """Test getting display name."""
        assert dealership_template.display_name == "Auto Dealership"

    def test_description(self, dealership_template):
        """Test getting description."""
        assert len(dealership_template.description) > 0

    def test_get_primary_key_hints_dealership(self, dealership_template):
        """Test getting primary key hints for dealership."""
        hints = dealership_template.get_primary_key_hints()

        assert "vin" in hints
        assert "VIN" in hints
        assert "stock_number" in hints

    def test_get_primary_key_hints_medical(self, medical_template):
        """Test getting primary key hints for medical."""
        hints = medical_template.get_primary_key_hints()

        assert "patient_id" in hints
        assert "mrn" in hints

    def test_get_primary_key_hints_legal(self, legal_template):
        """Test getting primary key hints for legal."""
        hints = legal_template.get_primary_key_hints()

        assert "case_id" in hints
        assert "matter_id" in hints

    def test_get_data_sources(self, dealership_template):
        """Test getting data sources."""
        sources = dealership_template.get_data_sources()

        assert "inventory" in sources
        assert "sales" in sources
        assert "required_columns" in sources["inventory"]

    def test_get_scoring_factors(self, dealership_template):
        """Test getting scoring factors."""
        scoring = dealership_template.get_scoring_factors()

        assert "perfect_sale" in scoring
        assert "dealer_financing" in scoring["perfect_sale"]

    def test_get_business_rules(self, dealership_template):
        """Test getting business rules."""
        rules = dealership_template.get_business_rules()

        assert len(rules) > 0
        assert any(r["name"] == "max_mileage" for r in rules)

    def test_get_metrics(self, dealership_template):
        """Test getting metrics."""
        metrics = dealership_template.get_metrics()

        assert "days_on_lot" in metrics
        assert "target" in metrics["days_on_lot"]

    def test_get_canned_queries(self, dealership_template):
        """Test getting canned queries."""
        queries = dealership_template.get_canned_queries()

        assert len(queries) > 0
        assert all("name" in q for q in queries)
        assert all("sql" in q for q in queries)

    def test_find_canned_query(self, dealership_template):
        """Test finding a specific canned query."""
        query = dealership_template.find_canned_query("aged_inventory")

        assert query is not None
        assert "sql" in query

    def test_find_nonexistent_canned_query(self, dealership_template):
        """Test finding a query that doesn't exist."""
        query = dealership_template.find_canned_query("nonexistent")
        assert query is None

    def test_get_system_prompt(self, dealership_template):
        """Test getting system prompt."""
        prompt = dealership_template.get_system_prompt()

        assert len(prompt) > 0
        assert "dealership" in prompt.lower()

    def test_get_strategic_prompt(self, dealership_template):
        """Test getting strategic analysis prompt."""
        prompt = dealership_template.get_strategic_prompt()

        assert len(prompt) > 0
        assert "inventory" in prompt.lower()

    def test_validate_data_source_valid(self, dealership_template):
        """Test validating a valid data source."""
        result = dealership_template.validate_data_source(
            "inventory",
            ["vin", "make", "model", "year", "days_on_lot"],
        )

        assert result["valid"] is True
        assert len(result["missing_required"]) == 0

    def test_validate_data_source_missing_required(self, dealership_template):
        """Test validating with missing required columns."""
        result = dealership_template.validate_data_source(
            "inventory",
            ["vin", "make"],  # Missing model and year
        )

        assert result["valid"] is False
        assert "model" in result["missing_required"]
        assert "year" in result["missing_required"]

    def test_validate_data_source_unknown_source(self, dealership_template):
        """Test validating an unknown data source."""
        result = dealership_template.validate_data_source(
            "unknown_source",
            ["col1", "col2"],
        )

        # Unknown sources are allowed
        assert result["valid"] is True
        assert "warning" in result

    def test_medical_template_scoring(self, medical_template):
        """Test medical template has scoring factors."""
        scoring = medical_template.get_scoring_factors()

        assert "ideal_visit" in scoring
        assert "patient_engagement" in scoring

    def test_legal_template_scoring(self, legal_template):
        """Test legal template has scoring factors."""
        scoring = legal_template.get_scoring_factors()

        assert "matter_health" in scoring
        assert "timekeeper_productivity" in scoring

    def test_medical_template_hipaa_warning(self, medical_template):
        """Test medical template has HIPAA considerations in prompt."""
        prompt = medical_template.get_system_prompt()

        assert "hipaa" in prompt.lower() or "privacy" in prompt.lower()

    def test_legal_template_privilege_warning(self, legal_template):
        """Test legal template has privilege considerations in prompt."""
        prompt = legal_template.get_system_prompt()

        assert "privilege" in prompt.lower() or "confidential" in prompt.lower()
