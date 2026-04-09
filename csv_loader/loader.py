import pandas as pd
import sqlite3


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Reads a CSV file and returns it as a pandas DataFrame.

    Args:
        file_path: path to the CSV file
    Returns:
        DataFrame with the CSV contents
    Raises:
        FileNotFoundError: if the file doesn't exist
        ValueError: if the file is not a valid CSV
    """
    # pd.read_csv raises FileNotFoundError for missing files and
    # pd.errors.EmptyDataError (a subclass of ValueError) for empty files,
    # so both exception types propagate to callers automatically.
    return pd.read_csv(file_path)


def insert_data(df: pd.DataFrame, table_name: str, db_path: str) -> None:
    """
    Inserts DataFrame rows into a SQLite table one by one.
    NOTE: must NOT use df.to_sql()

    Args:
        df: DataFrame to insert
        table_name: name of the target table
        db_path: path to the SQLite database
    Raises:
        ValueError: if DataFrame is empty
        sqlite3.Error: if insertion fails
    """
    if df.empty:
        raise ValueError("Cannot insert an empty DataFrame.")

    columns = list(df.columns)
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

    conn = sqlite3.connect(db_path)
    try:
        for _, row in df.iterrows():
            conn.execute(sql, tuple(row))
        conn.commit()
    finally:
        conn.close()