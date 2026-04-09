import pytest
import pandas as pd
import os
from csv_loader.loader import load_csv, insert_data


# ── load_csv tests ──────────────────────────────────────────────

def test_load_csv_returns_dataframe(tmp_path):
    """load_csv should return a pandas DataFrame"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25\n")
    df = load_csv(str(csv_file))
    assert isinstance(df, pd.DataFrame)


def test_load_csv_correct_columns(tmp_path):
    """load_csv should return correct column names"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25\n")
    df = load_csv(str(csv_file))
    assert list(df.columns) == ["name", "age"]


def test_load_csv_correct_row_count(tmp_path):
    """load_csv should return correct number of rows"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25\n")
    df = load_csv(str(csv_file))
    assert len(df) == 2


def test_load_csv_file_not_found():
    """load_csv should raise FileNotFoundError for missing file"""
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent.csv")


def test_load_csv_empty_file(tmp_path):
    """load_csv should raise ValueError for empty file"""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")
    with pytest.raises(ValueError):
        load_csv(str(csv_file))


# ── insert_data tests ───────────────────────────────────────────

def test_insert_data_rows_exist(tmp_path):
    """insert_data should insert all rows into the database"""
    import sqlite3
    db_path = str(tmp_path / "test.db")
    df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})

    # create table first
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)")
    conn.commit()
    conn.close()

    insert_data(df, "people", db_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT name, age FROM people").fetchall()
    conn.close()
    assert len(rows) == 2


def test_insert_data_correct_values(tmp_path):
    """insert_data should insert correct values"""
    import sqlite3
    db_path = str(tmp_path / "test.db")
    df = pd.DataFrame({"name": ["Alice"], "age": [30]})

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)")
    conn.commit()
    conn.close()

    insert_data(df, "people", db_path)

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT name, age FROM people").fetchone()
    conn.close()
    assert row == ("Alice", 30)


def test_insert_data_empty_dataframe(tmp_path):
    """insert_data should raise ValueError for empty DataFrame"""
    db_path = str(tmp_path / "test.db")
    df = pd.DataFrame()
    with pytest.raises(ValueError):
        insert_data(df, "people", db_path)