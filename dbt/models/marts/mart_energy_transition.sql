-- Grain: country x window (one window, set by vars transition_start_year / transition_end_year).
-- ASSOCIATIONAL, not causal: it reports how shares, emissions and GDP moved over the same period.
with p as (
    select * from {{ ref('mart_country_energy_profile') }}
),

s as (select * from p where year = {{ var('transition_start_year') }}),
e as (select * from p where year = {{ var('transition_end_year') }}),

changes as (
    select
        e.geography_key,
        e.country_name,
        e.continent,
        {{ var('transition_start_year') }}                       as start_year,
        {{ var('transition_end_year') }}                         as end_year,

        s.total_generation_twh                                   as start_generation_twh,
        e.total_generation_twh                                   as end_generation_twh,
        s.renewable_share_pct                                    as start_renewable_share_pct,
        e.renewable_share_pct                                    as end_renewable_share_pct,
        e.renewable_share_pct - s.renewable_share_pct            as renewable_share_change_pp,
        -- Read the share change together with these: a share can rise because fossil generation FELL
        -- (e.g. a collapsing grid), not because renewables grew.
        e.total_generation_twh - s.total_generation_twh          as total_generation_change_twh,
        e.renewables_twh - s.renewables_twh                      as renewables_change_twh,
        e.fossil_share_pct - s.fossil_share_pct                  as fossil_share_change_pp,
        e.coal_share_pct - s.coal_share_pct                      as coal_share_change_pp,
        e.gas_share_pct - s.gas_share_pct                        as gas_share_change_pp,
        e.power_carbon_intensity_gco2e_kwh - s.power_carbon_intensity_gco2e_kwh
                                                                 as carbon_intensity_change_gco2e_kwh,

        case when s.gdp_intl_dollar_2011 > 0
             then (e.gdp_intl_dollar_2011 / s.gdp_intl_dollar_2011 - 1) * 100 end as gdp_growth_pct,
        case when s.national_co2_mt > 0
             then (e.national_co2_mt / s.national_co2_mt - 1) * 100 end            as national_co2_change_pct,

        -- GDP up and economy-wide CO2 down over the window (NULL if any of the four values is missing).
        case when s.gdp_intl_dollar_2011 > 0 and s.national_co2_mt > 0
                  and e.gdp_intl_dollar_2011 is not null and e.national_co2_mt is not null
             then e.gdp_intl_dollar_2011 > s.gdp_intl_dollar_2011
                  and e.national_co2_mt < s.national_co2_mt end                    as is_economy_co2_decoupled,

        -- Eligible = both endpoint years reconcile to Ember's totals and the country is big enough to compare.
        (coalesce(s.is_complete_year, false)
         and coalesce(e.is_complete_year, false)
         and s.total_generation_twh >= {{ var('transition_min_generation_twh') }}) as is_eligible
    from e
    inner join s on e.geography_key = s.geography_key
)

select
    *,
    case when is_eligible
         then rank() over (partition by is_eligible order by renewable_share_change_pp desc nulls last)
    end as renewable_share_change_rank
from changes
