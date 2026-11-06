# Exported data dictionary

This dictionary covers the six CSV outputs in `data/exports/` used by the Power BI model. It describes the
checked-in export schema; refreshes can add data rows without changing these fields. Source provenance and
calculation rules are documented in [data_sources.md](data_sources.md) and
[business_logic/metrics.md](business_logic/metrics.md).

## Conventions

- `geography_key` and `source_key` are text identifiers. `year`, `start_year`, and `end_year` are whole years,
  not dates.
- `_twh`, `_gw`, `_mtco2e`, `_gco2e_kwh`, `_t`, and `_kwh` suffixes identify units: terawatt-hours, gigawatts,
  million metric tons CO₂ equivalent, grams CO₂ equivalent per kilowatt-hour, metric tons per person, and
  kilowatt-hours per person.
- Fields ending in `_pct` store percentage points on a 0–100 scale unless the field is a change explicitly
  expressed in percentage points (`_pp`). Do not format percentage-point changes as ratios.
- Missing measurements remain null. A missing generating-source row is treated as zero only for the documented
  source-sum/reconciliation logic.
- Geography dimensions include countries and aggregate geographies. Use Ember's `REG_WORLD` record for world
  figures rather than summing country rows.

## `dim_geography.csv`

**Grain:** one row per country or aggregate geography. **Key:** `geography_key`.

| Field | Type / unit | Meaning |
|---|---|---|
| `geography_key` | Text, key | Stable geography identifier; includes provider/canonical codes and region keys. |
| `geography_name` | Text | Display name of the geography. |
| `entity_type` | Text | Classification of the row, such as a country or an aggregate region. |
| `continent` | Text | Continent assignment when available. |
| `is_country` | Boolean | True for country rows; false for aggregate geographies. |

## `dim_energy_source.csv`

**Grain:** one row per Ember electricity source label. **Key:** `source_key`.

| Field | Type / unit | Meaning |
|---|---|---|
| `source_key` | Text, key | Canonical source identifier. |
| `source_name` | Text | Human-readable source label. |
| `category` | Text | Grouping used in report visuals (for example fossil, renewable, or other). |
| `is_aggregate` | Boolean | Marks an aggregate/summary series rather than a base generation source. |
| `is_renewable` | Boolean | Whether Ember classifies the source as renewable. |
| `is_low_carbon` | Boolean | Whether the source is classified as low-carbon. |
| `is_generation` | Boolean | Whether the source is a generation series used by generation analysis. |

## `fct_generation_by_source.csv`

**Grain:** geography × year × source. **Keys:** (`geography_key`, `year`, `source_key`).

| Field | Type / unit | Meaning |
|---|---|---|
| `geography_key` | Text, foreign key | Geography represented by the record. |
| `year` | Whole year | Reporting year. |
| `source_key` | Text, foreign key | Electricity source represented by the record. |
| `generation_twh` | TWh | Electricity generation for the source. |
| `capacity_gw` | GW | Installed nameplate capacity where reported. |
| `power_emissions_mtco2e` | Mt CO₂e | Ember power-sector lifecycle emissions attributed to the record. |

## `mart_country_energy_profile.csv`

**Grain:** country × year. **Key:** (`geography_key`, `year`).

| Field | Type / unit | Meaning |
|---|---|---|
| `geography_key` | Text, foreign key | Country identifier. |
| `country_name` | Text | Country display name. |
| `continent` | Text | Continent assignment. |
| `year` | Whole year | Reporting year. |
| `total_generation_twh` | TWh | Ember's published total generation. |
| `total_generation_recomputed_twh` | TWh | Recomputed total from the base generating sources. |
| `is_complete_year` | Boolean | True when the published total and recomputed sources reconcile within the model tolerance. |
| `renewables_twh` | TWh | Renewable-source generation. |
| `fossil_twh` | TWh | Fossil-source generation. |
| `nuclear_twh` | TWh | Nuclear generation. |
| `solar_twh` | TWh | Solar generation. |
| `wind_twh` | TWh | Wind generation. |
| `hydro_twh` | TWh | Hydro generation. |
| `bioenergy_twh` | TWh | Bioenergy generation. |
| `coal_twh` | TWh | Coal generation. |
| `gas_twh` | TWh | Gas generation. |
| `demand_twh` | TWh | Electricity demand, which may differ from generation due to net imports. |
| `net_imports_twh` | TWh | Net electricity imports; positive/negative direction follows the source convention. |
| `renewables_capacity_gw` | GW | Installed renewable nameplate capacity. |
| `power_emissions_mtco2e` | Mt CO₂e | Ember lifecycle power-sector emissions. |
| `power_carbon_intensity_gco2e_kwh` | g CO₂e/kWh | Ember power-sector lifecycle emissions intensity. |
| `population` | People | OWID population value; not imputed. |
| `gdp_intl_dollar_2011` | 2011 international dollars | OWID GDP at 2011 prices; coverage ends in 2022 in the source vintage. |
| `national_co2_mt` | Mt CO₂ | OWID territorial, economy-wide CO₂, excluding land use. |
| `national_co2_per_capita_t` | t/person | OWID national CO₂ per capita. |
| `primary_energy_twh` | TWh | OWID primary energy consumption. |
| `has_economy_row` | Boolean | Indicates a matched economy/emissions observation. |
| `renewable_share_pct` | Percent of generation (0–100) | Renewable generation divided by the published total. |
| `fossil_share_pct` | Percent of generation (0–100) | Fossil generation divided by the published total. |
| `nuclear_share_pct` | Percent of generation (0–100) | Nuclear generation divided by the published total. |
| `wind_solar_share_pct` | Percent of generation (0–100) | Wind plus solar generation divided by the published total. |
| `coal_share_pct` | Percent of generation (0–100) | Coal generation divided by the published total. |
| `gas_share_pct` | Percent of generation (0–100) | Gas generation divided by the published total. |
| `generation_per_capita_kwh` | kWh/person | Generation divided by OWID population. |

