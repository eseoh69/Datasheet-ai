def validate_query(sql: str, schema: dict) -> dict:
    """
    Main validation entry point. Checks query type, tables, and columns.

    Args:
        sql: SQL query string to validate
        schema: dict from schema_manager.get_schema()
    Returns:
        {"valid": True} if valid
        {"valid": False, "reason": "explanation"} if invalid
    """
    pass


def is_select_query(sql: str) -> bool:
    """
    Checks that the query is a SELECT statement only.
    Rejects INSERT, UPDATE, DELETE, DROP, etc.

    Args:
        sql: SQL query string
    Returns:
        True if SELECT, False otherwise
    """
    pass


def extract_tables(sql: str) -> list:
    """
    Extracts table names referenced in the SQL query.

    Args:
        sql: SQL query string
    Returns:
        list of table name strings
    """
    pass


def extract_columns(sql: str) -> list:
    """
    Extracts column names referenced in the SQL query.

    Args:
        sql: SQL query string
    Returns:
        list of column name strings
    """
    pass


def validate_tables(tables: list, schema: dict) -> dict:
    """
    Checks that all referenced tables exist in the database schema.

    Args:
        tables: list of table names from extract_tables()
        schema: dict from schema_manager.get_schema()
    Returns:
        {"valid": True} if all tables exist
        {"valid": False, "reason": "Unknown table: X"} if not
    """
    pass


def validate_columns(columns: list, tables: list, schema: dict) -> dict:
    """
    Checks that all referenced columns exist in the referenced tables.

    Args:
        columns: list of column names from extract_columns()
        tables: list of table names from extract_tables()
        schema: dict from schema_manager.get_schema()
    Returns:
        {"valid": True} if all columns exist
        {"valid": False, "reason": "Unknown column: X"} if not
    """
    pass