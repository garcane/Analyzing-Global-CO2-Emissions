"""Source definitions: where each dataset comes from and which RAW table it lands in."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ingestion.schemas import EMBER_YEARLY_COLUMNS, OWID_CO2_COLUMNS


def raw_column_name(source_column: str) -> str:
    """'Generation (TWh)' -> 'generation_twh'. Deterministic, snake_case, Snowflake-safe."""
    name = re.sub(r"[^0-9a-zA-Z]+", "_", source_column).strip("_").lower()
    return name or "col"


@dataclass(frozen=True)
class SourceSpec:
    name: str                 # log key, e.g. 'ember_yearly_csv'
    schema: str               # RAW schema
    table: str                # RAW table
    columns: list[str]        # exact expected CSV header
    filename: str             # file name under data/ (or data/api/)
    url: str | None = None    # None for API-derived files
    year_column: str | None = None
    year_min: int = 1700
    year_max: int = 2100
    key_columns: tuple[str, ...] = ()   # must be non-null on every row

    @property
    def raw_columns(self) -> list[str]:
        return [raw_column_name(c) for c in self.columns]

    @property
    def fqn(self) -> str:
        return f"{self.schema}.{self.table}"


EMBER_YEARLY_CSV = SourceSpec(
    name="ember_yearly_csv",
    schema="EMBER",
    table="GENERATION_YEARLY",
    columns=EMBER_YEARLY_COLUMNS,
    filename="release_generation_yearly_global.csv",
    url="https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv",
    year_column="Year",
    year_min=1985,
    key_columns=("Area", "Year", "Area type", "Electricity source"),
)

OWID_CO2_CSV = SourceSpec(
    name="owid_co2_csv",
    schema="OWID",
    table="CO2",
    columns=OWID_CO2_COLUMNS,
    filename="owid-co2-data.csv",
    url="https://owid-public.owid.io/data/co2/owid-co2-data.csv",
    year_column="year",
    year_min=1700,
    key_columns=("country", "year"),
)

# Ember API (OpenAPI spec read 2026-11-05). Response rows are flattened to these columns.
EMBER_API_BASE = "https://api.ember-energy.org/v1"

_API_COMMON = ["entity", "entity_code", "is_aggregate_entity", "date"]

EMBER_API_GENERATION = SourceSpec(
    name="ember_api_generation",
    schema="EMBER",
    table="API_GENERATION_YEARLY",
    columns=_API_COMMON + ["series", "is_aggregate_series", "generation_twh", "share_of_generation_pct"],
    filename="ember_api_generation_yearly.csv",
    year_column="date",
    year_min=1985,
    key_columns=("entity", "date", "series"),
)
EMBER_API_DEMAND = SourceSpec(
    name="ember_api_demand",
    schema="EMBER",
    table="API_DEMAND_YEARLY",
    columns=_API_COMMON + ["demand_twh", "demand_kwh_per_capita"],
    filename="ember_api_demand_yearly.csv",
    year_column="date",
    year_min=1985,
    key_columns=("entity", "date"),
)
EMBER_API_EMISSIONS = SourceSpec(
    name="ember_api_emissions",
    schema="EMBER",
    table="API_EMISSIONS_YEARLY",
    columns=_API_COMMON + ["series", "is_aggregate_series", "emissions_mtco2", "share_of_emissions_pct"],
    filename="ember_api_emissions_yearly.csv",
    year_column="date",
    year_min=1985,
    key_columns=("entity", "date", "series"),
)

# (spec, endpoint path)
EMBER_API_ENDPOINTS = [
    (EMBER_API_GENERATION, "/electricity-generation/yearly"),
    (EMBER_API_DEMAND, "/electricity-demand/yearly"),
    (EMBER_API_EMISSIONS, "/power-sector-emissions/yearly"),
]

SOURCES = {
    s.name: s
    for s in (
        EMBER_YEARLY_CSV,
        OWID_CO2_CSV,
        EMBER_API_GENERATION,
        EMBER_API_DEMAND,
        EMBER_API_EMISSIONS,
    )
}
