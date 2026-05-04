import pandas as pd
import pytest

from etl.sources import init_db, load_provider_master, load_timesheet, run_query
from etl.generator import generate_timesheet, write_timesheet_xlsx


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "master.db"
    init_db(p)
    return p


def test_init_db_creates_file(db):
    assert db.exists()


def test_load_provider_master_returns_active_only(db):
    df = load_provider_master(db)
    assert len(df) > 0
    expected = {"provider_id", "npi", "department_name", "contracted_hours_per_week", "hourly_rate", "utilization_target"}
    assert expected.issubset(df.columns)
    # PROV013 is seeded as inactive — should not appear
    assert "PROV013" not in df["provider_id"].values


def test_run_query_active_providers(db):
    df = run_query(db, "active_providers")
    assert len(df) > 0
    assert "provider_id" in df.columns


def test_run_query_unknown_raises(db):
    with pytest.raises(FileNotFoundError):
        run_query(db, "no_such_query")


def test_load_timesheet_parses_and_normalizes(tmp_path):
    df = generate_timesheet(seed=1)
    p = tmp_path / "ts.xlsx"
    write_timesheet_xlsx(df, p)
    out = load_timesheet(p)
    assert pd.api.types.is_datetime64_any_dtype(out["shift_date"])
    assert pd.api.types.is_numeric_dtype(out["hours_worked"])
    assert out["on_call"].dtype == bool
    # provider_id whitespace should be stripped
    assert all(pid == pid.strip() for pid in out["provider_id"])
