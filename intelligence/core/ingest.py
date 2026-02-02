"""CSV ingestion with schema inference and primary key detection."""

import sqlite3
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Optional, Union

import pandas as pd


@dataclass
class IngestResult:
    """Result of CSV ingestion."""

    table_name: str
    rows_imported: int
    columns: list[str]
    column_types: dict[str, str]
    primary_key: Optional[str] = None
    warnings: list[str] = field(default_factory=list)


class DataIngestor:
    """CSV ingestion with schema inference and primary key detection."""

    # Primary key hints by template
    PRIMARY_KEY_HINTS = {
        "dealership": [
            "vin",
            "VIN",
            "stock_number",
            "stocknumber",
            "stock_no",
            "StockNumber",
            "Stock_Number",
        ],
        "medical": [
            "patient_id",
            "patientid",
            "PatientID",
            "mrn",
            "MRN",
            "Patient_ID",
        ],
        "legal": [
            "case_id",
            "caseid",
            "CaseID",
            "matter_id",
            "MatterID",
            "Case_ID",
        ],
        "generic": ["id", "ID", "Id", "key", "KEY"],
    }

    def __init__(self, db_path: Path, template: str = "generic"):
        """
        Initialize the data ingestor.

        Args:
            db_path: Path to the SQLite database file
            template: Vertical template name for primary key hints
        """
        self.db_path = db_path
        self.template = template
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Ensure the database file and parent directories exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Create database if it doesn't exist
        conn = sqlite3.connect(self.db_path)
        conn.close()

    def ingest_csv(
        self,
        csv_content: Union[bytes, str],
        table_name: str,
        primary_key_hint: Optional[str] = None,
    ) -> IngestResult:
        """
        Ingest CSV content into SQLite database.

        Args:
            csv_content: CSV file content as bytes or string
            table_name: Name for the database table
            primary_key_hint: Optional column name to use as primary key

        Returns:
            IngestResult with import statistics and detected schema
        """
        warnings: list[str] = []

        # Parse CSV
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode("utf-8")

        try:
            df = pd.read_csv(StringIO(csv_content))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")

        if df.empty:
            raise ValueError("CSV file is empty")

        # Clean column names (remove spaces, lowercase)
        original_columns = list(df.columns)
        df.columns = [self._clean_column_name(c) for c in df.columns]
        cleaned_columns = list(df.columns)

        # Track column renames for warnings
        for orig, clean in zip(original_columns, cleaned_columns):
            if orig != clean:
                warnings.append(f"Column '{orig}' renamed to '{clean}'")

        # Detect primary key
        primary_key = self._detect_primary_key(df, primary_key_hint)
        if primary_key:
            # Verify uniqueness
            if df[primary_key].duplicated().any():
                warnings.append(
                    f"Primary key '{primary_key}' has duplicates - "
                    "may cause issues with joins"
                )

        # Infer column types
        column_types = self._infer_types(df)

        # Import to SQLite
        conn = sqlite3.connect(self.db_path)
        try:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            rows_imported = len(df)
        finally:
            conn.close()

        return IngestResult(
            table_name=table_name,
            rows_imported=rows_imported,
            columns=cleaned_columns,
            column_types=column_types,
            primary_key=primary_key,
            warnings=warnings,
        )

    def _clean_column_name(self, name: str) -> str:
        """Clean a column name for SQL compatibility."""
        # Replace spaces and special chars with underscore
        clean = "".join(c if c.isalnum() else "_" for c in str(name))
        # Remove leading/trailing underscores
        clean = clean.strip("_")
        # Lowercase
        clean = clean.lower()
        # Ensure not empty
        return clean or "column"

    def _detect_primary_key(
        self,
        df: pd.DataFrame,
        hint: Optional[str] = None,
    ) -> Optional[str]:
        """
        Detect the primary key column.

        Args:
            df: DataFrame to analyze
            hint: Optional column name hint from user

        Returns:
            Column name if primary key detected, None otherwise
        """
        columns = list(df.columns)

        # If user provided hint, check if it exists
        if hint:
            hint_clean = self._clean_column_name(hint)
            if hint_clean in columns:
                return hint_clean
            # Try original case
            if hint in columns:
                return hint

        # Get hints for current template
        hints = self.PRIMARY_KEY_HINTS.get(
            self.template,
            self.PRIMARY_KEY_HINTS["generic"],
        )

        # Check each hint
        for pk_hint in hints:
            clean_hint = self._clean_column_name(pk_hint)
            if clean_hint in columns:
                return clean_hint

        return None

    def _infer_types(self, df: pd.DataFrame) -> dict[str, str]:
        """
        Infer SQL-friendly type names for each column.

        Returns:
            Dict mapping column name to type string
        """
        type_map = {}

        for col in df.columns:
            dtype = df[col].dtype

            if pd.api.types.is_integer_dtype(dtype):
                type_map[col] = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                type_map[col] = "REAL"
            elif pd.api.types.is_bool_dtype(dtype):
                type_map[col] = "BOOLEAN"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                type_map[col] = "DATETIME"
            else:
                type_map[col] = "TEXT"

        return type_map

    def list_tables(self) -> list[str]:
        """List all tables in the database."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_table_schema(self, table_name: str) -> dict:
        """
        Get schema information for a table.

        Returns:
            Dict with columns, types, and row count
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Get column info
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = []
            types = {}
            for row in cursor.fetchall():
                col_name = row[1]
                col_type = row[2]
                columns.append(col_name)
                types[col_name] = col_type

            # Get row count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            return {
                "table_name": table_name,
                "columns": columns,
                "types": types,
                "row_count": row_count,
            }
        finally:
            conn.close()

    def preview_table(self, table_name: str, limit: int = 10) -> list[dict]:
        """
        Get a preview of rows from a table.

        Returns:
            List of row dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                f"SELECT * FROM {table_name} LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_table(self, table_name: str) -> bool:
        """
        Delete a table from the database.

        Returns:
            True if deleted, False if table didn't exist
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master " "WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                return False

            conn.execute(f"DROP TABLE {table_name}")
            conn.commit()
            return True
        finally:
            conn.close()
