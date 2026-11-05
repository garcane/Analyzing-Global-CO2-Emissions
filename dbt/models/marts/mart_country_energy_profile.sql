-- Grain: country x year. The wide table behind most dashboard pages.
-- Descriptive measures only (levels, shares, per-capita). Economy figures come from OWID and are NULL
-- where OWID has no row (or no value) for that country-year; nothing is imputed.
-- Shares use the published total as denominator and are NULL unless the year reconciles (is_complete_year).
with gen as (
    select * from {{ ref('int_generation_by_geography_year') }}
),

bal as (
    select * from {{ ref('fct_electricity_balance') }}
),

eco as (
    select * from {{ ref('fct_country_economy_emissions') }}
),

geo as (
    select * from {{ ref('dim_geography') }} where is_country
),

joined as (
    select
        g.geography_key,
        geo.geography_name                                   as country_name,
        geo.continent,
        g.year,

        bal.published_total_generation_twh                   as total_generation_twh,
        g.total_generation_recomputed_twh,
        -- Complete = Ember published a total AND the nine sources reconcile to it (missing rows = 0 TWh).
        coalesce(
            abs(g.total_generation_recomputed_twh - bal.published_total_generation_twh)
                <= {{ var('tolerance_total_twh') }},
            false
        )                                                    as is_complete_year,

        g.renewables_twh,
        g.fossil_twh,
        g.nuclear_twh,
        g.solar_twh,
        g.wind_twh,
        g.hydro_twh,
        g.bioenergy_twh,
        g.coal_twh,
        g.gas_twh,

        bal.demand_twh,
        bal.net_imports_twh,
        bal.renewables_capacity_gw,
        bal.power_emissions_mtco2e,
        bal.power_carbon_intensity_gco2e_kwh,

        eco.population,
        eco.gdp_intl_dollar_2011,
        eco.national_co2_mt,
        eco.national_co2_per_capita_t,
        eco.primary_energy_twh,
        eco.geography_key is not null                        as has_economy_row
    from gen as g
    inner join geo on g.geography_key = geo.geography_key
    left join bal on g.geography_key = bal.geography_key and g.year = bal.year
    left join eco on g.geography_key = eco.geography_key and g.year = eco.year
)

select
    *,
    case when is_complete_year and total_generation_twh > 0
         then renewables_twh / total_generation_twh * 100 end   as renewable_share_pct,
    case when is_complete_year and total_generation_twh > 0
         then fossil_twh / total_generation_twh * 100 end       as fossil_share_pct,
    case when is_complete_year and total_generation_twh > 0
         then nuclear_twh / total_generation_twh * 100 end      as nuclear_share_pct,
    case when is_complete_year and total_generation_twh > 0
         then (solar_twh + wind_twh) / total_generation_twh * 100 end as wind_solar_share_pct,
    case when is_complete_year and total_generation_twh > 0
         then coal_twh / total_generation_twh * 100 end         as coal_share_pct,
    case when is_complete_year and total_generation_twh > 0
         then gas_twh / total_generation_twh * 100 end          as gas_share_pct,
    -- kWh per person: TWh * 1e9 kWh/TWh / people. NULL without a population (no imputation).
    case when population > 0 and total_generation_twh is not null
         then total_generation_twh * 1e9 / population end       as generation_per_capita_kwh
from joined
