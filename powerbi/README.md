# Power BI project (PBIP)

`GEI.pbip` is a Power BI Project: plain text files instead of a binary `.pbix`, so the model and report diff
and review in git. It reads the six CSVs in `data/exports/` (written by `python -m ingestion.export`), so it
works with no Snowflake connection and keeps working after the Snowflake trial ends.

```
GEI.pbip
GEI.SemanticModel/   TMDL model: 6 tables, 5 relationships, 31 measures, one parameter (ExportsFolder)
GEI.Report/          PBIR report: 6 pages, 30 visuals, GEI Emerald theme
```

## Open it
1. Power BI Desktop (Windows, a current release): **File > Open report > Browse** and pick `powerbi/GEI.pbip`.
2. If the data fails to load: **Home > Transform data > Edit parameters** and set `ExportsFolder` to the full path
   of `data/exports\` on your machine (it must end with a backslash). The default is this repository's path on
   the machine that generated it.
3. **Refresh**. Save. After your first save Desktop owns the files: edit in Desktop, not by hand.

## Pages
1. World overview (Ember's own World figures) 2. Country mix 3. Renewable growth and capacity 4. Transition
leaders 5. Emissions and economy 6. Data notes. Annual-analysis pages have year slicers bound directly to each
visual's annual fact table; country mix and transition leaders include geographic maps. Transition leaders remains
a fixed 2010-2022 window. See `docs/powerbi/report_spec.md` for the question each page answers and
`docs/powerbi/model.md` for the model rules (never average percentages, never sum countries to get the World,
regions only appear on page 1).

## What has and has not been checked
| Check | Status |
|---|---|
| Original report JSON files validate against Microsoft's published JSON schemas | done before this redesign; new map/slicer JSON parses but is not schema-validated |
| Report format versions match the files this Desktop release wrote itself (`version.json` 2.0.0, page 2.1.0, pages 1.1.0, report 3.3.0 with the Fluent2 theme) | done, after the first open failed with "cannot read visualContainers" because the first version used older format versions |
| Updated semantic model reloads from the TMDL folder (6 tables, 5 relationships, 31 measures) | done via the Power BI authoring MCP |
| All report field bindings refer to a column or measure that exists in the model | done for the original report; new map and date bindings match the updated model |
| Model and project settings match what Power BI Desktop itself wrote (model version 4.2, compatibility level 1606) | done |
| **Updated report opened in Power BI Desktop** | **not done** |
| Visual type names (`lineChart`, `areaChart`, `stackedColumnChart`, `scatterChart`, `tableEx`, `slicer`, `textbox`, `filledMap`) and their role names (including `Location` and `Color saturation`) | **unverified** until Desktop opens the report |
| Text-box paragraph JSON and the TMDL/M text (parameter, CSV partitions, measure expressions) | **unverified** until Desktop loads them |
| DAX measures return the expected numbers | **unverified**: compare with the table in `docs/powerbi/report_spec.md` |

If Desktop reports an error when opening, it names the file. The most likely culprits are individual
`visuals/<name>/visual.json` files: delete that one visual folder and Desktop opens the rest, then re-create the
visual in the UI. A model-level error will name a `.tmdl` file under `GEI.SemanticModel/definition/`.

## Power BI Modeling MCP (optional)
Microsoft's server (`@microsoft/powerbi-modeling-mcp`, version 1.0.0, MIT, maintained by Microsoft) is registered for
this project in Claude Code's local config (not in the repo). It can edit and query the semantic model (tables,
columns, measures, relationships, DAX queries) of a model open in Power BI Desktop or a TMDL folder, so it can run
the DAX checks against the expected values. It **cannot** change report pages or visuals, so it cannot fix
problems in `GEI.Report`. Its tools appear only in a new Claude Code session, and its EULA must be accepted by you
(it blocks every tool until you do). It collects usage data for Microsoft and may self-update.
