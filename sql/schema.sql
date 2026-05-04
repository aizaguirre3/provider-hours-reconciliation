-- Provider master schema (sqlite-compatible).

CREATE TABLE IF NOT EXISTS departments (
  department_code      TEXT PRIMARY KEY,
  department_name      TEXT NOT NULL,
  utilization_target   REAL NOT NULL DEFAULT 0.85
);

CREATE TABLE IF NOT EXISTS providers (
  provider_id                TEXT PRIMARY KEY,
  npi                        TEXT NOT NULL UNIQUE,
  last_name                  TEXT NOT NULL,
  first_name                 TEXT NOT NULL,
  credentials                TEXT NOT NULL,
  department_code            TEXT NOT NULL REFERENCES departments(department_code),
  contracted_hours_per_week  REAL NOT NULL,
  hourly_rate                REAL NOT NULL,
  active                     INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_providers_dept ON providers(department_code);
CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(active);
