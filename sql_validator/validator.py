import re


def is_select_query(sql: str) -> bool:
    """
    Checks that the query is a SELECT statement only.
    Rejects INSERT, UPDATE, DELETE, DROP, etc.
    """
    if not sql or not sql.strip():
        return False
    return sql.strip().upper().startswith("SELECT")


def extract_tables(sql: str) -> list:
    """
    Extracts table names referenced in the SQL query.
    Normalizes to lowercase.
    """
    # Match FROM and JOIN keywords followed by a table name
    pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return [m.lower() for m in matches]


def extract_columns(sql: str) -> list:
    """
    Extracts column names referenced in the SQL query.
    Returns empty list for SELECT *.
    Normalizes to lowercase.
    """
    # Get the part between SELECT and FROM
    match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
    if not match:
        return []

    columns_str = match.group(1).strip()

    # SELECT * means no specific columns to validate
    if columns_str == "*":
        return []

    # Split by comma, clean up, and strip table prefixes (e.g. users.name -> name)
    columns = []
    for c in columns_str.split(","):
        col = c.strip().lower()
        # Remove table prefix if present (e.g. users.name -> name)
        if "." in col:
            col = col.split(".")[1]
        columns.append(col)
    return columns



def validate_tables(tables: list, schema: dict) -> dict:
    """
    Checks that all referenced tables exist in the database schema.
    """
    for table in tables:
        if table not in schema:
            return {"valid": False, "reason": f"Unknown table: {table}"}
    return {"valid": True}


def validate_columns(columns: list, tables: list, schema: dict) -> dict:
    """
    Checks that all referenced columns exist in the referenced tables.
    """
    # Empty columns means SELECT * — skip validation
    if not columns:
        return {"valid": True}

    # Gather all valid columns across all referenced tables
    valid_columns = set()
    for table in tables:
        if table in schema:
            for col in schema[table]:
                valid_columns.add(col["name"].lower())

    for col in columns:
        if col not in valid_columns:
            return {"valid": False, "reason": f"Unknown column: {col}"}
    return {"valid": True}


def validate_query(sql: str, schema: dict) -> dict:
    """
    Main validation entry point. Checks query type, tables, and columns.
    """
    # Check empty
    if not sql or not sql.strip():
        return {"valid": False, "reason": "Query cannot be empty"}

    # Check for semicolon (SQL injection)
    if ";" in sql:
        return {"valid": False, "reason": "Query contains semicolon — possible SQL injection"}

    # Check it's a SELECT
    if not is_select_query(sql):
        return {"valid": False, "reason": "Only SELECT queries are allowed"}

    # Extract and validate tables
    tables = extract_tables(sql)
    table_result = validate_tables(tables, schema)
    if not table_result["valid"]:
        return table_result

    # Extract and validate columns
    columns = extract_columns(sql)
    column_result = validate_columns(columns, tables, schema)
    if not column_result["valid"]:
        return column_result

    return {"valid": True}