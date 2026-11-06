# Operations runbook

## Refreshing the data (manual, about 5 minutes)
1. Re-download and load a source: `uv run python -m ingestion.cli ember_yearly_csv --download` (same for
   `owid_co2_csv`; `ember_api` fetches without `--download`). An identical file is skipped automatically.
2. Rebuild: `uv run python dbt/run_dbt.py build --target prod`, then `... source freshness`.
3. Re-export for Power BI: `uv run python -m ingestion.export`; commit the changed CSVs.
4. Read the warnings below; a blocking failure means do not publish.

## What blocks and what only warns
| Check | Result | Why |
|---|---|---|
| Header differs from `ingestion/schemas.py` | **blocks the load** | a provider format change must be reviewed, not absorbed |
| Row count or loaded rows differ from the file | **blocks, load is deleted** | a partial load must never become "latest" |
| Unique keys, not-null, relationships, accepted values | **blocks the build** | wrong joins or labels would silently change numbers |
| Renewables = sum of parts; nine sources = published total; every country mapped; no aggregates in country marts | **blocks the build** | these protect the headline metrics |
| Negative generation/capacity/emissions in the source-grain fact | **blocks** | physically implausible (Net imports excluded) |
| API differs from CSV beyond 0.01 TWh | warns | two publication channels can briefly disagree |
| Row count moves more than 5% between loads | warns | one new year adds about 3.3%; more suggests a structural change |
| Gaps inside a country's year series | warns | real, but they limit year-on-year charts |
| Capacity factor above 1.5 | warns | Ember capacity placeholders (all 16 rows have 0.11 GW or less) |
| Source freshness (45 days Ember, 400 days OWID) | warns | measures when WE last loaded, not when the provider published |

## Failure recovery
- A failed load deletes its own rows, is marked FAILED in `META.INGESTION_LOG`, and is never the "latest" load,
  so dbt keeps reading the previous good data. Fix the cause and run the load again.
- Superseded loads stay in RAW so a revision can be compared with `INGESTION_LOG` and the `_load_id` column.
- If a dbt build fails halfway, rerun it: models are tables/views rebuilt from RAW and have no state.

## Deliberately not built
- **No scheduler or orchestrator.** Sources change a few times a month at most, the manual refresh takes minutes,
  and an orchestrator would add infrastructure without a requirement (see ADR 10).
- **No incremental models.** About 100,000 rows rebuild in seconds; sources have no change key (ADR 2).
- **No alerting.** The warning table above is the monitoring; the loader log is the audit trail.

## CI
- `.github/workflows/ci.yml`: every pull request and push to `main` runs lint, unit tests (including the secret
  scan, the profile check and the RAW/staging column contract) and `dbt parse`. No Snowflake, no secrets.
- `.github/workflows/dbt-snowflake.yml`: manual only, behind the `snowflake-trial` environment (reviewer required).
  Builds and tests into a throwaway `dbt_ci_<run id>_*` schema and drops it afterwards. It signs in as
  `GEI_CI_SVC` with the `GEI_CI` role, which can read `GEI_RAW` and create its own schemas but has **no privilege on
  the prod `STAGING` / `INTERMEDIATE` / `MARTS` schemas**: Snowflake itself prevents it from writing prod.
  Needs the repository secrets `SNOWFLAKE_ACCOUNT`, `CI_SNOWFLAKE_USER` and `CI_SNOWFLAKE_PRIVATE_KEY`.

## GitHub settings only you can change
1. Settings > Code security: enable **secret scanning** and **push protection** (free on public repositories).
2. Settings > Environments > New environment `snowflake-trial`; add yourself as **required reviewer**.
3. In that environment add secrets: `SNOWFLAKE_ACCOUNT` (e.g. `GWEPWIG-CA86069`), `CI_SNOWFLAKE_USER`
   (`GEI_CI_SVC`) and `CI_SNOWFLAKE_PRIVATE_KEY` (the full contents of `~/.snowflake/gei_ci.p8`).
   Create the users first with the SQL from `infra/snowflake_setup.sql` section 6b.
4. Optionally protect `main` and require the `CI / checks` status to pass before merging.
Never paste a secret in an issue, a commit or a chat.

## When the Snowflake trial ends (about 1 December 2026)
What keeps working: the repository, all tests and CI (`ci.yml`), the committed source CSVs, the committed exports in
`data/exports/`, and a Power BI report built in Import mode. What stops: loading, dbt builds, the manual Snowflake
workflow and live refresh. Everything is rebuildable on a new Snowflake account from `infra/snowflake_setup.sql`,
the loader and dbt.
