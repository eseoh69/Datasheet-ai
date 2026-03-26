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
    pass


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
    pass