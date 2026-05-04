# Provider Hours Reconciliation

[![CI](https://github.com/aizaguirre3/provider-hours-reconciliation/actions/workflows/ci.yml/badge.svg)](https://github.com/aizaguirre3/provider-hours-reconciliation/actions/workflows/ci.yml)

A weekly Excel ↔ SQL ETL job for healthcare scheduling ops. Pulls a provider master from a sqlite database, ingests a (potentially messy) Excel timesheet upload, reconciles **contracted vs actual hours**, flags exceptions (underutilization, overtime, missing timesheet, unknown provider), and writes a stakeholder-ready multi-sheet Excel report. Designed to run headless on a cron schedule.

## Why this exists

Every clinic ops analyst's recurring Tuesday morning task: a vendor scheduling system (think QGenda, Symplr, Tangier) drops an Excel timesheet, somebody has to reconcile it against the provider master, find the overtime, find the gaps, and email a clean report to the department director. This script is that job, reproducibly.

## What it does

- **Pulls** active providers + department metadata from a sqlite database via real `.sql` queries
- **Ingests** an Excel timesheet upload (one sheet, one row per shift), normalizing whitespace, mixed date formats, Y/N flags, and numeric coercion
- **Reconciles** by provider: total actual hours, on-call hours, shift count, utilization %, variance vs contracted, estimated cost
- **Flags** exceptions per provider:
  - `missing_timesheet` — active provider with zero shifts
  - `underutilization` — actual < department's utilization target (typically 75–85%)
  - `overtime` — actual > 110% of contracted
- **Detects** unknown provider IDs that appear in the timesheet but not in the master
- **Drops** invalid rows (negative or null hours), counting them in the summary
- **Writes** a 5-sheet formatted Excel report: Summary, Provider Utilization, Exceptions, Department Rollup, Unknown Providers

## Quickstart

```bash
git clone https://github.com/aizaguirre3/provider-hours-reconciliation.git
cd provider-hours-reconciliation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

```bash
# Initialize the master DB from sql/schema.sql + sql/seed.sql
python -m cli.main init-db --db data/master.db

# Generate a synthetic sample timesheet (one week, ~50 shifts)
python -m cli.main generate-sample -o samples/timesheet_sample.xlsx

# Run the reconciliation; writes a 5-sheet Excel report
python -m cli.main run samples/timesheet_sample.xlsx \
    --db data/master.db \
    --report data/weekly_report.xlsx

# Run any of the SQL queries directly
python -m cli.main query active_providers   --db data/master.db
python -m cli.main query department_targets --db data/master.db
python -m cli.main query provider_master    --db data/master.db
```

## Architecture

```
provider-hours-reconciliation/
├── etl/
│   ├── sources.py     # init_db, load_provider_master, load_timesheet, run_query
│   ├── reconcile.py   # join, compute metrics, flag exceptions
│   ├── report.py      # write 5-sheet formatted Excel
│   └── generator.py   # synthesize a sample timesheet for the demo
├── sql/
│   ├── schema.sql     # CREATE TABLE for departments + providers
│   ├── seed.sql       # 8 departments, 14 providers (1 inactive)
│   └── queries/
│       ├── provider_master.sql
│       ├── active_providers.sql
│       └── department_targets.sql
├── cli/main.py        # init-db / generate-sample / run / query
├── scheduler/         # cron.example for headless automation
├── tests/             # 24 unit tests
└── .github/workflows/ # CI: pytest on Python 3.11 and 3.12
```

## Data model

**Provider master (sqlite — persistent):**

| table | columns |
|---|---|
| `departments` | `department_code` (PK), `department_name`, `utilization_target` |
| `providers`   | `provider_id` (PK), `npi`, `last_name`, `first_name`, `credentials`, `department_code` (FK), `contracted_hours_per_week`, `hourly_rate`, `active` |

**Timesheet input (Excel — vendor-supplied):**

| column | notes |
|---|---|
| `provider_id` | matched against the master; whitespace tolerated |
| `shift_date` | mixed formats handled (ISO, US, etc.) |
| `shift_type` | DAY / EVENING / NIGHT / CALL |
| `hours_worked` | numeric; negative or null rows are dropped + counted |
| `on_call` | accepts Y/N/yes/no/1/0/true/false |

## Sample run output

```
13 providers | actual 536.0h / contracted 468.0h | util 114.5% | exceptions: 9 | unknown: 1 | dropped rows: 1
```

The companion `weekly_report.xlsx` has 5 sheets:

1. **Summary** — total providers, contracted hours, actual hours, utilization, estimated cost, exception counts, dropped rows
2. **Provider Utilization** — one row per active provider with all metrics + exception flags
3. **Exceptions** — filtered to providers with at least one flag set, for fast triage
4. **Department Rollup** — aggregated by department, with rollup utilization %
5. **Unknown Providers** — provider IDs that appeared in the timesheet but not in the master

## Automation

This is built to run unattended. See [`scheduler/cron.example`](scheduler/cron.example) for a sample crontab line that runs every Tuesday at 7am, picks up the prior week's timesheet by date convention, and writes a dated report.

## Development

```bash
.venv/bin/pytest -q
```

Tests run on Python 3.11 and 3.12 in CI on every push.

## License

MIT
