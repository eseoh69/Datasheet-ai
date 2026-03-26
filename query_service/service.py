import sqlite3


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
    pass


def execute_query(db_path: str, sql: str) -> list:
    """
    Executes a validated SQL query against the database.
    NOTE: CLI must never call this directly — always go through query_service.

    Args:
        db_path: path to the SQLite database
        sql: a validated SQL query string
    Returns:
        list of dicts representing rows e.g. [{"col": val}, ...]
    Raises:
        ValueError: if query is not validated
        sqlite3.Error: if execution fails
    """
    pass


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
    pass


def format_results(results: list) -> str:
    """
    Formats query results into a readable string for display.

    Args:
        results: list of dicts from execute_query()
    Returns:
        formatted string of results
    """
    pass