Shares are null when the year is not complete. They are shares of generation, not consumption.

## `mart_renewable_growth.csv`

**Grain:** country × year × renewable series. **Key:** (`geography_key`, `year`, `series`).

| Field | Type / unit | Meaning |
|---|---|---|
| `geography_key` | Text, foreign key | Country identifier. |
| `country_name` | Text | Country display name. |
| `continent` | Text | Continent assignment. |
| `year` | Whole year | Reporting year. |
| `series` | Text | Renewable technology/source series (such as solar, wind, hydro, or renewables). |
| `generation_twh` | TWh | Generation for the series. |
| `capacity_gw` | GW | Installed nameplate capacity for the series. |
| `yoy_change_twh` | TWh | Absolute generation change from the prior year. |
| `yoy_change_pct` | Percent | Relative generation change from the prior year; null if a valid prior base is unavailable. |
| `capacity_factor` | Ratio (0–1 expected) | Generation divided by nameplate capacity and hours in the year; low-capacity placeholders may be excluded. |

## `mart_energy_transition.csv`

**Grain:** country over the fixed 2010–2022 comparison window. **Key:** `geography_key`.

| Field | Type / unit | Meaning |
|---|---|---|
| `geography_key` | Text, foreign key | Country identifier. |
| `country_name` | Text | Country display name. |
| `continent` | Text | Continent assignment. |
| `start_year` | Whole year | Start of the comparison window (2010). |
| `end_year` | Whole year | End of the comparison window (2022). |
| `start_generation_twh` | TWh | Total generation at the start endpoint. |
| `end_generation_twh` | TWh | Total generation at the end endpoint. |
| `start_renewable_share_pct` | Percent (0–100) | Renewable generation share at the start endpoint. |
| `end_renewable_share_pct` | Percent (0–100) | Renewable generation share at the end endpoint. |
| `renewable_share_change_pp` | Percentage points | End renewable share minus start renewable share. |
| `total_generation_change_twh` | TWh | Change in total generation across endpoints. |
| `renewables_change_twh` | TWh | Change in renewable generation across endpoints. |
| `fossil_share_change_pp` | Percentage points | Change in fossil generation share. |
| `coal_share_change_pp` | Percentage points | Change in coal generation share. |
| `gas_share_change_pp` | Percentage points | Change in gas generation share. |
| `carbon_intensity_change_gco2e_kwh` | g CO₂e/kWh | Change in Ember power-sector carbon intensity. |
| `gdp_growth_pct` | Percent | OWID GDP growth over the endpoints. |
| `national_co2_change_pct` | Percent | OWID national CO₂ change over the endpoints. |
| `is_economy_co2_decoupled` | Boolean | True when GDP rose and national CO₂ fell; associational classification only. |
| `is_eligible` | Boolean | True when the country meets the transition-comparison inclusion rules. |
| `renewable_share_change_rank` | Whole number, rank | Rank by renewable-share change, subject to eligibility rules. |
| `renewables_growth_twh_rank` | Whole number, rank | Rank by absolute renewable-generation growth. |

## Related documentation

- [Metric definitions](business_logic/metrics.md)
- [Power BI model and relationship rules](powerbi/model.md)
- [Expected report checks](powerbi/report_spec.md)
- [Source coverage and caveats](data_sources.md)
