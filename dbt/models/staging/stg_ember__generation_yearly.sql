-- Grain: area x year x electricity source (latest successful load only).
-- Typing only: no business logic. Unparseable values become NULL (try_*) and are caught by tests.
select
    area,
    nullif(iso_3_code, '')                                  as iso3_code,
    try_to_number(year)::int                                as year,
    area_type,
    electricity_source,
    try_to_boolean(is_aggregated_source)                    as is_aggregated_source,
    try_to_decimal(generation_twh, 18, 6)                   as generation_twh,
    -- RAW name has no "_pct": the loader's column rule drops the "%" from "Share of generation (%)".
    try_to_decimal(share_of_generation, 18, 6)              as share_of_generation_pct,
    try_to_decimal(capacity_gw, 18, 6)                      as capacity_gw,
    try_to_decimal(emissions_mtco2e, 18, 6)                 as emissions_mtco2e,
    try_to_decimal(emissions_intensity_gco2e_kwh, 18, 6)    as emissions_intensity_gco2e_kwh,
    _load_id                                                as load_id
from {{ from_latest_load(source('raw_ember', 'generation_yearly'), 'ember_yearly_csv') }}
