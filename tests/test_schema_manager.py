import pytest
import sqlite3
import pandas as pd

from schema_manager.manager import (
    get_schema,
    infer_schema,
    compare_schema,
    create_table,
    drop_table,
)


# ── Helpers ─────────────────────────────────────────────────────

def make_db(tmp_path, ddl_statements=None):
    """Create a temporary SQLite database, optionally running DDL statements."""
    db_path = str(tmp_path / "test.db")
    if ddl_statements:
        conn = sqlite3.connect(db_path)
        for stmt in ddl_statements:
            conn.execute(stmt)
        conn.commit()
        conn.close()
    return db_path


# ════════════════════════════════════════════════════════════════
# get_schema
# ════════════════════════════════════════════════════════════════
# get_schema must discover every table in the database and return
# column names + types exactly as SQLite stores them.

class TestGetSchema:

    def test_empty_database_returns_empty_dict(self, tmp_path):
        """An empty database has no tables, so the result must be {}."""
        db_path = make_db(tmp_path)
        schema = get_schema(db_path)
        assert schema == {}

    def test_single_table_present(self, tmp_path):
        """A database with one table must include that table in the result."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)"
        ])
        schema = get_schema(db_path)
        assert "users" in schema

    def test_single_table_column_names(self, tmp_path):
        """Column names returned must match the DDL."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)"
        ])
        schema = get_schema(db_path)
        col_names = [c["name"] for c in schema["users"]]
        assert "name" in col_names
        assert "age" in col_names

    def test_single_table_column_types(self, tmp_path):
        """Column types returned must match the SQL types used in CREATE TABLE."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, price REAL, label TEXT)"
        ])
        schema = get_schema(db_path)
        type_map = {c["name"]: c["type"] for c in schema["products"]}
        assert type_map["price"] == "REAL"
        assert type_map["label"] == "TEXT"

    def test_multiple_tables_all_present(self, tmp_path):
        """All tables in the database must appear as keys in the result."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)",
            "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL)",
        ])
        schema = get_schema(db_path)
        assert "users" in schema
        assert "orders" in schema

    def test_multiple_tables_independent_columns(self, tmp_path):
        """Each table's columns must be listed separately, not mixed together."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)",
            "CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, total REAL)",
        ])
        schema = get_schema(db_path)
        user_cols = [c["name"] for c in schema["users"]]
        order_cols = [c["name"] for c in schema["orders"]]
        assert "name" in user_cols
        assert "total" not in user_cols
        assert "total" in order_cols
        assert "name" not in order_cols

    def test_returns_list_of_dicts(self, tmp_path):
        """Each table's value must be a list of dicts with 'name' and 'type' keys."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT)"
        ])
        schema = get_schema(db_path)
        assert isinstance(schema["items"], list)
        for col in schema["items"]:
            assert "name" in col
            assert "type" in col


# ════════════════════════════════════════════════════════════════
# infer_schema
# ════════════════════════════════════════════════════════════════
# infer_schema inspects a DataFrame and maps each column's pandas
# dtype to the correct SQL type (TEXT, INTEGER, REAL).

class TestInferSchema:

    def test_integer_column_maps_to_integer(self):
        """Pandas int64 columns should map to INTEGER."""
        df = pd.DataFrame({"age": [25, 30]})
        schema = infer_schema(df)
        assert schema["age"] == "INTEGER"

    def test_float_column_maps_to_real(self):
        """Pandas float64 columns should map to REAL."""
        df = pd.DataFrame({"score": [9.5, 7.2]})
        schema = infer_schema(df)
        assert schema["score"] == "REAL"

    def test_string_column_maps_to_text(self):
        """Pandas object (string) columns should map to TEXT."""
        df = pd.DataFrame({"name": ["Alice", "Bob"]})
        schema = infer_schema(df)
        assert schema["name"] == "TEXT"

    def test_mixed_columns(self):
        """A DataFrame with multiple types should map each column correctly."""
        df = pd.DataFrame({
            "name": ["Alice"],
            "age": [30],
            "score": [9.5],
        })
        schema = infer_schema(df)
        assert schema["name"] == "TEXT"
        assert schema["age"] == "INTEGER"
        assert schema["score"] == "REAL"

    def test_returns_all_column_names(self):
        """Every column in the DataFrame must appear as a key in the result."""
        df = pd.DataFrame({"a": [1], "b": ["x"], "c": [3.0]})
        schema = infer_schema(df)
        assert set(schema.keys()) == {"a", "b", "c"}

    def test_returns_dict(self):
        """Return type must be a dict."""
        df = pd.DataFrame({"x": [1]})
        result = infer_schema(df)
        assert isinstance(result, dict)


# ════════════════════════════════════════════════════════════════
# compare_schema
# ════════════════════════════════════════════════════════════════
# compare_schema decides whether to APPEND data to an existing
# table or CREATE a new one.  "append" only if column names AND
# types all match; "create" for any mismatch.

