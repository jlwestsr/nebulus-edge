"""Tests for the Edge platform adapter."""

from pathlib import Path

from nebulus_core.platform.base import PlatformAdapter

from nebulus_edge.adapter import EdgeAdapter


class TestEdgeAdapter:
    """Tests for EdgeAdapter class."""

    def test_implements_protocol(self):
        """Test that EdgeAdapter satisfies the PlatformAdapter protocol."""
        adapter = EdgeAdapter()
        assert isinstance(adapter, PlatformAdapter)

    def test_platform_name(self):
        """Test platform name is 'edge'."""
        adapter = EdgeAdapter()
        assert adapter.platform_name == "edge"

    def test_llm_base_url(self):
        """Test LLM base URL returns a valid HTTP URL."""
        adapter = EdgeAdapter()
        assert isinstance(adapter.llm_base_url, str)
        assert "http" in adapter.llm_base_url

    def test_chroma_settings_embedded(self):
        """Test ChromaDB settings use embedded mode."""
        adapter = EdgeAdapter()
        settings = adapter.chroma_settings
        assert settings["mode"] == "embedded"
        assert "path" in settings

    def test_default_model(self):
        """Test default model is a non-empty string."""
        adapter = EdgeAdapter()
        assert isinstance(adapter.default_model, str)

    def test_data_dir(self):
        """Test data_dir returns a Path."""
        adapter = EdgeAdapter()
        assert isinstance(adapter.data_dir, Path)

    def test_mcp_settings(self):
        """Test mcp_settings returns a dict with server_name."""
        adapter = EdgeAdapter()
        settings = adapter.mcp_settings
        assert isinstance(settings, dict)
        assert "server_name" in settings

    def test_services(self):
        """Test services returns a list of ServiceInfo."""
        adapter = EdgeAdapter()
        services = adapter.services
        assert len(services) == 2
        names = {s.name for s in services}
        assert "brain" in names
        assert "intelligence" in names
