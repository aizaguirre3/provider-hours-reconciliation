import pandas as pd

from etl.generator import generate_timesheet


EXPECTED_COLS = {"provider_id", "shift_date", "shift_type", "hours_worked", "on_call"}


def test_generates_rows_for_each_provider():
    df = generate_timesheet(seed=1)
    assert EXPECTED_COLS.issubset(df.columns)
    # 12 providers * 4-5 shifts + 2 dirt rows
    assert 12 * 4 <= len(df) <= 12 * 5 + 2


def test_reproducible_with_seed():
    a = generate_timesheet(seed=42)
    b = generate_timesheet(seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_dirty_mode_includes_unknown_provider():
    df = generate_timesheet(seed=1, dirt=True)
    assert "PROV099" in df["provider_id"].values


def test_dirty_mode_includes_negative_hours():
    df = generate_timesheet(seed=1, dirt=True)
    assert (df["hours_worked"] < 0).any()


def test_clean_mode_no_dirt():
    df = generate_timesheet(seed=1, dirt=False)
    assert "PROV099" not in df["provider_id"].values
    assert (df["hours_worked"] > 0).all()
