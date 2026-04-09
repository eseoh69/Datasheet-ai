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
    conn = sqlite3.connect(db_path)
    try:
        # sqlite_master holds the names of all user-created objects.
        # We filter for 'table' to exclude indexes and views.
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in table_names:
            # PRAGMA table_info returns one row per column:
            # (cid, name, type, notnull, dflt_value, pk)
            info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            schema[table] = [{"name": row[1], "type": row[2]} for row in info]

        return schema
    finally:
        conn.close()


def infer_schema(df) -> dict:
    """
    Inspects a DataFrame and maps column names to SQL types.

    Args:
        df: pandas DataFrame
    Returns:
        dict of {column_name: sql_type} e.g. {"age": "INTEGER", "name": "TEXT"}
    """
    # Pandas dtype groups → SQL type mapping
    type_map = {}
    for col, dtype in df.dtypes.items():
        if dtype.kind == "i":          # signed integer (int8, int16, int32, int64)
            type_map[col] = "INTEGER"
        elif dtype.kind == "f":        # floating point (float32, float64)
            type_map[col] = "REAL"
        else:                          # object, bool, datetime, etc. → store as text
            type_map[col] = "TEXT"
    return type_map


def compare_schema(existing: list, incoming: dict) -> str:
    """
    Compares an incoming schema against an existing table schema.

    Args:
        existing: schema from get_schema() for a specific table
                  — a list of {"name": ..., "type": ...} dicts
        incoming: schema from infer_schema() — {column_name: sql_type}
    Returns:
        "append" if schemas match, "create" if they don't
    """
    # Convert the list-of-dicts format that get_schema() produces into
    # the same {name: type} dict format that infer_schema() produces,
    # then compare.  We exclude the auto-added 'id' column so it doesn't
    # block an otherwise valid match.
    existing_map = {
        col["name"]: col["type"]
        for col in existing
        if col["name"] != "id"
    }
    return "append" if existing_map == incoming else "create"


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
    # Build column definitions, always starting with the primary key.
    col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
    for col_name, col_type in schema.items():
        col_defs.append(f"{col_name} {col_type}")

    ddl = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def drop_table(db_path: str, table_name: str) -> None:
    """
    Drops a table from the database.

    Args:
        db_path: path to the SQLite database
        table_name: name of the table to drop
    Raises:
        sqlite3.Error: if drop fails
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(f"DROP TABLE {table_name}")
        conn.commit()
    finally:
        conn.close()