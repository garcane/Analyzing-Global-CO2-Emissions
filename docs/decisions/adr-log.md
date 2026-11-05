# Architecture decision log

Status: Accepted unless stated. Date: 2026-11-05.

1. **Ember CSV is the primary load; the API is a second extractor.** CSV has yearly capacity for every source; the API (free key, emailed) has no yearly capacity endpoint. Its generation endpoint returns the same 17 series as the CSV, including `Demand` and `Net imports`. API data lands in separate RAW tables. Verified 2026-11-05: all 94,366 API generation rows (2000–2025) have a CSV counterpart and agree within 0.01 TWh (the API rounds to 2 decimals).
2. **Snapshot-per-release, not incremental loading.** Sources revise history and have no change key. Same file hash = no-op; a new hash appends a new `_load_id`; staging reads the latest successful load.
3. **RAW lands all columns as VARCHAR plus load metadata**; typing happens in dbt staging (`try_cast`), so bad values fail tests instead of failing the load.
4. **ISO-3 is the country key.** Aggregates live in the same geography dimension with `is_country = false`. No regex name filtering (the legacy notebook's defect).
5. **No imputation** of missing values.
6. **Fact tables:** `fct_generation_by_source` (country × year × source), `fct_electricity_balance` (country × year), `fct_country_economy_emissions` (country × year). Facts are combined only at country-year after aggregating the source-grain fact.
7. **Key-pair authentication is the default; browser login is an opt-in for local development** (`SNOWFLAKE_AUTHENTICATOR=externalbrowser`). Least-privilege roles (`GEI_LOADER`, `GEI_TRANSFORMER`, `GEI_REPORTER`); the loader refuses administrator roles in both modes; browser auth is never used in automation (it cannot run unattended).
8. **`uv` + `pyproject.toml` is the only dependency manifest** (`requirements.txt` retired: UTF-16, Windows-only pin). Python 3.13 (owner decision; 3.15 support in dbt/Snowflake packages unconfirmed).
9. **OWID Energy deferred.** Provenance of its electricity columns unverified; may not be independent of Ember.
10. **No orchestrator** until the manual pipeline is stable.
11. **Dropped models:** `dim_date`, separate `fct_renewable_capacity` (same grain as generation), `mart_electricity_mix` and `mart_emissions_intensity` (folded into the profile mart).
12. **Large CSVs stay committed in `data/`** (owner decision). Each Ember refresh adds ~16 MB to git history.
13. **BI tool: Power BI.** Snowflake is a trial account: XS warehouse, auto-suspend 60 s, resource monitor.
14. **Project-specific databases `GEI_RAW` and `GEI_ANALYTICS`** (names in `GEI_RAW_DATABASE` / `GEI_ANALYTICS_DATABASE`), separate from the tutorial data in `RAW` / `ANALYTICS`. The v1 setup granted `GEI_TRANSFORMER` access to tutorial schemas (`JAFFLE_SHOP`, `STRIPE`, `DBT_GARCANE`); v2 revokes that and scopes every grant to the new databases. The loader ignores a stale `SNOWFLAKE_DATABASE`.
15. **A missing Ember source row means zero generation; completeness is judged by reconciliation** with Ember's published total, not by row presence (see metrics.md for the measurement).
16. **dbt uses no external packages** (generic tests `accepted_range` and `unique_combination_of_columns` live in `dbt/macros/`), so `dbt deps` is not needed. dbt runs through `dbt/run_dbt.py`, which loads `.env` and uses the OS certificate store.
17. **Schema naming:** the `prod` target writes the exact `STAGING` / `INTERMEDIATE` / `MARTS` schemas (so `GEI_REPORTER`'s grants on `MARTS` apply); `dev` and CI targets prefix them (`dbt_<name>_marts`). `dbt/profiles.yml` is committed because it contains only `env_var()` lookups.
18. **Staging reads only the latest successful load** (`from_latest_load` macro over `META.LATEST_SUCCESSFUL_LOAD`); older loads stay in RAW for revision diffs.
19. **CI is split in two.** `ci.yml` is offline (lint, tests, secret scan, `dbt parse`) and runs on every PR; `dbt-snowflake.yml` is manual, approval-gated and builds into a throwaway schema as a dedicated CI user (`GEI_CI_SVC`) with a dedicated role `GEI_CI` that has no privileges on the prod schemas (enforced by Snowflake, not by convention). Reason: CI that needs Snowflake dies with the trial and spends credits on every push.
20. **Reporting reads exported CSVs as well as Snowflake.** `python -m ingestion.export` writes the six reporting tables to `data/exports/` (read-only role `GEI_REPORTER_SVC`). Power BI imports the data (no DirectQuery), so the report and its inputs survive the trial.
21. **Two transition rankings** (percentage-point share change and absolute renewable growth). Ranking by share alone rewards grids whose total generation fell (2010-2022: the top four by share all shrank).
22. **No scheduler, no incremental models, no alerting** (see docs/operations.md).
