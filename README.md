# Global Energy Intelligence Pipeline

How is electricity generation changing across countries, what is driving renewable growth, and how does the energy transition relate to national CO₂ emissions and economic development?

This repository evolves an exploratory CO₂ notebook into a reproducible pipeline:

```
Ember (CSV + API) ─┐
OWID CO₂ (CSV) ────┼─> Python ingestion ─> Snowflake RAW ─> dbt staging ─> intermediate ─> marts ─> Power BI
ISO reference ─────┘
```

**Status:** Phase 1 (scope, reference data, environment) done. Phase 2 done: the Ember CSV, Ember API and OWID CO₂ data are loaded into Snowflake `RAW` and reconciled (see [docs/snowflake_setup.md](docs/snowflake_setup.md)). dbt models, CI and the dashboard are not built yet.

## Data

| Source | Role | Details |
|---|---|---|
| [Ember Yearly Electricity Data](https://ember-energy.org/data/yearly-electricity-data/) | Generation, capacity, demand, net imports, power-sector emissions | CC-BY-4.0 |
| [OWID CO₂ and GHG emissions](https://github.com/owid/co2-data) | Economy-wide CO₂, population, GDP, primary energy | CC BY 4.0 (third-party terms apply) |
| `data/reference/` | ISO-3 country and energy-source reference tables | maintained here |

Verified source facts, units and caveats: [docs/data_sources.md](docs/data_sources.md). Metric definitions: [docs/business_logic/metrics.md](docs/business_logic/metrics.md). Design decisions: [docs/decisions/adr-log.md](docs/decisions/adr-log.md).

Two things to keep in mind when reading results: Ember's latest years are estimates (2025 covers only 94 countries), and Ember's power-sector emissions are lifecycle figures, not comparable with OWID's combustion CO₂. Results are descriptive or associational; nothing here claims causation.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13.

```bash
uv sync
cp .env.example .env     # then fill in; never commit .env
uv run dbt --version
```

## Layout

```
data/                CSV sources (committed) and data/reference/ seeds
notebooks/legacy/    original exploratory notebook, kept unchanged (see its README for known defects)
docs/                data sources, metric definitions, decision log
ingestion/           Python extract / validate / load
dbt/                 dbt project: staging -> intermediate -> marts (run via dbt/run_dbt.py)
infra/               Snowflake one-time setup SQL (run manually)
tests/unit/          pytest, no Snowflake needed
```

Run the tests: `uv run pytest`. Validate a source without Snowflake: `uv run python -m ingestion.cli ember_yearly_csv --dry-run`.
