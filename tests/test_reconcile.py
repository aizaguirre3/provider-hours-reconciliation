import pandas as pd
import pytest

from etl.sources import init_db, load_provider_master, load_timesheet
from etl.reconcile import reconcile
from etl.generator import generate_timesheet, write_timesheet_xlsx


@pytest.fixture
def master(tmp_path):
    db = tmp_path / "master.db"
    init_db(db)
    return load_provider_master(db)


@pytest.fixture
def timesheet(tmp_path):
    df = generate_timesheet(seed=42)
    p = tmp_path / "ts.xlsx"
    write_timesheet_xlsx(df, p)
    return load_timesheet(p)


def test_reconcile_returns_expected_keys(master, timesheet):
    out = reconcile(timesheet, master)
    assert set(out.keys()) == {"utilization", "unknown_providers", "department_rollup", "summary", "dropped_rows"}


def test_utilization_one_row_per_active_provider(master, timesheet):
    out = reconcile(timesheet, master)
    assert len(out["utilization"]) == len(master)


def test_unknown_provider_detected(master, timesheet):
    out = reconcile(timesheet, master)
    assert "PROV099" in out["unknown_providers"]["provider_id"].values


def test_dropped_rows_counts_negative_hours(master, timesheet):
    out = reconcile(timesheet, master)
    assert out["dropped_rows"] >= 1  # generator injects one negative row


def test_utilization_pct_calculated(master, timesheet):
    out = reconcile(timesheet, master)
    util = out["utilization"]
    sample = util.iloc[0]
    expected = round(sample["actual_hours"] / sample["contracted_hours_per_week"], 3)
    assert sample["utilization_pct"] == expected


def test_estimated_cost_calculated(master, timesheet):
    out = reconcile(timesheet, master)
    util = out["utilization"]
    sample = util.iloc[0]
    expected = round(sample["actual_hours"] * sample["hourly_rate"], 2)
    assert sample["estimated_cost"] == expected


def test_overtime_flag_set_when_over_threshold():
    master = pd.DataFrame([{
        "provider_id": "P1", "npi": "1", "last_name": "A", "first_name": "B",
        "credentials": "MD", "department_code": "X", "department_name": "X",
        "utilization_target": 0.85, "contracted_hours_per_week": 40, "hourly_rate": 100,
    }])
    ts = pd.DataFrame([
        {"provider_id": "P1", "shift_date": pd.Timestamp("2025-01-01"), "shift_type": "DAY", "hours_worked": 50, "on_call": False},
    ])
    out = reconcile(ts, master)
    assert "overtime" in out["utilization"].iloc[0]["exceptions"]


def test_missing_timesheet_flag_set(master):
    empty_ts = pd.DataFrame(columns=["provider_id", "shift_date", "shift_type", "hours_worked", "on_call"])
    empty_ts["hours_worked"] = pd.to_numeric(empty_ts["hours_worked"])
    out = reconcile(empty_ts, master)
    assert (out["utilization"]["exceptions"] == "missing_timesheet").all()


def test_summary_overall_utilization(master, timesheet):
    out = reconcile(timesheet, master)
    s = out["summary"]
    assert "overall_utilization_pct" in s
    assert 0 <= s["overall_utilization_pct"] <= 2  # sanity bound


def test_department_rollup_one_row_per_department(master, timesheet):
    out = reconcile(timesheet, master)
    assert len(out["department_rollup"]) == master["department_code"].nunique()
