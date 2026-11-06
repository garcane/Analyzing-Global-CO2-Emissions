-- Grain: one row per Ember "Electricity source" value, including aggregates, trade and demand.
-- This is where "what counts as renewable / low-carbon / generation" is defined.
select
    regexp_replace(lower(source_name), '[^a-z0-9]+', '_') as source_key,
    source_name,
    category,
    is_aggregate,
    is_renewable,
    is_low_carbon,
    is_generation
from {{ ref('energy_source') }}
