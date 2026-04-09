import pytest
from sql_validator.validator import (
    validate_query,
    is_select_query,
    extract_tables,
    extract_columns,
    validate_tables,
    validate_columns,
)

# Sample schema to use across tests
# Mirrors what schema_manager.get_schema() returns
SAMPLE_SCHEMA = {
    "users": [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "age", "type": "INTEGER"},
    ],
    "orders": [
        {"name": "id", "type": "INTEGER"},
        {"name": "total", "type": "REAL"},
    ],
}


# ════════════════════════════════════════════════════════════════
# is_select_query
# ════════════════════════════════════════════════════════════════

class TestIsSelectQuery:

    def test_select_returns_true(self):
        """A basic SELECT query should return True."""
        assert is_select_query("SELECT * FROM users") == True

    def test_select_lowercase_returns_true(self):
        """SELECT in lowercase should still return True."""
        assert is_select_query("select * from users") == True

    def test_drop_returns_false(self):
        """DROP TABLE should return False."""
        assert is_select_query("DROP TABLE users") == False

    def test_delete_returns_false(self):
        """DELETE should return False."""
        assert is_select_query("DELETE FROM users") == False

    def test_insert_returns_false(self):
        """INSERT should return False."""
        assert is_select_query("INSERT INTO users (name) VALUES ('Alice')") == False

    def test_update_returns_false(self):
        """UPDATE should return False."""
        assert is_select_query("UPDATE users SET name='Bob'") == False

    def test_empty_string_returns_false(self):
        """Empty string should return False."""
        assert is_select_query("") == False


# ════════════════════════════════════════════════════════════════
# extract_tables
# ════════════════════════════════════════════════════════════════

class TestExtractTables:

    def test_single_table(self):
        """Should extract a single table name."""
        tables = extract_tables("SELECT * FROM users")
        assert "users" in tables

    def test_case_insensitive(self):
        """Table names should be normalized to lowercase."""
        tables = extract_tables("SELECT * FROM USERS")
        assert "users" in tables

    def test_multiple_tables_join(self):
        """Should extract both tables in a JOIN query."""
        tables = extract_tables("SELECT * FROM users JOIN orders ON users.id = orders.id")
        assert "users" in tables
        assert "orders" in tables


# ════════════════════════════════════════════════════════════════
# extract_columns
# ════════════════════════════════════════════════════════════════

class TestExtractColumns:

    def test_single_column(self):
        """Should extract a single column name."""
        columns = extract_columns("SELECT name FROM users")
        assert "name" in columns

    def test_multiple_columns(self):
        """Should extract multiple column names."""
        columns = extract_columns("SELECT name, age FROM users")
        assert "name" in columns
        assert "age" in columns

    def test_star_returns_empty(self):
        """SELECT * should return empty list — no specific columns to validate."""
        columns = extract_columns("SELECT * FROM users")
        assert columns == []

    def test_case_insensitive(self):
        """Column names should be normalized to lowercase."""
        columns = extract_columns("SELECT NAME FROM users")
        assert "name" in columns
    
    def test_column_with_table_prefix(self):
        """Should extract column name even when prefixed with table name e.g. users.name"""
        columns = extract_columns("SELECT users.name FROM users")
        assert "name" in columns


# ════════════════════════════════════════════════════════════════
# validate_tables
# ════════════════════════════════════════════════════════════════

class TestValidateTables:

    def test_known_table_is_valid(self):
        """A table that exists in the schema should pass."""
        result = validate_tables(["users"], SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_unknown_table_is_invalid(self):
        """A table not in the schema should fail."""
        result = validate_tables(["nonexistent"], SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_unknown_table_has_reason(self):
        """Rejection must include a reason string."""
        result = validate_tables(["nonexistent"], SAMPLE_SCHEMA)
        assert "reason" in result
        assert isinstance(result["reason"], str)

    def test_multiple_tables_all_known(self):
        """Multiple known tables should pass."""
        result = validate_tables(["users", "orders"], SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_one_unknown_in_multiple_fails(self):
        """If any table is unknown, the whole query should fail."""
        result = validate_tables(["users", "unknown_table"], SAMPLE_SCHEMA)
        assert result["valid"] == False


# ════════════════════════════════════════════════════════════════
# validate_columns
# ════════════════════════════════════════════════════════════════

class TestValidateColumns:

    def test_known_column_is_valid(self):
        """A column that exists in the table should pass."""
        result = validate_columns(["name"], ["users"], SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_unknown_column_is_invalid(self):
        """A column not in the table should fail."""
        result = validate_columns(["password"], ["users"], SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_unknown_column_has_reason(self):
        """Rejection must include a reason string."""
        result = validate_columns(["password"], ["users"], SAMPLE_SCHEMA)
        assert "reason" in result
        assert isinstance(result["reason"], str)

    def test_empty_columns_is_valid(self):
        """Empty column list (SELECT *) should always pass."""
        result = validate_columns([], ["users"], SAMPLE_SCHEMA)
        assert result["valid"] == True


# ════════════════════════════════════════════════════════════════
# validate_query (main entry point)
# ════════════════════════════════════════════════════════════════

class TestValidateQuery:

    def test_valid_select_passes(self):
        """A clean SELECT query should pass all checks."""
        result = validate_query("SELECT name FROM users", SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_select_star_passes(self):
        """SELECT * should be valid."""
        result = validate_query("SELECT * FROM users", SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_empty_string_is_invalid(self):
        """Empty query should be rejected."""
        result = validate_query("", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_drop_table_is_invalid(self):
        """DROP TABLE must be rejected."""
        result = validate_query("DROP TABLE users", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_delete_is_invalid(self):
        """DELETE must be rejected."""
        result = validate_query("DELETE FROM users", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_insert_is_invalid(self):
        """INSERT must be rejected."""
        result = validate_query("INSERT INTO users (name) VALUES ('Alice')", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_update_is_invalid(self):
        """UPDATE must be rejected."""
        result = validate_query("UPDATE users SET name='Bob'", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_semicolon_is_invalid(self):
        """Query with semicolon (SQL injection) must be rejected."""
        result = validate_query("SELECT * FROM users; DROP TABLE users", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_unknown_table_is_invalid(self):
        """Query referencing unknown table must be rejected."""
        result = validate_query("SELECT * FROM nonexistent", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_unknown_column_is_invalid(self):
        """Query referencing unknown column must be rejected."""
        result = validate_query("SELECT password FROM users", SAMPLE_SCHEMA)
        assert result["valid"] == False

    def test_case_insensitive_table(self):
        """Table names should be case insensitive."""
        result = validate_query("SELECT * FROM USERS", SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_case_insensitive_column(self):
        """Column names should be case insensitive."""
        result = validate_query("SELECT NAME FROM users", SAMPLE_SCHEMA)
        assert result["valid"] == True

    def test_invalid_query_has_reason(self):
        """Every rejected query must include a reason."""
        result = validate_query("DROP TABLE users", SAMPLE_SCHEMA)
        assert "reason" in result
        assert isinstance(result["reason"], str)