class TestCompareSchema:
    # existing schema uses the format returned by get_schema:
    # [{"name": col_name, "type": col_type}]

    def _existing(self, *cols):
        """Helper: build an existing schema list from (name, type) pairs."""
        return [{"name": n, "type": t} for n, t in cols]

    def test_identical_schemas_return_append(self):
        """Exact match -> 'append'."""
        existing = self._existing(("name", "TEXT"), ("age", "INTEGER"))
        incoming = {"name": "TEXT", "age": "INTEGER"}
        assert compare_schema(existing, incoming) == "append"

    def test_different_column_names_return_create(self):
        """Different column names -> 'create'."""
        existing = self._existing(("name", "TEXT"), ("age", "INTEGER"))
        incoming = {"username": "TEXT", "age": "INTEGER"}
        assert compare_schema(existing, incoming) == "create"

    def test_different_column_types_return_create(self):
        """Same names but different types -> 'create'."""
        existing = self._existing(("name", "TEXT"), ("age", "INTEGER"))
        incoming = {"name": "TEXT", "age": "REAL"}   # age type differs
        assert compare_schema(existing, incoming) == "create"

    def test_extra_column_in_incoming_returns_create(self):
        """Incoming has more columns than existing -> 'create'."""
        existing = self._existing(("name", "TEXT"))
        incoming = {"name": "TEXT", "age": "INTEGER"}
        assert compare_schema(existing, incoming) == "create"

    def test_missing_column_in_incoming_returns_create(self):
        """Incoming has fewer columns than existing -> 'create'."""
        existing = self._existing(("name", "TEXT"), ("age", "INTEGER"))
        incoming = {"name": "TEXT"}
        assert compare_schema(existing, incoming) == "create"

    def test_empty_schemas_return_append(self):
        """Two empty schemas are considered matching."""
        assert compare_schema([], {}) == "append"

    def test_return_value_is_string(self):
        """Return type must be the string 'append' or 'create'."""
        existing = self._existing(("x", "TEXT"))
        incoming = {"x": "TEXT"}
        result = compare_schema(existing, incoming)
        assert isinstance(result, str)
        assert result in ("append", "create")


# ════════════════════════════════════════════════════════════════
# create_table
# ════════════════════════════════════════════════════════════════
# create_table must always add 'id INTEGER PRIMARY KEY AUTOINCREMENT'
# in addition to the user-supplied columns.

class TestCreateTable:

    def test_table_exists_after_creation(self, tmp_path):
        """After create_table the table must be discoverable via get_schema."""
        db_path = make_db(tmp_path)
        create_table(db_path, "employees", {"name": "TEXT", "salary": "REAL"})
        schema = get_schema(db_path)
        assert "employees" in schema

    def test_autoincrement_id_column_added(self, tmp_path):
        """create_table must automatically add an 'id' primary key column."""
        db_path = make_db(tmp_path)
        create_table(db_path, "employees", {"name": "TEXT"})
        schema = get_schema(db_path)
        col_names = [c["name"] for c in schema["employees"]]
        assert "id" in col_names

    def test_user_columns_present(self, tmp_path):
        """All columns passed in schema dict must be in the created table."""
        db_path = make_db(tmp_path)
        create_table(db_path, "products", {"label": "TEXT", "price": "REAL", "qty": "INTEGER"})
        schema = get_schema(db_path)
        col_names = [c["name"] for c in schema["products"]]
        assert "label" in col_names
        assert "price" in col_names
        assert "qty" in col_names

    def test_id_is_autoincrement(self, tmp_path):
        """Rows inserted without specifying id should get auto-incremented ids."""
        db_path = make_db(tmp_path)
        create_table(db_path, "items", {"name": "TEXT"})
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO items (name) VALUES ('alpha')")
        conn.execute("INSERT INTO items (name) VALUES ('beta')")
        conn.commit()
        rows = conn.execute("SELECT id FROM items ORDER BY id").fetchall()
        conn.close()
        assert rows[0][0] == 1
        assert rows[1][0] == 2

    def test_correct_column_types(self, tmp_path):
        """Column types in the created table must match the schema dict."""
        db_path = make_db(tmp_path)
        create_table(db_path, "readings", {"sensor": "TEXT", "value": "REAL"})
        schema = get_schema(db_path)
        type_map = {c["name"]: c["type"] for c in schema["readings"]}
        assert type_map["sensor"] == "TEXT"
        assert type_map["value"] == "REAL"

    def test_raises_on_duplicate_table(self, tmp_path):
        """Creating a table that already exists must raise sqlite3.Error."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE things (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        ])
        with pytest.raises(sqlite3.Error):
            create_table(db_path, "things", {"name": "TEXT"})


# ════════════════════════════════════════════════════════════════
# drop_table
# ════════════════════════════════════════════════════════════════

class TestDropTable:

    def test_table_removed_after_drop(self, tmp_path):
        """After drop_table the table must no longer appear in get_schema."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE temp_data (id INTEGER PRIMARY KEY AUTOINCREMENT, val TEXT)"
        ])
        drop_table(db_path, "temp_data")
        schema = get_schema(db_path)
        assert "temp_data" not in schema

    def test_other_tables_unaffected(self, tmp_path):
        """Dropping one table must not affect other tables in the database."""
        db_path = make_db(tmp_path, [
            "CREATE TABLE keep_me (id INTEGER PRIMARY KEY AUTOINCREMENT, x TEXT)",
            "CREATE TABLE remove_me (id INTEGER PRIMARY KEY AUTOINCREMENT, y TEXT)",
        ])
        drop_table(db_path, "remove_me")
        schema = get_schema(db_path)
        assert "keep_me" in schema
        assert "remove_me" not in schema
