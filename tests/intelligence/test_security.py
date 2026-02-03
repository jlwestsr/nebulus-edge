"""Tests for the security module."""

import pytest

from intelligence.core.security import (
    ValidationError,
    quote_identifier,
    sanitize_table_name,
    validate_column_name,
    validate_limit,
    validate_sql_query,
    validate_table_name,
)


class TestValidateTableName:
    """Tests for validate_table_name function."""

    def test_valid_table_names(self):
        """Test that valid table names pass validation."""
        assert validate_table_name("users") == "users"
        assert validate_table_name("user_data") == "user_data"
        assert validate_table_name("Table1") == "Table1"
        assert validate_table_name("_private") == "_private"

    def test_empty_table_name(self):
        """Test that empty table name raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_table_name("")

    def test_table_name_too_long(self):
        """Test that very long table name raises error."""
        long_name = "a" * 200
        with pytest.raises(ValidationError, match="too long"):
            validate_table_name(long_name)

    def test_invalid_characters(self):
        """Test that invalid characters raise error."""
        with pytest.raises(ValidationError, match="Invalid table name"):
            validate_table_name("users; DROP TABLE")

        with pytest.raises(ValidationError, match="Invalid table name"):
            validate_table_name("users--comment")

        with pytest.raises(ValidationError, match="Invalid table name"):
            validate_table_name("table with spaces")

    def test_reserved_keywords(self):
        """Test that SQL reserved keywords raise error."""
        with pytest.raises(ValidationError, match="reserved SQL keyword"):
            validate_table_name("select")

        with pytest.raises(ValidationError, match="reserved SQL keyword"):
            validate_table_name("DROP")

        with pytest.raises(ValidationError, match="reserved SQL keyword"):
            validate_table_name("TABLE")


class TestValidateColumnName:
    """Tests for validate_column_name function."""

    def test_valid_column_names(self):
        """Test that valid column names pass validation."""
        assert validate_column_name("id") == "id"
        assert validate_column_name("user_name") == "user_name"
        assert validate_column_name("Column1") == "Column1"

    def test_empty_column_name(self):
        """Test that empty column name raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_column_name("")

    def test_invalid_column_characters(self):
        """Test that invalid characters raise error."""
        with pytest.raises(ValidationError, match="Invalid column name"):
            validate_column_name("column; DROP")


class TestSanitizeTableName:
    """Tests for sanitize_table_name function."""

    def test_basic_sanitization(self):
        """Test basic table name sanitization."""
        assert sanitize_table_name("users") == "users"
        assert sanitize_table_name("User Data") == "user_data"
        assert sanitize_table_name("table-name") == "table_name"

    def test_empty_input(self):
        """Test that empty input returns default."""
        assert sanitize_table_name("") == "table_data"

    def test_numeric_start(self):
        """Test that names starting with numbers are prefixed."""
        assert sanitize_table_name("123table") == "t_123table"

    def test_reserved_keyword(self):
        """Test that reserved keywords are suffixed."""
        assert sanitize_table_name("select") == "select_table"

    def test_special_characters(self):
        """Test that special characters are replaced and trailing underscores stripped."""
        assert sanitize_table_name("my@table!") == "my_table"


class TestQuoteIdentifier:
    """Tests for quote_identifier function."""

    def test_basic_quoting(self):
        """Test basic identifier quoting."""
        assert quote_identifier("users") == '"users"'
        assert quote_identifier("user_data") == '"user_data"'

    def test_double_quote_escaping(self):
        """Test that double quotes are escaped."""
        assert quote_identifier('user"name') == '"user""name"'


class TestValidateSqlQuery:
    """Tests for validate_sql_query function."""

    def test_valid_select_queries(self):
        """Test that valid SELECT queries pass."""
        assert validate_sql_query("SELECT * FROM users") == "SELECT * FROM users"
        assert (
            validate_sql_query("SELECT id, name FROM users WHERE id = 1")
            == "SELECT id, name FROM users WHERE id = 1"
        )

    def test_empty_query(self):
        """Test that empty query raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_sql_query("")

    def test_non_select_blocked(self):
        """Test that non-SELECT queries are blocked."""
        with pytest.raises(ValidationError, match="Only SELECT"):
            validate_sql_query("INSERT INTO users VALUES (1)")

        with pytest.raises(ValidationError, match="Only SELECT"):
            validate_sql_query("UPDATE users SET name = 'x'")

        with pytest.raises(ValidationError, match="Only SELECT"):
            validate_sql_query("DELETE FROM users")

    def test_dangerous_keywords_blocked(self):
        """Test that dangerous keywords in SELECT are blocked."""
        with pytest.raises(ValidationError, match="forbidden keyword"):
            validate_sql_query("SELECT * FROM users; DROP TABLE users")

        with pytest.raises(ValidationError, match="forbidden keyword"):
            validate_sql_query("SELECT * FROM (DELETE FROM users RETURNING *)")

    def test_comment_injection_blocked(self):
        """Test that SQL comments are blocked."""
        with pytest.raises(ValidationError, match="comments"):
            validate_sql_query("SELECT * FROM users -- WHERE id = 1")

        with pytest.raises(ValidationError, match="comments"):
            validate_sql_query("SELECT * /* comment */ FROM users")

    def test_multiple_statements_blocked(self):
        """Test that multiple SQL statements are blocked."""
        with pytest.raises(ValidationError, match="Multiple SQL"):
            validate_sql_query("SELECT 1; SELECT 2")

    def test_allow_write_mode(self):
        """Test that allow_write=True permits write operations."""
        # These should not raise when allow_write=True
        validate_sql_query("INSERT INTO users VALUES (1)", allow_write=True)
        validate_sql_query("UPDATE users SET name = 'x'", allow_write=True)


class TestValidateLimit:
    """Tests for validate_limit function."""

    def test_valid_limits(self):
        """Test that valid limits are accepted."""
        assert validate_limit(10) == 10
        assert validate_limit(100) == 100
        assert validate_limit(None) == 10000  # Default max

    def test_limit_capped(self):
        """Test that limits are capped at max."""
        assert validate_limit(50000) == 10000
        assert validate_limit(100, max_limit=50) == 50

    def test_negative_limit(self):
        """Test that negative limits raise error."""
        with pytest.raises(ValidationError, match="non-negative"):
            validate_limit(-1)
