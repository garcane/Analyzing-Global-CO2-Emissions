-- Grain: geography x year. Ember's published country-year totals: demand, trade, published aggregates
-- (kept so the recomputed totals can be reconciled against them) and power-sector emissions.
select
    geography_key,
    year,
    max(case when electricity_source = 'Demand'           then generation_twh end) as demand_twh,
    max(case when electricity_source = 'Net imports'      then generation_twh end) as net_imports_twh,
    max(case when electricity_source = 'Total generation' then generation_twh end) as published_total_generation_twh,
    max(case when electricity_source = 'Renewables'       then generation_twh end) as published_renewables_twh,
    max(case when electricity_source = 'Fossil'           then generation_twh end) as published_fossil_twh,
    max(case when electricity_source = 'Renewables'       then capacity_gw end)    as renewables_capacity_gw,
    max(case when electricity_source = 'Total generation' then capacity_gw end)    as total_capacity_gw,
    -- Ember emissions are LIFECYCLE (upstream methane, supply chain; 100-year CO2e), not combustion-only.
    max(case when electricity_source = 'Total generation' then emissions_mtco2e end) as power_emissions_mtco2e,
    max(case when electricity_source = 'Total generation' then emissions_intensity_gco2e_kwh end) as power_carbon_intensity_gco2e_kwh
from {{ ref('int_ember__rows') }}
group by geography_key, year
