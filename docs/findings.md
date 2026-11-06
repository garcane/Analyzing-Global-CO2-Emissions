# Findings summary

This summary captures the reference analysis calculated from the checked-in reporting exports on 2026-11-05.
Treat the values as a reproducible snapshot, not as live figures. Refresh the source data, rebuild the marts, and
recheck the dashboard before publishing a newer vintage. Detailed comparison values are in the
[Power BI report specification](powerbi/report_spec.md).

## What the data shows

### Electricity generation and renewables are both growing

Ember's reported World generation increased from **15,325.3 TWh in 2000** to **29,788.6 TWh in 2023**. The
World renewable share rose from **18.7% to 30.0%** across those years, an increase of **11.3 percentage points**.
The World values are Ember's own aggregate (`REG_WORLD`), not sums of country records.

### Renewable growth is concentrated in large electricity systems

Over 2010–2022, the largest absolute increases in renewable generation were in **China (1,823.5 TWh)**,
**the United States (533.7 TWh)**, **India (221.3 TWh)**, **Brazil (156.5 TWh)**, and **Germany (146.1 TWh)**.
Absolute growth highlights scale; percentage and share changes answer different questions and should not be
substituted for it.

### Share-based leaders are not necessarily absolute-growth leaders

Luxembourg, Lithuania, Denmark, and Lebanon were the top four countries by renewable-share gain in the
2010–2022 window. All four had lower total generation over the comparison window, and most had small absolute
renewable gains. This illustrates why a larger renewable share does not by itself prove a large increase in
renewable output: a country's total generation can also fall.

### Economic growth and falling CO₂ co-occurred for some countries

Of **208** countries represented in the transition comparison, **148** met the eligibility rules. **48** of the
eligible countries had GDP growth alongside falling national CO₂ over 2010–2022. This is a descriptive
classification of two endpoint changes, not evidence that renewable deployment caused emissions to fall.

## Example 2023 country values

| Country | Total generation | Renewable share | Fossil share |
|---|---:|---:|---:|
| China | 9,402.74 TWh | 30.0% | — |
| United States | 4,253.91 TWh | 22.7% | 59.1% |
| India | 1,916.85 TWh | 19.2% | — |
| Germany | 506.72 TWh | 54.7% | — |
| Norway | — | 98.5% | — |
| Kosovo | — | 12.6% | — |

The dashes mean the value is not included in this compact summary, not zero or missing from the source.

## How to read these findings

- Ember power-sector emissions are lifecycle CO₂e; OWID national CO₂ is territorial/economy-wide CO₂ excluding
  land use. These are not directly comparable quantities.
- Generation shares are not consumption shares. Net imports can make a country's consumption mix different.
- Ember's 2024 and 2025 values are estimates. In this vintage, 2024 has 194 countries and 2025 has 94, so use
  2023 or earlier when broad country coverage matters.
- GDP coverage ends in 2022 in the source vintage, which sets the transition-window endpoint.
- Year-on-year changes can be distorted by missing years or coverage breaks. Capacity is nameplate, and
  capacity-factor observations can be unreliable where Ember capacity placeholders are used.
- The report's world trends, shares, and growth comparisons are descriptive; GDP/CO₂ co-movement is
  associational. None of these analyses establish causation.

## Reproduce and verify

1. Follow the [operations runbook](operations.md) to refresh the sources and rebuild the dbt models.
2. Export the reporting tables with `uv run python -m ingestion.export`.
3. Refresh the Power BI Project using the generated files in `data/exports/`.
4. Compare the results with the checks in [powerbi/report_spec.md](powerbi/report_spec.md).

The project owner has confirmed that the PBIP opens in Power BI Desktop. A full review of visual rendering and
the expected measure values is still required before treating the dashboard as a signed-off publication.
