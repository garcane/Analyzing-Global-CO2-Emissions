{{ config(severity='warn') }}
-- WARNS. A new release of a source should look like the previous one plus new data.
-- Compares the latest successful load of each source with the one before it.
-- Threshold (var row_count_change_warn_pct = 5): one new Ember year adds about 3,400 rows to ~104k
-- (3.3%), so a bigger jump in a single release suggests a structural change (new labels, dropped
-- coverage), not just a new year. Returns no rows while a source has only one successful load.
with loads as (
    select
        source_name,
        loaded_rows,
        row_number() over (partition by source_name order by finished_at_utc desc) as recency
    from {{ source('raw_meta', 'ingestion_log') }}
    where status = 'SUCCESS'
)

select
    latest.source_name,
    latest.loaded_rows                                                                  as latest_rows,
    previous.loaded_rows                                                                as previous_rows,
    abs(latest.loaded_rows - previous.loaded_rows) / nullif(previous.loaded_rows, 0) * 100 as change_pct
from loads as latest
inner join loads as previous
    on latest.source_name = previous.source_name
   and latest.recency = 1
   and previous.recency = 2
where abs(latest.loaded_rows - previous.loaded_rows) / nullif(previous.loaded_rows, 0) * 100
      > {{ var('row_count_change_warn_pct') }}
