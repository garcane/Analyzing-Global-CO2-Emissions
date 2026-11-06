-- Ember rows with the project's geography key.
--   countries: ISO-3 code           regions/aggregates (World, EU, G20, ...): REG_<SLUG>
-- Aggregates are kept as geographies (Ember reports them natively) but flagged is_country = false
-- downstream. World and regions are never derived by summing countries.
select
    case
        when area_type = 'Country or economy' then iso3_code
        else 'REG_' || upper(regexp_replace(area, '[^A-Za-z0-9]+', '_'))
    end as geography_key,
    area,
    area_type,
    year,
    electricity_source,
    is_aggregated_source,
    generation_twh,
    share_of_generation_pct,
    capacity_gw,
    emissions_mtco2e,
    emissions_intensity_gco2e_kwh
from {{ ref('stg_ember__generation_yearly') }}
