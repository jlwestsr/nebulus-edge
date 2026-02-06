"""Tests for audit export functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from nebulus_core.intelligence.core.audit import AuditEvent, AuditEventType, AuditLogger
from shared.audit.export import AuditExporter


@pytest.fixture
def temp_db():
    """Create a temporary audit database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Create logger and add some test events
    logger = AuditLogger(db_path=db_path)

    # Add test events
    for i in range(10):
        event = AuditEvent(
            event_type=AuditEventType.DATA_UPLOAD,
            timestamp=datetime.now(),
            user_id=f"user_{i}",
            session_id=f"session_{i}",
            ip_address="127.0.0.1",
            resource=f"table_{i}",
            action="upload",
            details={"rows": i * 100},
            success=True,
        )
        logger.log(event)

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def exporter(temp_db):
    """Create an AuditExporter instance."""
    return AuditExporter(db_path=temp_db, secret_key="test-secret-key")


def test_export_csv_creates_files(exporter, temp_db):
    """Test that export creates CSV, signature, and metadata files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_export.csv"

        # Export last 30 days
        files = exporter.export_csv(output_path=str(output_path), days=30)

        # Check that all files were created
        assert Path(files["csv"]).exists()
        assert Path(files["signature"]).exists()
        assert Path(files["metadata"]).exists()

        # Check CSV content
        csv_content = Path(files["csv"]).read_text()
        assert "timestamp" in csv_content
        assert "event_type" in csv_content
        assert "user_id" in csv_content

        # Check metadata
        with open(files["metadata"]) as f:
            metadata = json.load(f)
        assert metadata["record_count"] == 10
        assert "csv_hash" in metadata
        assert metadata["signature_algorithm"] == "HMAC-SHA256"


def test_export_csv_with_date_range(exporter):
    """Test export with specific date range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_export.csv"

        # Export last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        files = exporter.export_csv(
            output_path=str(output_path),
            start_date=start_date,
            end_date=end_date,
        )

        assert Path(files["csv"]).exists()


def test_verify_export_valid(exporter):
    """Test verification of valid export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_export.csv"

        # Export and verify
        files = exporter.export_csv(output_path=str(output_path), days=30)
        result = exporter.verify_export(csv_path=files["csv"])

        assert result["hash_valid"] is True
        assert result["signature_valid"] is True
        assert result["tampered"] is False
        assert result["record_count"] == 10


def test_verify_export_tampered(exporter):
    """Test verification detects tampering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_export.csv"

        # Export
        files = exporter.export_csv(output_path=str(output_path), days=30)

        # Tamper with CSV
        csv_file = Path(files["csv"])
        content = csv_file.read_text()
        csv_file.write_text(content + "\nTAMPERED")

        # Verify should detect tampering
        result = exporter.verify_export(csv_path=files["csv"])

        assert result["hash_valid"] is False
        assert result["tampered"] is True


def test_verify_export_missing_files(exporter):
    """Test verification fails if files are missing."""
    with pytest.raises(FileNotFoundError):
        exporter.verify_export(csv_path="nonexistent.csv")


def test_export_empty_database():
    """Test export with empty database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Create empty logger
    AuditLogger(db_path=db_path)
    exporter = AuditExporter(db_path=str(db_path))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_export.csv"

        files = exporter.export_csv(output_path=str(output_path), days=30)

        # Check that empty CSV was created with headers
        csv_content = Path(files["csv"]).read_text()
        assert "timestamp" in csv_content

        # Check metadata shows 0 records
        with open(files["metadata"]) as f:
            metadata = json.load(f)
        assert metadata["record_count"] == 0

    # Cleanup
    Path(db_path).unlink(missing_ok=True)
