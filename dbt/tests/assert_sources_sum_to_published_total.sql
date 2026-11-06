-- BLOCKS. The nine generating sources (missing rows = 0 TWh) must add up to Ember's published
-- Total generation for every COUNTRY-year that has a published total (5,916 country-years, 0 mismatches on
-- 2026-11-05, including the 1,216 with a missing source row). A failure means a source label changed,
-- a source is mis-classified, or the file is damaged. Regions are not tested: not verified.
select
    g.geography_key,
    g.year,
    g.total_generation_recomputed_twh,
    b.published_total_generation_twh
from {{ ref('int_generation_by_geography_year') }} as g
inner join {{ ref('fct_electricity_balance') }} as b
    on g.geography_key = b.geography_key and g.year = b.year
inner join {{ ref('dim_geography') }} as geo
    on g.geography_key = geo.geography_key and geo.is_country
where b.published_total_generation_twh is not null
  and abs(g.total_generation_recomputed_twh - b.published_total_generation_twh) > {{ var('tolerance_total_twh') }}
