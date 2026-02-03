"""Tests for the Open WebUI Intelligence tool."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import MagicMock, patch


def load_tool_module():
    """Load the intelligence tool module from body/functions."""
    tool_path = Path("body/functions/intelligence.py")
    spec = importlib.util.spec_from_file_location("intelligence_tool", tool_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestIntelligenceTool:
    """Tests for the Intelligence tool class."""

    def test_import_tool(self):
        """Test that the tool module can be imported."""
        module = load_tool_module()
        assert hasattr(module, "Tools")
        assert module.Tools is not None

    def test_tool_initialization(self):
        """Test that Tools class initializes correctly."""
        module = load_tool_module()
        tool = module.Tools()
        assert tool.intelligence_url == "http://host.docker.internal:8081"

    def test_tool_initialization_with_env(self):
        """Test Tools initializes with custom URL from environment."""
        with patch.dict(os.environ, {"INTELLIGENCE_URL": "http://custom:9999"}):
            module = load_tool_module()
            tool = module.Tools()
            assert tool.intelligence_url == "http://custom:9999"

    def test_tool_has_required_methods(self):
        """Test that Tools class has all required methods."""
        module = load_tool_module()
        tool = module.Tools()

        # Core query tools
        assert hasattr(tool, "ask_data")
        assert hasattr(tool, "upload_csv")
        assert hasattr(tool, "list_tables")
        assert hasattr(tool, "score_records")

        # Knowledge tools
        assert hasattr(tool, "get_scoring_factors")
        assert hasattr(tool, "get_business_rules")
        assert hasattr(tool, "get_metrics")

        # Insight tools
        assert hasattr(tool, "get_insights")
        assert hasattr(tool, "get_alerts")

        # Feedback tools
        assert hasattr(tool, "submit_feedback")
        assert hasattr(tool, "get_feedback_summary")
        assert hasattr(tool, "get_improvement_suggestions")

    @patch("requests.post")
    def test_ask_data_success(self, mock_post):
        """Test ask_data method with successful response."""
        module = load_tool_module()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "There were 50 sales last month.",
            "classification": "sql",
            "confidence": 0.95,
            "sql_used": "SELECT COUNT(*) FROM sales",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        tool = module.Tools()
        result = tool.ask_data("How many sales last month?")

        assert "50 sales" in result
        assert "sql" in result.lower()
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_ask_data_connection_error(self, mock_post):
        """Test ask_data handles connection errors gracefully."""
        import requests

        module = load_tool_module()
        mock_post.side_effect = requests.exceptions.ConnectionError()

        tool = module.Tools()
        result = tool.ask_data("Test question")

        assert "Unable to connect" in result

    @patch("requests.get")
    def test_get_insights_success(self, mock_get):
        """Test get_insights method with successful response."""
        module = load_tool_module()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "summary": "Found 3 insights",
            "insights": [
                {
                    "title": "Aged Inventory",
                    "description": "10 vehicles over 90 days",
                    "priority": "high",
                    "recommendations": ["Review pricing"],
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        tool = module.Tools()
        result = tool.get_insights()

        assert "Aged Inventory" in result
        assert "HIGH" in result

    @patch("requests.get")
    def test_get_alerts_no_alerts(self, mock_get):
        """Test get_alerts when no high-priority items exist."""
        module = load_tool_module()

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        tool = module.Tools()
        result = tool.get_alerts()

        assert "No high-priority alerts" in result
        assert "healthy" in result.lower()

    @patch("requests.post")
    def test_submit_feedback(self, mock_post):
        """Test submit_feedback method."""
        module = load_tool_module()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        tool = module.Tools()
        result = tool.submit_feedback("query about sales", 2, "Very helpful!")

        assert "Feedback Recorded" in result
        assert "Excellent" in result
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_submit_feedback_clamps_rating(self, mock_post):
        """Test that submit_feedback clamps rating to valid range."""
        module = load_tool_module()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        tool = module.Tools()

        # Rating of 10 should be clamped to 2
        tool.submit_feedback("test", 10)
        call_args = mock_post.call_args
        assert call_args[1]["json"]["rating"] == 2

        # Rating of -10 should be clamped to -2
        tool.submit_feedback("test", -10)
        call_args = mock_post.call_args
        assert call_args[1]["json"]["rating"] == -2
