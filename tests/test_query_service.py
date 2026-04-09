import pytest
import sqlite3
from unittest.mock import patch

from query_service.service import (
    get_schema_context,
    execute_query,
    process_query,
    format_results,
)


# ── Helpers ─────────────────────────────────────────────────────

def make_db(tmp_path):
    """Create a test database with a users table and two rows."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE users "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)"
    )
    conn.execute("INSERT INTO users (name, age) VALUES ('Alice', 30)")
    conn.execute("INSERT INTO users (name, age) VALUES ('Bob', 25)")
    conn.commit()
    conn.close()
    return db_path


# ════════════════════════════════════════════════════════════════
# get_schema_context
# ════════════════════════════════════════════════════════════════
# get_schema_context must produce a human-readable string that
# describes all tables and their columns so the LLM knows the
# database structure before it generates SQL.

class TestGetSchemaContext:

    def test_returns_string(self, tmp_path):
        """Result must be a string."""
        db_path = make_db(tmp_path)
        result = get_schema_context(db_path)
        assert isinstance(result, str)

    def test_contains_table_name(self, tmp_path):
        """Table name must appear somewhere in the context string."""
        db_path = make_db(tmp_path)
        result = get_schema_context(db_path)
        assert "users" in result

    def test_contains_column_names(self, tmp_path):
        """Column names must appear in the context string."""
        db_path = make_db(tmp_path)
        result = get_schema_context(db_path)
        assert "name" in result
        assert "age" in result

    def test_empty_database_returns_string(self, tmp_path):
        """An empty database should still return a string (possibly empty or 'no tables')."""
        db_path = str(tmp_path / "empty.db")
        sqlite3.connect(db_path).close()
        result = get_schema_context(db_path)
        assert isinstance(result, str)

    def test_multiple_tables_both_in_context(self, tmp_path):
        """All tables must be represented in the schema context."""
        db_path = str(tmp_path / "multi.db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL)")
        conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
        conn.commit()
        conn.close()
        result = get_schema_context(db_path)
        assert "orders" in result
        assert "customers" in result


# ════════════════════════════════════════════════════════════════
# execute_query
# ════════════════════════════════════════════════════════════════
# execute_query runs a validated SQL SELECT and returns rows as
# a list of dicts.  It must NOT accept unvalidated SQL — that
# guard lives in process_query, which calls the validator first.

class TestExecuteQuery:

    def test_returns_list(self, tmp_path):
        """execute_query must return a list."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT * FROM users")
        assert isinstance(result, list)

    def test_returns_list_of_dicts(self, tmp_path):
        """Each row in the result must be a dict."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT * FROM users")
        assert len(result) > 0
        assert isinstance(result[0], dict)

    def test_correct_row_count(self, tmp_path):
        """Row count must match what is actually in the table."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT * FROM users")
        assert len(result) == 2

    def test_correct_column_keys(self, tmp_path):
        """Dict keys must match the selected column names."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT name, age FROM users")
        assert "name" in result[0]
        assert "age" in result[0]

    def test_correct_values(self, tmp_path):
        """Values must match what was inserted."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT name FROM users WHERE name='Alice'")
        assert result[0]["name"] == "Alice"

    def test_empty_result_returns_empty_list(self, tmp_path):
        """A query that matches no rows must return an empty list, not None."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT * FROM users WHERE age > 999")
        assert result == []

    def test_where_clause_filters_correctly(self, tmp_path):
        """WHERE clause must reduce the result set correctly."""
        db_path = make_db(tmp_path)
        result = execute_query(db_path, "SELECT name FROM users WHERE age = 30")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"


# ════════════════════════════════════════════════════════════════
# process_query
# ════════════════════════════════════════════════════════════════
# process_query is the main entry point for the CLI.  It calls
# the SQL Validator first and only executes if the query passes.
# We mock the validator here so Query Service tests stay isolated.

class TestProcessQuery:

    def test_valid_query_returns_results(self, tmp_path):
        """A query that passes validation should return results."""
        db_path = make_db(tmp_path)
        # Patch the validator so it always says valid — we're testing
        # process_query's flow, not the validator's logic.
        with patch("query_service.service.validate_query", return_value={"valid": True}):
            result = process_query(db_path, "SELECT * FROM users")
        assert isinstance(result, list)
        assert len(result) == 2

    def test_invalid_query_raises_value_error(self, tmp_path):
        """A query rejected by the validator must raise ValueError."""
        db_path = make_db(tmp_path)
        with patch(
            "query_service.service.validate_query",
            return_value={"valid": False, "reason": "Only SELECT is allowed"}
        ):
            with pytest.raises(ValueError, match="Only SELECT is allowed"):
                process_query(db_path, "DROP TABLE users")

    def test_process_query_calls_validator(self, tmp_path):
        """process_query must call validate_query before executing."""
        db_path = make_db(tmp_path)
        with patch("query_service.service.validate_query", return_value={"valid": True}) as mock_v:
            process_query(db_path, "SELECT * FROM users")
        mock_v.assert_called_once()


# ════════════════════════════════════════════════════════════════
# format_results
# ════════════════════════════════════════════════════════════════
# format_results converts a list-of-dicts into a printable string.
# It does not access the database — pure formatting logic.

class TestFormatResults:

    def test_returns_string(self):
        """format_results must always return a string."""
        result = format_results([{"name": "Alice", "age": 30}])
        assert isinstance(result, str)

    def test_contains_values(self):
        """The formatted string must include the data values."""
        result = format_results([{"name": "Alice", "age": 30}])
        assert "Alice" in result
        assert "30" in result

    def test_empty_list_returns_string(self):
        """An empty result set must return a string (not raise an error)."""
        result = format_results([])
        assert isinstance(result, str)

    def test_multiple_rows_all_present(self):
        """All rows must appear in the formatted output."""
        rows = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = format_results(rows)
        assert "Alice" in result
        assert "Bob" in result
