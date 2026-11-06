-- Grain: geography x year x generating source (the nine base sources only).
-- Excluded on purpose: aggregate rows (Total, Fossil, Renewables, ...) so nothing double counts,
-- and Net imports / Demand, which are trade and demand, not generation (see fct_electricity_balance).
-- generation_twh is energy over the year (TWh); capacity_gw is nameplate power (GW). Never mixed here.
select
    r.geography_key,
    r.year,
    s.source_key,
    r.generation_twh,
    r.capacity_gw,
    r.emissions_mtco2e as power_emissions_mtco2e
from {{ ref('int_ember__rows') }} as r
inner join {{ ref('dim_energy_source') }} as s
    on r.electricity_source = s.source_name
where s.is_generation
  and not s.is_aggregate
