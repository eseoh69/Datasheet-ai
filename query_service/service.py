import sqlite3

from schema_manager.manager import get_schema
from sql_validator.validator import validate_query


def get_schema_context(db_path: str) -> str:
    """
    Retrieves the database schema and formats it as a string
    to be passed to the LLM as context.

    Args:
        db_path: path to the SQLite database
    Returns:
        formatted string describing all tables and columns
    Raises:
        sqlite3.Error: if database cannot be opened
    """
    schema = get_schema(db_path)
    if not schema:
        return "No tables found in the database."

    lines = []
    for table_name, columns in schema.items():
        col_descriptions = ", ".join(
            f"{col['name']} ({col['type']})" for col in columns
        )
        lines.append(f"- {table_name}: {col_descriptions}")

    return "Database schema:\n" + "\n".join(lines)


def execute_query(db_path: str, sql: str) -> list:
    """
    Executes a validated SQL query against the database.
    NOTE: CLI must never call this directly — always go through process_query.

    Args:
        db_path: path to the SQLite database
        sql: a validated SQL query string
    Returns:
        list of dicts representing rows e.g. [{"col": val}, ...]
    Raises:
        sqlite3.Error: if execution fails
    """
    conn = sqlite3.connect(db_path)
    # row_factory makes each row behave like a dict keyed by column name
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def process_query(db_path: str, sql: str) -> list:
    """
    Full pipeline: validate the SQL then execute it.
    This is the main entry point for the CLI.

    Args:
        db_path: path to the SQLite database
        sql: SQL query string to validate and execute
    Returns:
        list of dicts representing query results
    Raises:
        ValueError: if validation fails
        sqlite3.Error: if execution fails
    """
    schema = get_schema(db_path)
    result = validate_query(sql, schema)

    if not result.get("valid"):
        raise ValueError(result.get("reason", "Invalid query"))

    return execute_query(db_path, sql)


def format_results(results: list) -> str:
    """
    Formats query results into a readable string for display.

    Args:
        results: list of dicts from execute_query()
    Returns:
        formatted string of results
    """
    if not results:
        return "No results found."

    # Print a simple aligned table: header row then one line per row
    headers = list(results[0].keys())
    header_line = " | ".join(headers)
    separator = "-" * len(header_line)

    data_lines = [
        " | ".join(str(row.get(h, "")) for h in headers)
        for row in results
    ]

    return "\n".join([header_line, separator] + data_lines)