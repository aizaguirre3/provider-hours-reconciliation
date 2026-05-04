"""Reconcile a timesheet against the provider master and produce metrics + flags."""
import pandas as pd


OVERTIME_THRESHOLD = 1.10  # >110% of contracted hours


def reconcile(timesheet_df, master_df):
    """Reconcile a timesheet DataFrame against the active provider master.

    timesheet_df columns expected: provider_id, shift_date, shift_type,
        hours_worked (numeric), on_call (bool).
    master_df columns expected: provider_id, npi, last_name, first_name,
        credentials, department_code, department_name, utilization_target,
        contracted_hours_per_week, hourly_rate.

    Returns a dict:
        utilization (DataFrame): one row per master provider, with metrics + exceptions.
        unknown_providers (DataFrame): provider_ids in the timesheet not in master.
        department_rollup (DataFrame): aggregates by department.
        summary (dict): top-level KPIs.
        dropped_rows (int): timesheet rows ignored (negative or null hours).
    """
    ts = timesheet_df.copy()
    pre_n = len(ts)
    ts = ts[(ts["hours_worked"].notna()) & (ts["hours_worked"] > 0)]
    dropped_rows = pre_n - len(ts)

    if "on_call" not in ts.columns:
        ts["on_call"] = False

    if len(ts) == 0:
        agg = pd.DataFrame(columns=["provider_id", "actual_hours", "shift_count", "on_call_hours"])
    else:
        total_agg = ts.groupby("provider_id").agg(
            actual_hours=("hours_worked", "sum"),
            shift_count=("hours_worked", "count"),
        )
        on_call_agg = (
            ts[ts["on_call"]]
            .groupby("provider_id")["hours_worked"]
            .sum()
            .rename("on_call_hours")
        )
        agg = total_agg.merge(on_call_agg, left_index=True, right_index=True, how="left").reset_index()
        agg["on_call_hours"] = agg["on_call_hours"].fillna(0.0)

    master_ids = set(master_df["provider_id"])
    unknown_mask = ~agg["provider_id"].isin(master_ids)
    unknown_providers = agg[unknown_mask].reset_index(drop=True)

    util = master_df.merge(agg, on="provider_id", how="left")
    util["actual_hours"] = util["actual_hours"].fillna(0.0)
    util["on_call_hours"] = util["on_call_hours"].fillna(0.0)
    util["shift_count"] = util["shift_count"].fillna(0).astype(int)
    util["utilization_pct"] = (util["actual_hours"] / util["contracted_hours_per_week"]).round(3)
    util["variance_hours"] = (util["actual_hours"] - util["contracted_hours_per_week"]).round(2)
    util["estimated_cost"] = (util["actual_hours"] * util["hourly_rate"]).round(2)

    def _flags(row):
        flags = []
        if row["shift_count"] == 0:
            flags.append("missing_timesheet")
        elif row["utilization_pct"] < row["utilization_target"]:
            flags.append("underutilization")
        if row["utilization_pct"] > OVERTIME_THRESHOLD:
            flags.append("overtime")
        return ", ".join(flags)

    util["exceptions"] = util.apply(_flags, axis=1)

    dept_rollup = (
        util.groupby(["department_code", "department_name"])
        .agg(
            n_providers=("provider_id", "count"),
            contracted_hours=("contracted_hours_per_week", "sum"),
            actual_hours=("actual_hours", "sum"),
            estimated_cost=("estimated_cost", "sum"),
        )
        .reset_index()
    )
    dept_rollup["utilization_pct"] = (
        dept_rollup["actual_hours"] / dept_rollup["contracted_hours"]
    ).round(3)

    total_contracted = float(util["contracted_hours_per_week"].sum())
    total_actual = float(util["actual_hours"].sum())
    summary = {
        "total_providers": int(len(util)),
        "total_contracted_hours": total_contracted,
        "total_actual_hours": total_actual,
        "overall_utilization_pct": round(total_actual / total_contracted, 3) if total_contracted else 0.0,
        "total_estimated_cost": round(float(util["estimated_cost"].sum()), 2),
        "n_with_exceptions": int((util["exceptions"] != "").sum()),
        "n_unknown_providers": int(len(unknown_providers)),
        "dropped_rows": int(dropped_rows),
    }

    return {
        "utilization": util,
        "unknown_providers": unknown_providers,
        "department_rollup": dept_rollup,
        "summary": summary,
        "dropped_rows": dropped_rows,
    }
