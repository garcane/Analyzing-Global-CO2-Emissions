-- BLOCKS. Ember's identity: Renewables = Hydro + Wind + Solar + Bioenergy + Other renewables.
-- Scope matches what was verified on the 2026-11-05 file: country rows where all five components and the
-- published Renewables row are present (4,788 country-years, 0 mismatches, max drift 0.002 TWh).
-- Returns violating rows; passes when empty.
with c as (
    select
        geography_key,
        year,
        max(case when electricity_source = 'Renewables' then generation_twh end)                   as published,
        sum(case when electricity_source in ('Hydro', 'Wind', 'Solar', 'Bioenergy', 'Other renewables')
                 then generation_twh end)                                                         as components,
        count(case when electricity_source in ('Hydro', 'Wind', 'Solar', 'Bioenergy', 'Other renewables')
                   then 1 end)                                                                    as n_components
    from {{ ref('int_ember__rows') }}
    where area_type = 'Country or economy'
    group by geography_key, year
)
select *
from c
where published is not null
  and n_components = 5
  and abs(published - components) > {{ var('tolerance_renewables_twh') }}
