# Power BI semantic model

Source tables are the six files in `data/exports/` (produced by `python -m ingestion.export` from the
production `GEI_ANALYTICS.MARTS` schema). The same six tables can be imported straight from Snowflake instead
(see "Connecting" below); the model is identical either way.

## Tables and relationships

```
dim_geography (geography_key) 1 ──< * fct_generation_by_source (geography_key)
dim_geography (geography_key) 1 ──< * mart_country_energy_profile (geography_key)
dim_geography (geography_key) 1 ──< * mart_renewable_growth (geography_key)
dim_geography (geography_key) 1 ──< * mart_energy_transition (geography_key)
dim_energy_source (source_key) 1 ──< * fct_generation_by_source (source_key)
```

All relationships single direction (dimension filters fact), no bi-directional filtering.

| Table | Grain | Use |
|---|---|---|
| `dim_geography` | one row per geography (229 countries, 15 regions incl. `REG_WORLD`) | slicers: country, continent; `is_country` filter |
| `dim_energy_source` | one row per Ember source label | `is_renewable`, `category` |
| `fct_generation_by_source` | geography x year x source | mix charts, World trend (includes regions) |
| `mart_country_energy_profile` | country x year | shares, per-capita, demand, emissions, GDP, CO2 |
| `mart_renewable_growth` | country x year x series | solar / wind / hydro / renewables growth, capacity factor |
| `mart_energy_transition` | country (window 2010-2022) | transition leaders, decoupling |

## Import settings (Power Query)
- `year`, `start_year`, `end_year` and all ranks: **Whole number**, never Date.
- Boolean columns (`is_country`, `is_complete_year`, `is_eligible`, `is_renewable`, ...): True/False.
- `*_pct` columns are already in percent units (0-100). Show them with format `0.0` and "%" in the title, or
  use the fraction measures in `measures.dax`, which are formatted as percentages.
- Hide key columns (`geography_key`, `source_key`) from the report view; slice by names.
- Empty cells are NULL (nothing was imputed). Do not replace blanks with 0.

## Rules that keep numbers correct
1. **Never average percentages across countries.** Compute shares from sums (see `measures.dax`).
2. **Never sum countries to get the World.** Use the `REG_WORLD` rows of `fct_generation_by_source` (Ember's own
   World figure; summing 2023 countries gives 29,683 TWh against Ember's 29,789 TWh).
3. Country pages filter `dim_geography[is_country] = TRUE`; the World page filters `REG_WORLD`.
4. 2024 has 194 countries and 2025 only 94 (partial and estimated): use year slicers at 2023 or earlier for complete coverage.
5. Power-sector emissions (Ember, lifecycle) and national CO2 (OWID, combustion) are different measures:
   label them separately and never put them on the same axis.

## Connecting
**CSV (guaranteed, works after the Snowflake trial ends):** Get data > Text/CSV, load the six files from
`data/exports/`, create the relationships above.

**Snowflake (Import mode, not DirectQuery):** Get data > Snowflake. Server `GWEPWIG-CA86069.snowflakecomputing.com`,
warehouse `GEI_WH`; under Advanced options set Role to `GEI_REPORTER`; database `GEI_ANALYTICS`, schema `MARTS`.
Sign in with your own Snowflake login; your user must have been granted `GEI_REPORTER` (the v3 setup script does
this; check with `USE ROLE GEI_REPORTER;` in Snowsight). Whether the Power BI connector supports the key-pair service user
(`GEI_REPORTER_SVC`) or your account's MFA password policy is **not verified**; if sign-in fails, use the CSV path.
Import mode caches the data inside the `.pbix`, so the report keeps working after the trial ends.
