"""Tests for the data ingestion module."""

import tempfile
from pathlib import Path

import pytest

from intelligence.core.ingest import DataIngestor, IngestResult


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def sample_csv():
    """Sample CSV content for testing."""
    return """vin,make,model,year,price
ABC123,Honda,Accord,2020,25000
DEF456,Toyota,Camry,2021,28000
GHI789,Ford,F-150,2019,35000
"""


@pytest.fixture
def ingestor(temp_db):
    """Create a DataIngestor instance."""
    return DataIngestor(temp_db, template="dealership")


class TestDataIngestor:
    """Tests for DataIngestor class."""

    def test_ingest_csv_basic(self, ingestor, sample_csv):
        """Test basic CSV ingestion."""
        result = ingestor.ingest_csv(sample_csv, "test_table")

        assert isinstance(result, IngestResult)
        assert result.table_name == "test_table"
        assert result.rows_imported == 3
        assert "vin" in result.columns
        assert "make" in result.columns

    def test_ingest_csv_bytes(self, ingestor, sample_csv):
        """Test CSV ingestion from bytes."""
        result = ingestor.ingest_csv(sample_csv.encode("utf-8"), "test_table")

        assert result.rows_imported == 3

    def test_primary_key_detection_dealership(self, ingestor, sample_csv):
        """Test primary key detection for dealership template."""
        result = ingestor.ingest_csv(sample_csv, "test_table")

        assert result.primary_key == "vin"

    def test_column_name_cleaning(self, ingestor):
        """Test that column names are cleaned properly."""
        csv_content = """First Name,Last-Name,Phone Number
John,Doe,555-1234
"""
        result = ingestor.ingest_csv(csv_content, "test_table")

        assert "first_name" in result.columns
        assert "last_name" in result.columns
        assert "phone_number" in result.columns

    def test_column_type_inference(self, ingestor, sample_csv):
        """Test column type inference."""
        result = ingestor.ingest_csv(sample_csv, "test_table")

        assert result.column_types["year"] == "INTEGER"
        assert result.column_types["price"] == "INTEGER"
        assert result.column_types["make"] == "TEXT"

    def test_list_tables(self, ingestor, sample_csv):
        """Test listing tables."""
        ingestor.ingest_csv(sample_csv, "table1")
        ingestor.ingest_csv(sample_csv, "table2")

        tables = ingestor.list_tables()
        assert "table1" in tables
        assert "table2" in tables

    def test_get_table_schema(self, ingestor, sample_csv):
        """Test getting table schema."""
        ingestor.ingest_csv(sample_csv, "test_table")

        schema = ingestor.get_table_schema("test_table")
        assert schema["table_name"] == "test_table"
        assert schema["row_count"] == 3
        assert "vin" in schema["columns"]

    def test_preview_table(self, ingestor, sample_csv):
        """Test previewing table data."""
        ingestor.ingest_csv(sample_csv, "test_table")

        preview = ingestor.preview_table("test_table", limit=2)
        assert len(preview) == 2
        assert preview[0]["make"] == "Honda"

    def test_delete_table(self, ingestor, sample_csv):
        """Test deleting a table."""
        ingestor.ingest_csv(sample_csv, "test_table")
        assert "test_table" in ingestor.list_tables()

        result = ingestor.delete_table("test_table")
        assert result is True
        assert "test_table" not in ingestor.list_tables()

    def test_delete_nonexistent_table(self, ingestor):
        """Test deleting a table that doesn't exist."""
        result = ingestor.delete_table("nonexistent")
        assert result is False

    def test_ingest_empty_csv_raises(self, ingestor):
        """Test that empty CSV raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse"):
            ingestor.ingest_csv("", "test_table")

    def test_ingest_headers_only_raises(self, ingestor):
        """Test that CSV with only headers raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            ingestor.ingest_csv("col1,col2,col3\n", "test_table")

    def test_duplicate_primary_key_warning(self, ingestor):
        """Test that duplicate primary keys generate a warning."""
        csv_content = """vin,make,model
ABC123,Honda,Accord
ABC123,Toyota,Camry
"""
        result = ingestor.ingest_csv(csv_content, "test_table")

        assert any("duplicates" in w.lower() for w in result.warnings)

    def test_medical_template_primary_key(self, temp_db):
        """Test primary key detection for medical template."""
        ingestor = DataIngestor(temp_db, template="medical")
        csv_content = """patient_id,first_name,last_name
P001,John,Doe
P002,Jane,Smith
"""
        result = ingestor.ingest_csv(csv_content, "patients")
        assert result.primary_key == "patient_id"

    def test_legal_template_primary_key(self, temp_db):
        """Test primary key detection for legal template."""
        ingestor = DataIngestor(temp_db, template="legal")
        csv_content = """case_id,client_name,matter_type
C001,Acme Corp,litigation
C002,Smith LLC,transactional
"""
        result = ingestor.ingest_csv(csv_content, "matters")
        assert result.primary_key == "case_id"
