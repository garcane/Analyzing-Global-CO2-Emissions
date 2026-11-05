# Legacy notebook (kept as a historical analysis)

`main.ipynb` is the original exploratory CO₂ analysis. It is **unchanged** apart from its location.

- It reads `owid-co2-data.csv` from the current directory. To run it from here, change cell 4 to `../../data/owid-co2-data.csv`.
- The saved notebook has no outputs; re-run it to see results.

## Known defects (checked against `data/owid-co2-data.csv`)

1. **Aggregates counted as countries.** The `PURE_COUNTRIES` name regex misses `Asia (excl. China and India)`, `North America (excl. USA)`, `International aviation`, `International shipping` and `Kosovo`. The 2020 "top 5 emitters" (cell 19, chart 5) therefore lists "Asia (excl. China and India)" second, and the top-10 share (cell 13) is 71.5% against 69.9% when restricted to ISO-coded countries.
2. **Chart 7 (cumulative emitters)** uses a filter without `World`, so `World` ranks first (~1,812 Gt) and `Asia (excl. China and India)` ranks fourth.
3. **Population is filled with one global median** (cell 7), which fabricates per-capita values for any affected row. Most affected rows are aggregates, but this was not isolated by country.
4. **Chart 3** plots each continent's aggregate row over 34 years, not a distribution of countries.
5. **Decoupling (cell 25)** correlates GDP and CO₂ levels, which both trend upward; a growth-based measure is more meaningful.
6. **Linear projection (cell 31)** has no uncertainty or scenario basis.

These are re-specified, not copied, in the dbt models (see `docs/business_logic/metrics.md`).
