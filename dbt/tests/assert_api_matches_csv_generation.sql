{{ config(severity='warn') }}
-- WARNS. Ember's API and bulk CSV are separate publication channels and can briefly disagree
-- (API 2-decimal rounding => 0.01 TWh tolerance). On 2026-11-05 all 94,366 API rows matched the CSV.
-- Rows returned: API values with no CSV counterpart, or differing by more than the rounding tolerance.
select
    a.entity,
    a.year,
    a.series,
    a.generation_twh as api_twh,
    c.generation_twh as csv_twh
from {{ ref('stg_ember_api__generation_yearly') }} as a
left join {{ ref('int_ember__rows') }} as c
    on a.entity = c.area and a.year = c.year and a.series = c.electricity_source
where c.area is null
   or abs(a.generation_twh - c.generation_twh) > 0.01
