"""SQLite wrapper with natural language to SQL conversion."""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

from intelligence.core.security import quote_identifier, validate_sql_query


@dataclass
class QueryResult:
    """Result of a SQL query."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    sql: str


class UnsafeQueryError(Exception):
    """Raised when a query is not safe to execute."""

    pass


class SQLEngine:
    """Execute SQL queries with natural language interface."""

    def __init__(self, db_path: Path, brain_url: str):
        """
        Initialize the SQL engine.

        Args:
            db_path: Path to the SQLite database file
            brain_url: URL of the Brain API for text-to-SQL conversion
        """
        self.db_path = db_path
        self.brain_url = brain_url

    def get_schema(self) -> dict:
        """
        Get the database schema.

        Returns:
            Dict with tables, columns, types, and relationships
        """
        conn = sqlite3.connect(self.db_path)
        try:
            schema = {"tables": {}}

            # Get all tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                # Quote table name for safe SQL
                quoted_table = quote_identifier(table)

                # Get column info
                cursor = conn.execute(f"PRAGMA table_info({quoted_table})")
                columns = []
                for row in cursor.fetchall():
                    columns.append(
                        {
                            "name": row[1],
                            "type": row[2],
                            "nullable": not row[3],
                            "primary_key": bool(row[5]),
                        }
                    )

                # Get sample values for context
                cursor = conn.execute(f"SELECT * FROM {quoted_table} LIMIT 3")
                sample_rows = cursor.fetchall()

                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM {quoted_table}")
                row_count = cursor.fetchone()[0]

                schema["tables"][table] = {
                    "columns": columns,
                    "row_count": row_count,
                    "sample_rows": sample_rows,
                }

            return schema
        finally:
            conn.close()

    def get_schema_for_prompt(self) -> str:
        """
        Format schema for LLM prompt.

        Returns:
            Human-readable schema string
        """
        schema = self.get_schema()
        lines = ["Database Schema:", ""]

        for table_name, table_info in schema["tables"].items():
            lines.append(f"Table: {table_name} ({table_info['row_count']} rows)")
            for col in table_info["columns"]:
                pk = " (PRIMARY KEY)" if col["primary_key"] else ""
                lines.append(f"  - {col['name']}: {col['type']}{pk}")
            lines.append("")

        return "\n".join(lines)

    async def natural_to_sql(
        self,
        question: str,
        schema: Optional[dict] = None,
    ) -> str:
        """
        Convert natural language question to SQL using Brain.

        Args:
            question: Natural language question
            schema: Optional schema dict (fetched if not provided)

        Returns:
            SQL query string
        """
        if schema is None:
            schema = self.get_schema()

        schema_str = self.get_schema_for_prompt()

        prompt = f"""You are a SQL expert. Convert the following natural language question to a SQLite query.

{schema_str}

Question: {question}

Rules:
1. Return ONLY the SQL query, no explanation
2. Use SQLite syntax
3. Only use SELECT statements (no INSERT, UPDATE, DELETE)
4. Use table and column names exactly as shown in the schema
5. If the question cannot be answered with the available data, return: SELECT 'Cannot answer: <reason>' AS error

SQL Query:"""

        # Call Brain API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.brain_url}/v1/chat/completions",
                json={
                    "model": "default-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.1,  # Low temperature for deterministic SQL
                },
            )
            response.raise_for_status()
            result = response.json()

        # Extract SQL from response
        content = result["choices"][0]["message"]["content"]
        sql = self._extract_sql(content)

        return sql

    def _extract_sql(self, content: str) -> str:
        """
        Extract SQL query from LLM response.

        Handles responses with markdown code blocks or plain SQL.
        """
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```sql or ```)
            lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        # Clean up
        content = content.strip()

        # Remove trailing semicolon for consistency
        if content.endswith(";"):
            content = content[:-1]

        return content

    def execute(
        self,
        sql: str,
        safe: bool = True,
        params: Optional[tuple] = None,
    ) -> QueryResult:
        """
        Execute a SQL query.

        Args:
            sql: SQL query to execute
            safe: If True, only allow SELECT statements
            params: Optional query parameters

        Returns:
            QueryResult with columns, rows, and metadata

        Raises:
            UnsafeQueryError: If safe=True and query is not SELECT
        """
        sql = sql.strip()

        # Safety check using centralized validation
        if safe:
            try:
                validate_sql_query(sql, allow_write=False)
            except Exception as e:
                raise UnsafeQueryError(str(e))

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(sql, params or ())

            # Get column names
            columns = [desc[0] for desc in cursor.description or []]

            # Fetch all rows
            rows = [list(row) for row in cursor.fetchall()]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                sql=sql,
            )
        finally:
            conn.close()

    async def ask(self, question: str) -> QueryResult:
        """
        Answer a natural language question with SQL.

        Args:
            question: Natural language question

        Returns:
            QueryResult with the answer
        """
        sql = await self.natural_to_sql(question)
        return self.execute(sql)

    async def explain_results(
        self,
        question: str,
        sql: str,
        results: QueryResult,
    ) -> str:
        """
        Generate natural language explanation of query results.

        Args:
            question: Original question
            sql: SQL that was executed
            results: Query results

        Returns:
            Natural language explanation
        """
        # Format results for prompt
        if results.row_count == 0:
            results_str = "No rows returned."
        else:
            # Show first 10 rows
            rows_to_show = results.rows[:10]
            results_str = json.dumps(
                {
                    "columns": results.columns,
                    "rows": rows_to_show,
                    "total_rows": results.row_count,
                },
                indent=2,
            )

        prompt = f"""Given the following question, SQL query, and results, provide a clear, concise answer.

Question: {question}

SQL Query: {sql}

Results:
{results_str}

Answer the question directly based on the results. Be specific with numbers and data. Keep the answer to 2-3 sentences."""

        # Call Brain API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.brain_url}/v1/chat/completions",
                json={
                    "model": "default-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                },
            )
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"]
