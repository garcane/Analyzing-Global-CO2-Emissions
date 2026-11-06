-- Grain: one row per geography. Countries come from the ISO reference; regions/aggregates are the
-- Ember "Region" areas. Country-level analysis filters is_country = true.
with countries as (
    select
        iso3            as geography_key,
        name            as geography_name,
        'country'       as entity_type,
        continent,
        true            as is_country
    from {{ ref('ref_country') }}
),

regions as (
    select distinct
        geography_key,
        area            as geography_name,
        'region'        as entity_type,
        cast(null as varchar) as continent,
        false           as is_country
    from {{ ref('int_ember__rows') }}
    where area_type = 'Region'
)

select * from countries
union all
select * from regions
