"""Load provider master from sqlite and timesheet uploads from Excel."""
import sqlite3
from pathlib import Path

import pandas as pd


SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
QUERIES_DIR = SQL_DIR / "queries"


_YN_TRUE = {"y", "yes", "true", "t", "1", "1.0"}


def _yn_to_bool(v):
    if pd.isna(v):
        return False
    return str(v).strip().lower() in _YN_TRUE


def init_db(db_path):
    """Create the provider master DB from schema.sql + seed.sql."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript((SQL_DIR / "schema.sql").read_text())
        conn.executescript((SQL_DIR / "seed.sql").read_text())
        conn.commit()
    finally:
        conn.close()


def load_provider_master(db_path):
    """Load active providers with department metadata via the provider_master query."""
    conn = sqlite3.connect(db_path)
    try:
        sql = (QUERIES_DIR / "provider_master.sql").read_text()
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def run_query(db_path, query_name):
    """Run a named .sql file from sql/queries against the DB and return a DataFrame."""
    sql_path = QUERIES_DIR / f"{query_name}.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"Query not found: {query_name}")
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql_path.read_text(), conn)
    finally:
        conn.close()


def load_timesheet(excel_path, sheet_name=0):
    """Load and lightly normalize a timesheet Excel file.

    - Strips whitespace on string identifier columns.
    - Coerces hours_worked to numeric.
    - Coerces on_call to bool (handles Y/N/yes/no/1/0/true/false).
    - Parses shift_date with pandas date inference.
    """
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    if "provider_id" in df.columns:
        df["provider_id"] = df["provider_id"].astype(str).str.strip()
    if "shift_type" in df.columns:
        df["shift_type"] = df["shift_type"].astype(str).str.strip().str.upper()
    if "hours_worked" in df.columns:
        df["hours_worked"] = pd.to_numeric(df["hours_worked"], errors="coerce")
    if "on_call" in df.columns:
        df["on_call"] = df["on_call"].map(_yn_to_bool)
    if "shift_date" in df.columns:
        df["shift_date"] = pd.to_datetime(df["shift_date"], errors="coerce", format="mixed")
    return df
