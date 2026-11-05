-- Grain: country x year (OWID). Only entities that map to the country reference; OWID aggregates
-- (World, continents, income groups, "excl." groups, international transport) are dropped here.
-- Kosovo has no ISO code in OWID and is matched by name through ref_country.owid_name.
-- national_co2_mt is ECONOMY-WIDE territorial CO2 from combustion and industry (excl. land use),
-- not electricity-sector emissions (see fct_electricity_balance.power_emissions_mtco2e).
select
    r.iso3                      as geography_key,
    o.year,
    o.co2_mt                    as national_co2_mt,
    o.co2_per_capita_t          as national_co2_per_capita_t,
    o.consumption_co2_mt,
    o.population,
    o.gdp_intl_dollar_2011      as gdp_intl_dollar_2011,
    o.primary_energy_twh,
    o.energy_per_capita_kwh
from {{ ref('stg_owid__co2') }} as o
inner join {{ ref('ref_country') }} as r
    on (o.iso_code is not null and o.iso_code = r.iso3)
    or (o.iso_code is null and o.country = r.owid_name)
