"""Data management API endpoints.

Handles CSV upload, table management, and schema operations.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from intelligence.core.ingest import DataIngestor
from intelligence.core.vector_engine import VectorEngine

router = APIRouter(prefix="/data", tags=["data"])


class TableInfo(BaseModel):
    """Information about a data table."""

    name: str
    row_count: int
    columns: list[str]
    primary_key: Optional[str] = None


class PIISummary(BaseModel):
    """Summary of PII detection results."""

    detected: bool = False
    columns_with_pii: list[str] = []
    records_affected: int = 0
    types_found: list[str] = []


class IngestResult(BaseModel):
    """Result of CSV ingestion."""

    table_name: str
    rows_imported: int
    columns: list[str]
    column_types: dict[str, str]
    primary_key: Optional[str] = None
    warnings: list[str] = []
    records_embedded: int = 0
    pii: Optional[PIISummary] = None


class SchemaInfo(BaseModel):
    """Detailed schema information for a table."""

    table_name: str
    columns: list[str]
    types: dict[str, str]
    row_count: int


def _get_ingestor(request: Request) -> DataIngestor:
    """Get or create a DataIngestor instance with vector support."""
    db_path = request.app.state.db_path / "main.db"
    template = request.app.state.template
    vector_path = request.app.state.vector_path

    # Create vector engine for semantic search
    vector_engine = VectorEngine(vector_path)

    return DataIngestor(db_path, template, vector_engine)


@router.post("/upload", response_model=IngestResult)
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    table_name: Optional[str] = None,
) -> IngestResult:
    """
    Upload a CSV file for analysis.

    - Auto-detects schema and column types
    - Detects primary key based on template hints
    - Creates SQLite table for querying
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Use filename as table name if not provided
    if not table_name:
        table_name = Path(file.filename).stem.lower().replace(" ", "_")
        # Clean table name
        table_name = "".join(c if c.isalnum() else "_" for c in table_name)
        table_name = table_name.strip("_")

    # Read file content
    content = await file.read()

    # Ingest the CSV
    ingestor = _get_ingestor(request)

    try:
        result = ingestor.ingest_csv(content, table_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    # Build PII summary if detection was performed
    pii_summary = None
    if result.pii_report:
        pii_summary = PIISummary(
            detected=result.pii_detected,
            columns_with_pii=result.pii_columns,
            records_affected=result.pii_report.records_with_pii,
            types_found=[t.value for t in result.pii_report.pii_by_type.keys()],
        )

    return IngestResult(
        table_name=result.table_name,
        rows_imported=result.rows_imported,
        columns=result.columns,
        column_types=result.column_types,
        primary_key=result.primary_key,
        warnings=result.warnings,
        records_embedded=result.records_embedded,
        pii=pii_summary,
    )


@router.get("/tables", response_model=list[TableInfo])
async def list_tables(request: Request) -> list[TableInfo]:
    """List all uploaded data tables with schema info."""
    ingestor = _get_ingestor(request)
    tables = []

    for table_name in ingestor.list_tables():
        try:
            schema = ingestor.get_table_schema(table_name)
            tables.append(
                TableInfo(
                    name=table_name,
                    row_count=schema["row_count"],
                    columns=schema["columns"],
                    primary_key=None,  # TODO: Store primary key info
                )
            )
        except Exception:
            # Skip tables that can't be read
            continue

    return tables


@router.get("/tables/{table_name}/schema", response_model=SchemaInfo)
async def get_schema(request: Request, table_name: str) -> SchemaInfo:
    """Get detailed schema for a table."""
    ingestor = _get_ingestor(request)

    if table_name not in ingestor.list_tables():
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    schema = ingestor.get_table_schema(table_name)

    return SchemaInfo(
        table_name=schema["table_name"],
        columns=schema["columns"],
        types=schema["types"],
        row_count=schema["row_count"],
    )


@router.get("/tables/{table_name}/preview")
async def preview_data(
    request: Request,
    table_name: str,
    limit: int = 10,
) -> list[dict]:
    """Preview rows from a table."""
    ingestor = _get_ingestor(request)

    if table_name not in ingestor.list_tables():
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    return ingestor.preview_table(table_name, limit)


@router.delete("/tables/{table_name}")
async def delete_table(request: Request, table_name: str) -> dict:
    """Delete a table and its associated data."""
    ingestor = _get_ingestor(request)

    if not ingestor.delete_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    return {"status": "deleted", "table_name": table_name}


@router.get("/relationships")
async def get_relationships(request: Request) -> list[dict]:
    """Get detected relationships between tables."""
    # TODO: Implement relationship detection based on shared column names
    # For now, return empty list
    return []
