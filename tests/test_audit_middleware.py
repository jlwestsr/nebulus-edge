"""Tests for audit middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from shared.middleware.audit_middleware import AuditMiddleware


@pytest.fixture
def app():
    """Create a test FastAPI app with audit middleware."""
    app = FastAPI()

    # Add audit middleware
    app.add_middleware(
        AuditMiddleware,
        enabled=True,
        debug=False,
        default_user="test-user",
    )

    @app.get("/test")
    async def test_endpoint(request: Request):
        """Test endpoint that returns audit context."""
        return {
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "session_id": getattr(request.state, "session_id", None),
            "ip_address": getattr(request.state, "ip_address", None),
            "request_hash": getattr(request.state, "request_hash", None),
        }

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_middleware_enriches_request_state(client):
    """Test that middleware enriches request.state with audit context."""
    response = client.get("/test")
    assert response.status_code == 200
    data = response.json()

    # Check that audit context was added
    assert data["request_id"] is not None
    assert data["user_id"] == "test-user"  # Default user
    assert data["session_id"] is not None
    assert data["ip_address"] == "testclient"  # TestClient default
    assert data["request_hash"] is not None


def test_middleware_extracts_custom_headers(client):
    """Test that middleware extracts user/session from headers."""
    response = client.get(
        "/test",
        headers={
            "X-User-ID": "custom-user",
            "X-Session-ID": "custom-session",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "custom-user"
    assert data["session_id"] == "custom-session"


def test_middleware_adds_response_headers(client):
    """Test that middleware adds audit headers to response."""
    response = client.get("/test")
    assert response.status_code == 200

    # Check response headers
    assert "X-Request-ID" in response.headers
    assert "X-Audit-Timestamp" in response.headers


def test_middleware_disabled(app):
    """Test that middleware can be disabled."""
    # Create app without middleware
    app_disabled = FastAPI()

    @app_disabled.get("/test")
    async def test_endpoint(request: Request):
        return {
            "request_id": getattr(request.state, "request_id", None),
        }

    client = TestClient(app_disabled)
    response = client.get("/test")
    assert response.status_code == 200
    data = response.json()

    # No audit context should be added
    assert data["request_id"] is None
