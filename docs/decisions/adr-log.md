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
