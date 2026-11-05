-- Grain: entity x year (latest successful load only). Includes non-country aggregates (iso_code is null);
-- they are removed when joining to the country reference, not here.
select
    country,
    nullif(iso_code, '')                            as iso_code,
    try_to_number(year)::int                        as year,
    try_to_double(population)                       as population,
    try_to_double(gdp)                              as gdp_intl_dollar_2011,
    try_to_double(co2)                              as co2_mt,
    try_to_double(co2_per_capita)                   as co2_per_capita_t,
    try_to_double(consumption_co2)                  as consumption_co2_mt,
    try_to_double(primary_energy_consumption)       as primary_energy_twh,
    try_to_double(energy_per_capita)                as energy_per_capita_kwh,
    _load_id                                        as load_id
from {{ from_latest_load(source('raw_owid', 'co2'), 'owid_co2_csv') }}
