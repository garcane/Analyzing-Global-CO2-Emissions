-- Grain: geography x year. The source-grain rows (geography x year x generating source) collapsed to one
-- row per geography-year. Every combination with country-year facts (population, GDP, CO2) happens AFTER
-- this step; joining source-grain rows directly would repeat those values once per source and inflate sums.
--
-- A missing source row means zero generation: in 1,216 of 5,916 country-years at least one of the nine
-- source rows is absent, and in every one of them the remaining sources add up to Ember's published
-- total (checked 2026-11-05). So missing rows are summed as 0 here, and completeness is judged by
-- reconciliation with the published total (see mart_country_energy_profile.is_complete_year).
select
    r.geography_key,
    r.year,
    count(*)                                                                          as n_source_rows,
    coalesce(sum(r.generation_twh), 0)                                                as total_generation_recomputed_twh,
    coalesce(sum(case when s.is_renewable then r.generation_twh end), 0)              as renewables_twh,
    coalesce(sum(case when s.category = 'fossil' then r.generation_twh end), 0)       as fossil_twh,
    coalesce(sum(case when s.category = 'nuclear' then r.generation_twh end), 0)      as nuclear_twh,
    coalesce(sum(case when s.source_name = 'Solar' then r.generation_twh end), 0)     as solar_twh,
    coalesce(sum(case when s.source_name = 'Wind' then r.generation_twh end), 0)      as wind_twh,
    coalesce(sum(case when s.source_name = 'Hydro' then r.generation_twh end), 0)     as hydro_twh,
    coalesce(sum(case when s.source_name = 'Bioenergy' then r.generation_twh end), 0) as bioenergy_twh,
    coalesce(sum(case when s.source_name = 'Coal' then r.generation_twh end), 0)      as coal_twh,
    coalesce(sum(case when s.source_name = 'Gas' then r.generation_twh end), 0)       as gas_twh
from {{ ref('int_ember__rows') }} as r
inner join {{ ref('energy_source') }} as s
    on r.electricity_source = s.source_name
where s.is_generation
  and not s.is_aggregate
group by r.geography_key, r.year
