# Metric definitions

Rules that apply to every metric:
- **Null is not zero** for measurements: an absent OWID value stays null; population is never imputed.
- **Exception, verified on the 2026-11-05 Ember file:** a missing *generating-source row* (e.g. no Nuclear row) means zero generation. In 1,216 of 5,916 country-years at least one of the nine source rows is absent, and in every one the other sources add up to Ember's published total (0 mismatches over 0.05 TWh). Treating absence as null would have blanked 20.6% of country-years, so the models sum missing source rows as 0 TWh.
- **A year is complete (`is_complete_year`)** when Ember published a total and the nine sources (missing = 0) reconcile to it within 0.05 TWh. Percentages use the published total as denominator and are NULL unless the year is complete.
- TWh (energy) and GW (power) are only combined through the capacity-factor formula.
- Never derive World/region values by summing countries (Ember's World ≠ Σ countries: 2023 = 29,788.6 vs 29,683.2 TWh).
- Latest years (2024, 2025) are Ember estimates, and 2025 covers only 94 countries; marts carry `is_complete_year` and `coverage_note`.
- Economy-wide CO₂ (OWID, combustion, territorial) and power-sector emissions (Ember, **lifecycle**) are different quantities and have different column names.

| Metric | Formula | Source fields | Unit | Grain | Limitations |
|---|---|---|---|---|---|
| Total generation | Σ base generating sources; reconciled to Ember's published `Total generation` | Generation (TWh) | TWh | country-year | Excludes imports; gross/net mixed by source |
| Renewable generation | Hydro + Wind + Solar + Bioenergy + Other renewables | Generation | TWh | country-year | Bioenergy counted renewable (Ember's convention) |
| Renewable share | renewable_twh / total_generation_twh | | % of generation | country-year | Not share of consumption; a net importer's consumption share differs |
| Fossil share | (Coal + Gas + Other fossil) / total | | % of generation | country-year | |
| Solar / wind / hydro growth | abs = x_t − x_{t−1}; rel = abs / x_{t−1} | Generation | TWh; % | country-year(-source) | Rel. null if previous null/0; always show abs beside rel (low bases) |
| Renewable installed capacity | Σ renewable-source capacity | Capacity (GW) | GW | country-year | Nameplate; solar AC/DC mixed; timing within year not stated |
| Capacity factor | generation_twh × 1000 / (capacity_gw × hours) ; hours = 8760 (8784 leap) | Generation, Capacity | ratio | country-year-source | Nameplate basis; capacity growth within a year biases low; unreliable for Other fossil |
| Generation per capita | generation_twh × 1e9 / population (kWh/person) | Generation + OWID population | kWh | country-year | No imputation; population vintage differs from Ember |
| YoY generation growth | (g_t − g_{t−1}) / g_{t−1} | Generation | % | country-year | Null if previous null/0 or non-consecutive; coverage breaks look like growth |
| National CO₂ per capita | OWID `co2_per_capita` | OWID | t/person | country-year | Economy-wide, territorial, excl. land use |
| Power-sector carbon intensity | Ember `Emissions intensity (gCO2e/kWh)` on the `Total generation` row | Ember | gCO₂e/kWh | country-year | Lifecycle basis; relies on fixed regional/2017–2020 factors |
| Change in fossil dependence | fossil_share_end − fossil_share_start | | percentage points | country-window | Both endpoints complete years; endpoint sensitivity (2020, hydrology) |
| Decoupling flag | GDP growth > 0 and national CO₂ change < 0 over the window | OWID gdp, co2 | boolean + both % | country-window | Associational only; GDP ends 2022 (2011 intl-$) |
| Transition ranking | Rank by pp change in renewable share, with a minimum generation size in the start year | | rank | country-window | Size threshold is a parameter (`dbt var`), chosen to stop micro-grids dominating; justify when set |

Inference label: every mart/dashboard page is tagged **descriptive** (levels, shares, growth) or **associational** (correlation, decoupling). No claim of causation.
