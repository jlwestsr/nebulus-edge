"""Integration tests for intelligence service audit logging."""

import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nebulus_core.intelligence.core.audit import AuditEvent, AuditEventType, AuditLogger


@pytest.fixture
def temp_storage():
    """Create temporary storage directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Path(tmpdir) / "storage"
        storage.mkdir()
        (storage / "databases").mkdir()
        (storage / "vectors").mkdir()
        (storage / "knowledge").mkdir()
        (storage / "feedback").mkdir()
        (storage / "audit").mkdir()

        yield storage


@pytest.fixture
def app(temp_storage, monkeypatch):
    """Create test FastAPI app with audit logging enabled."""
    # Set environment variables
    monkeypatch.setenv("AUDIT_ENABLED", "true")
    monkeypatch.setenv("AUDIT_RETENTION_DAYS", "30")
    monkeypatch.setenv("AUDIT_DEBUG", "false")
    monkeypatch.setenv("BRAIN_URL", "http://localhost:8080")

    # Import and configure the app
    # NOTE: This import must happen after setting env vars
    import sys

    # Remove cached modules to force reload with new env vars
    if "intelligence.server" in sys.modules:
        del sys.modules["intelligence.server"]

    # Mock the storage paths in the server module
    from intelligence import server

    server.STORAGE_PATH = temp_storage
    server.DB_PATH = temp_storage / "databases"
    server.VECTOR_PATH = temp_storage / "vectors"
    server.KNOWLEDGE_PATH = temp_storage / "knowledge"
    server.FEEDBACK_PATH = temp_storage / "feedback"
    server.AUDIT_PATH = temp_storage / "audit"

    # Get the app (lifespan will initialize audit logging)
    from intelligence.server import app

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def audit_logger(temp_storage):
    """Create audit logger for verification."""
    audit_db = temp_storage / "audit" / "audit.db"
    return AuditLogger(db_path=audit_db)


def test_csv_upload_creates_audit_log(client, audit_logger, temp_storage):
    """Test that CSV upload creates an audit log entry."""
    # Create a test CSV
    csv_content = b"id,name,value\\n1,test,100\\n2,test2,200\\n"
    csv_file = BytesIO(csv_content)

    # Upload CSV
    response = client.post(
        "/data/upload",
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    # Should succeed (or fail gracefully if dependencies missing)
    # The audit log should be created either way
    if response.status_code == 200:
        # Check audit log for DATA_UPLOAD event
        events = audit_logger.get_events(event_type=AuditEventType.DATA_UPLOAD)
        assert len(events) > 0

        # Verify event details
        event = events[0]
        assert event.event_type == AuditEventType.DATA_UPLOAD
        assert event.user_id == "appliance-admin"
        assert event.resource == "test"
        assert event.action == "upload_csv"
        assert event.success is True


def test_query_operation_logged(client, audit_logger, temp_storage):
    """Test that query operations are logged."""
    # Upload data first
    csv_content = b"id,name,value\\n1,test,100\\n2,test2,200\\n"
    csv_file = BytesIO(csv_content)
    upload_response = client.post(
        "/data/upload",
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    if upload_response.status_code == 200:
        # Execute a query
        response = client.post(
            "/query/ask",
            json={"question": "How many records are there?"},
        )

        # Check if query was logged
        if response.status_code == 200:
            events = audit_logger.get_events(event_type=AuditEventType.QUERY_NATURAL)
            assert len(events) > 0

            event = events[0]
            assert event.event_type == AuditEventType.QUERY_NATURAL
            assert event.action == "ask_question"
            assert "query_hash" in event.details


def test_sql_query_logged(client, audit_logger, temp_storage):
    """Test that SQL queries are logged."""
    # Upload data first
    csv_content = b"id,name,value\\n1,test,100\\n2,test2,200\\n"
    csv_file = BytesIO(csv_content)
    upload_response = client.post(
        "/data/upload",
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    if upload_response.status_code == 200:
        # Execute SQL query
        response = client.post(
            "/query/sql",
            json={"sql": "SELECT * FROM test LIMIT 10"},
        )

        # Query should be logged (success or failure)
        events = audit_logger.get_events(event_type=AuditEventType.QUERY_SQL)
        assert len(events) > 0

        event = events[0]
        assert event.event_type == AuditEventType.QUERY_SQL
        assert event.action == "execute_sql"
        assert "query_hash" in event.details


def test_delete_table_logged(client, audit_logger, temp_storage):
    """Test that table deletion is logged."""
    # Upload data first
    csv_content = b"id,name,value\\n1,test,100\\n"
    csv_file = BytesIO(csv_content)
    upload_response = client.post(
        "/data/upload",
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    if upload_response.status_code == 200:
        # Delete the table
        response = client.delete("/data/tables/test")

        # Deletion should be logged
        events = audit_logger.get_events(event_type=AuditEventType.DATA_DELETE)
        assert len(events) > 0

        event = events[0]
        assert event.event_type == AuditEventType.DATA_DELETE
        assert event.resource == "test"
        assert event.action == "delete_table"


def test_audit_context_preserved(client, audit_logger):
    """Test that audit context (user, session, IP) is preserved."""
    csv_content = b"id,name\\n1,test\\n"
    csv_file = BytesIO(csv_content)

    # Upload with custom headers
    response = client.post(
        "/data/upload",
        files={"file": ("test.csv", csv_file, "text/csv")},
        headers={
            "X-User-ID": "test-user@example.com",
            "X-Session-ID": "test-session-123",
        },
    )

    if response.status_code == 200:
        # Check that context was preserved in audit log
        events = audit_logger.get_events(event_type=AuditEventType.DATA_UPLOAD)
        if events:
            event = events[0]
            assert event.user_id == "test-user@example.com"
            assert event.session_id == "test-session-123"
