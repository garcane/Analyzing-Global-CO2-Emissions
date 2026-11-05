# Data sources (verified facts)

Verified = read from the provider's page/spec/PDF or observed in the local file. Checked 2026-11-05.

## Ember — Yearly Electricity Data (primary)

| | |
|---|---|
| Bulk CSV (global) | `https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv` |
| Licence | CC-BY-4.0 (Ember site footer and API spec). Attribute as "Ember – Yearly Electricity Data". Ember gives no fixed attribution string. |
| Cadence | Page says both "Updated monthly" and "twice a month" (inconsistent) |
| Local file | 104,256 rows × 24 columns; 1985–2025; 209 countries/economies + 15 regions; grain = area × year × electricity source |
| API | Base `https://api.ember-energy.org/v1`; key sent as `api_key` **query parameter**; no pagination; "no rate limiting at present". Yearly endpoints: `/electricity-generation/yearly`, `/electricity-demand/yearly`, `/carbon-intensity/yearly`, `/power-sector-emissions/yearly`. **No yearly capacity endpoint** (monthly wind/solar only, from 2016). Verified by live load: unfiltered requests work in one response (generation 94,366 rows, demand 5,676, emissions 94,366; 2000–2025); the generation endpoint returns the same 17 series as the CSV including `Demand` and `Net imports`, and matches the CSV within 0.01 TWh. |
| Methodology | "Ember Methodology v1.6" PDF: https://files.ember-energy.org/public-downloads/ember_electricity_data_methodology.pdf |

Methodology points that affect modelling (from the PDF):
- **Demand** = power production + net imports. **"% share" is share of generation**, not of consumption.
- Where net imports are unavailable for any year they are **assumed zero**; if generation exists for 2025 but imports do not, imports are **carried forward**.
- **Latest years are estimated**: missing annual data is projected from monthly data (ARIMA); world/regional totals for the latest year are estimated. Summing monthly values will not reproduce the annual values. The CSV has no estimate-flag column.
- Generation is **gross** where sources report gross, net where they report net (mixed).
- Hydro excludes pumped hydro where possible; Solar includes distributed PV where possible; Bioenergy is classed renewable by Ember with stated sustainability caveats; Other fossil includes oil, petroleum products, manufactured gases and waste.
- **Capacity** = maximum nameplate output. Solar is reported as a mix of AC and DC; capacity ratios for Other fossil are incorrect for some countries; GEM figures are gross while other sources are net. Year-end vs average timing is **not stated**.
- **Emissions** are full **lifecycle** (upstream methane, supply chain), all gases as CO₂e on a 100-year basis, from generation × factors (UNECE/IPCC AR5 etc.). Not comparable to OWID's combustion CO₂.

## OWID CO₂ and GHG emissions (existing dataset)

| | |
|---|---|
| Download | `https://owid-public.owid.io/data/co2/owid-co2-data.csv` (from the OWID co2-data README) |
| Licence | CC BY 4.0 for OWID-produced content; third-party data stays under its own licence terms; cite OWID and the underlying sources |
| Cadence | Annual, no fixed schedule; latest changelog entry 2026-06-01 (carbon-intensity units changed kg → g CO₂/kWh) |
| Local file | 50,191 rows × 79 columns; 1750–2023; 255 entities (218 ISO codes, 37 non-countries) |

Column units (OWID codebook): `co2` Mt (excl. land use, Global Carbon Budget); `co2_per_capita` t/person; `population` people; `gdp` international-$ in **2011 prices** (Maddison Project 2023; non-null only to 2022 in local file); `primary_energy_consumption` **TWh** (EIA + Energy Institute); `energy_per_capita` kWh/person; `consumption_co2` Mt.

## OWID Energy (deferred, not in MVP)
`data/owid_energy.csv` and `data/column_mapping_for_owid_energy.csv` are kept in the repo. Provenance of its electricity columns not yet verified; not loaded.
