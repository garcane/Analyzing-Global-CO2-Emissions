# Report specification

Audience: someone judging whether the energy transition is real, where, and how it relates to emissions and
growth. Every page carries a one-line label: **Descriptive** (levels, shares, growth) or **Association** (two
things moved together; no causal claim). 2023 is the recommended latest complete year (2024-2025 are partial and
estimated); the year slicers expose all available years.

Year slicers on annual-analysis pages are bound directly to each visual's annual fact table. Transition leaders is
a fixed 2010-2022 comparison window, not annual-grain data. Country mix maps renewable share by country;
Transition leaders maps renewable-share change in percentage points for that window.

| Page | Business question(s) | Visuals | Label |
|---|---|---|---|
| 1. World overview | 1, 3 | Line: `World Renewable Share` and `World Generation TWh` by year (REG_WORLD). Stacked area: mix by `dim_energy_source[category]` for REG_WORLD. | Descriptive |
| 2. Country mix | 1, 3, 5 | Country + year slicers; stacked bar of generation by source; cards `Renewable Share`, `Fossil Share`; line of coal/gas share by year (`mart_country_energy_profile[coal_share_pct]`, `gas_share_pct`); per-capita generation. | Descriptive |
| 3. Renewable growth | 2, 4 | Table of `Renewables YoY TWh` by country for the selected year; small multiples for solar / wind / hydro; **capacity vs generation** scatter or paired columns (GW vs TWh) with `Capacity Factor` (single year). | Descriptive |
| 4. Transition leaders | 5, 9 | Two ranked bar charts side by side: by `renewable_share_change_pp` and by `renewables_change_twh`; table beside them with `Total Generation Change TWh`. `is_eligible` filter on. | Descriptive |
| 5. Emissions and economy | 6, 7, 8 | Scatter: GDP growth % vs economy-wide CO2 change % (`mart_energy_transition`), colour = `is_economy_co2_decoupled`; line: power carbon intensity by year; table of decoupled countries. | **Association** |
| 6. Data notes | all | Text only (below). | n/a |

Business questions (from the project brief): 1 evolution of generation; 2 greatest renewable growth; 3 fossil /
nuclear / renewable mix; 4 capacity turning into generation; 5 reducing coal and gas; 6 renewables vs national CO2;
7 GDP, population and energy vs generation; 8 growth with falling emissions intensity; 9 most progress.

## Page 4 reading guide (put on the page)
Share-of-generation gains can come from fossil generation **falling**. For 2010-2022 the top four countries by
share gain (Luxembourg, Lithuania, Denmark, Lebanon) all had lower total generation, with small absolute
renewable gains in most. Ranked by absolute renewable growth the leaders are China, the United States, India,
Brazil and Germany. Show both rankings and the total-generation change together.

## Page 6 text (data notes)
- Electricity data: Ember yearly data, CC-BY-4.0. Emissions/economy data: Our World in Data CO2 dataset, CC BY.
- 2024 covers 194 countries and 2025 only 94; Ember's latest years are estimates and are not flagged per value.
- A missing source row means zero generation for that source (verified: the sources still sum to Ember's total).
- Power-sector emissions (Ember) are lifecycle figures; national CO2 (OWID) is territorial combustion and industry.
  They are not comparable.
- Shares are shares of generation, not consumption; net importers' consumption mix differs.
- Capacity is nameplate; capacity factors for capacities under 0.15 GW are hidden (Ember placeholders).
- GDP (OWID, 2011 international dollars) ends in 2022, so the transition window is 2010-2022.
- "Decoupled" = GDP up and CO2 down over the window: an association, not evidence of cause.

## Checking the finished report
Compare these with the visuals (all computed from the exported marts on 2026-11-05):

| Check | Expected |
|---|---|
| United States 2023: total generation, renewable share, fossil share | 4,253.91 TWh, 22.7%, 59.1% |
| Germany 2023: total, renewable share | 506.72 TWh, 54.7% |
| China 2023: total, renewable share | 9,402.74 TWh, 30.0% |
| India 2023: total, renewable share | 1,916.85 TWh, 19.2% |
| Norway 2023: renewable share | 98.5% |
| Kosovo 2023 (XKX, joined to OWID by name): renewable share | 12.6% |
| World (REG_WORLD): total 2000 / 2015 / 2023 | 15,325.3 / 24,063.5 / 29,788.6 TWh |
| World renewable share 2000 / 2015 / 2023 | 18.7% / 22.9% / 30.0% |
| Countries with data: 2023 / 2024 / 2025 | 208 / 194 / 94 |
| Transition window: eligible countries; GDP up and CO2 down | 148 of 208; 48 |
| Top 5 by absolute renewable growth 2010-2022 | China 1,823.5; United States 533.7; India 221.3; Brazil 156.5; Germany 146.1 TWh |
| Largest solar year-on-year gain, 2023 | China +156.9 TWh; United States +33.9; Brazil +20.5 |

## The project
The model and the six pages above exist as a Power BI Project in `powerbi/GEI.pbip` (see `powerbi/README.md`
for how to open it and for what has and has not been verified). It was generated as text files and now opens in
Power BI Desktop (confirmed 2026-11-06). The numbers have **not yet been checked**: refresh and compare them
with the table above. The measures in
`measures.dax` are the same ones that are in the project's model.
Screenshots of the finished pages belong in `docs/img/` and the README.
