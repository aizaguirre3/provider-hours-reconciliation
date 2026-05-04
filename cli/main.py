"""CLI: init-db, generate-sample, run, validate."""
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.sources import init_db, load_provider_master, load_timesheet, run_query
from etl.reconcile import reconcile
from etl.report import write_report
from etl.generator import generate_timesheet, write_timesheet_xlsx


@click.group()
def cli():
    """Provider Hours Reconciliation — weekly Excel ↔ SQL ETL."""


@cli.command("init-db")
@click.option("--db", "db_path", type=click.Path(dir_okay=False), default="data/master.db")
def init_db_cmd(db_path):
    """Initialize the sqlite provider master DB from schema.sql + seed.sql."""
    init_db(db_path)
    click.echo(f"Initialized DB at {db_path}")


@cli.command("generate-sample")
@click.option("--week-start", default="2025-11-03", help="ISO date of Monday for the sample week.")
@click.option("--seed", type=int, default=42)
@click.option("--output", "-o", type=click.Path(dir_okay=False), default="samples/timesheet_sample.xlsx")
def generate_sample_cmd(week_start, seed, output):
    """Generate a synthetic Excel timesheet for one week."""
    df = generate_timesheet(week_start=week_start, seed=seed)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    write_timesheet_xlsx(df, output)
    click.echo(f"Wrote {len(df)} rows to {output}")


@cli.command()
@click.argument("timesheet", type=click.Path(exists=True, dir_okay=False))
@click.option("--db", "db_path", type=click.Path(exists=True, dir_okay=False), default="data/master.db")
@click.option("--report", "-o", "report_path", type=click.Path(dir_okay=False), default="data/weekly_report.xlsx")
def run(timesheet, db_path, report_path):
    """Reconcile a timesheet against the provider master and write the weekly Excel report."""
    master = load_provider_master(db_path)
    ts = load_timesheet(timesheet)
    result = reconcile(ts, master)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    write_report(result, report_path)
    s = result["summary"]
    click.echo(
        f"{s['total_providers']} providers | "
        f"actual {s['total_actual_hours']:.1f}h / contracted {s['total_contracted_hours']:.1f}h | "
        f"util {s['overall_utilization_pct']*100:.1f}% | "
        f"exceptions: {s['n_with_exceptions']} | "
        f"unknown: {s['n_unknown_providers']} | "
        f"dropped rows: {s['dropped_rows']}"
    )
    click.echo(f"Report written to {report_path}")


@cli.command()
@click.argument("query_name")
@click.option("--db", "db_path", type=click.Path(exists=True, dir_okay=False), default="data/master.db")
def query(query_name, db_path):
    """Run a named .sql file from sql/queries/ and print results."""
    df = run_query(db_path, query_name)
    click.echo(df.to_string(index=False))


if __name__ == "__main__":
    cli()
