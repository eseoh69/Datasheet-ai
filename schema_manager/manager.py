import sqlite3


def get_schema(db_path: str) -> dict:
    """
    Discovers all tables and their columns in the database.

    Args:
        db_path: path to the SQLite database
    Returns:
        dict of {table_name: [{"name": col_name, "type": col_type}]}
    Raises:
        sqlite3.Error: if database cannot be opened
    """
    pass


def infer_schema(df) -> dict:
    """
    Inspects a DataFrame and maps column names to SQL types.

    Args:
        df: pandas DataFrame
    Returns:
        dict of {column_name: sql_type} e.g. {"age": "INTEGER", "name": "TEXT"}
    """
    pass


def compare_schema(existing: dict, incoming: dict) -> str:
    """
    Compares an incoming schema against an existing table schema.

    Args:
        existing: schema from get_schema() for a specific table
        incoming: schema from infer_schema()
    Returns:
        "append" if schemas match, "create" if they don't
    """
    pass


def create_table(db_path: str, table_name: str, schema: dict) -> None:
    """
    Creates a new table in the database with an auto-increment primary key.
    Always adds: id INTEGER PRIMARY KEY AUTOINCREMENT

    Args:
        db_path: path to the SQLite database
        table_name: name of the table to create
        schema: dict of {column_name: sql_type}
    Raises:
        sqlite3.Error: if table creation fails
    """
    pass


def drop_table(db_path: str, table_name: str) -> None:
    """
    Drops a table from the database.

    Args:
        db_path: path to the SQLite database
        table_name: name of the table to drop
    Raises:
        sqlite3.Error: if drop fails
    """
    pass