-- Grain: entity x year x series (latest successful API load only). Used for CSV reconciliation.
select
    entity,
    nullif(entity_code, '')                     as iso3_code,
    try_to_number(date)::int                    as year,
    series,
    try_to_boolean(is_aggregate_series)         as is_aggregate_series,
    try_to_decimal(generation_twh, 18, 6)       as generation_twh,
    _load_id                                    as load_id
from {{ from_latest_load(source('raw_ember', 'api_generation_yearly'), 'ember_api_generation') }}
