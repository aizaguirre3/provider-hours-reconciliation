"""Generate a synthetic weekly timesheet Excel file with realistic dirt."""
import random
from datetime import datetime, timedelta

import pandas as pd


DEFAULT_PROVIDERS = [f"PROV{i:03d}" for i in range(1, 13)]  # PROV001..PROV012


def generate_timesheet(week_start="2025-11-03", providers=None, seed=42, dirt=True):
    """Generate ~5 shifts per provider for a given week.

    Realistic dirt when dirt=True:
      - Trailing whitespace on some provider IDs
      - Mixed date formats on some rows (US vs ISO)
      - on_call as "1"/"0" instead of "Y"/"N" on some rows
      - One unknown provider_id (PROV099)
      - One negative-hours data entry error
    """
    rng = random.Random(seed)
    providers = providers or DEFAULT_PROVIDERS
    start = datetime.strptime(week_start, "%Y-%m-%d")
    rows = []

    for pid in providers:
        n_shifts = rng.randint(4, 5)
        weekdays_used = set()
        for _ in range(n_shifts):
            day_offset = rng.choice([0, 1, 2, 3, 4])
            while day_offset in weekdays_used and len(weekdays_used) < 5:
                day_offset = rng.choice([0, 1, 2, 3, 4])
            weekdays_used.add(day_offset)
            shift_dt = start + timedelta(days=day_offset)
            shift_type = rng.choices(
                ["DAY", "EVENING", "NIGHT", "CALL"],
                weights=[0.6, 0.2, 0.1, 0.1],
            )[0]
            hours = {
                "DAY": rng.choice([8, 9, 10]),
                "EVENING": rng.choice([6, 8]),
                "NIGHT": rng.choice([8, 10, 12]),
                "CALL": rng.choice([12, 24]),
            }[shift_type]
            on_call = "Y" if shift_type == "CALL" else "N"

            row = {
                "provider_id": pid,
                "shift_date": shift_dt.strftime("%Y-%m-%d"),
                "shift_type": shift_type,
                "hours_worked": hours,
                "on_call": on_call,
            }
            if dirt:
                if rng.random() < 0.05:
                    row["provider_id"] = pid + " "
                if rng.random() < 0.08:
                    row["shift_date"] = shift_dt.strftime("%m/%d/%Y")
                if rng.random() < 0.05:
                    row["on_call"] = "1" if on_call == "Y" else "0"
            rows.append(row)

    if dirt:
        rows.append({
            "provider_id": "PROV099",
            "shift_date": (start + timedelta(days=2)).strftime("%Y-%m-%d"),
            "shift_type": "DAY",
            "hours_worked": 8,
            "on_call": "N",
        })
        rows.append({
            "provider_id": rng.choice(providers),
            "shift_date": (start + timedelta(days=3)).strftime("%Y-%m-%d"),
            "shift_type": "DAY",
            "hours_worked": -8,
            "on_call": "N",
        })

    rng.shuffle(rows)
    return pd.DataFrame(rows)


def write_timesheet_xlsx(df, path, sheet_name="Week"):
    df.to_excel(path, sheet_name=sheet_name, index=False)
