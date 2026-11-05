-- Grain: country x year x series, series in (solar, wind, hydro, renewables).
-- Answers: which countries grew renewable generation most, and is installed capacity turning into
-- electricity (capacity factor). Always read absolute TWh beside % growth: % from a tiny base is noise.
with by_source as (
    select
        r.geography_key,
        r.year,
        lower(r.electricity_source) as series,
        r.generation_twh,
        r.capacity_gw
    from {{ ref('int_ember__rows') }} as r
    where r.electricity_source in ('Solar', 'Wind', 'Hydro')
),

renewables as (
    select
        g.geography_key,
        g.year,
        'renewables'                    as series,
        g.renewables_twh                as generation_twh,
        b.renewables_capacity_gw        as capacity_gw
    from {{ ref('int_generation_by_geography_year') }} as g
    left join {{ ref('fct_electricity_balance') }} as b
        on g.geography_key = b.geography_key and g.year = b.year
),

unioned as (
    select * from by_source
    union all
    select * from renewables
),

countries as (
    select u.*, geo.geography_name as country_name, geo.continent
    from unioned as u
    inner join {{ ref('dim_geography') }} as geo
        on u.geography_key = geo.geography_key and geo.is_country
),

lagged as (
    select
        *,
        lag(generation_twh) over (partition by geography_key, series order by year) as prev_generation_twh,
        lag(year)           over (partition by geography_key, series order by year) as prev_year
    from countries
)

select
    geography_key,
    country_name,
    continent,
    year,
    series,
    generation_twh,
    capacity_gw,
    -- Year-on-year change only against the immediately preceding year.
    case when prev_year = year - 1 then generation_twh - prev_generation_twh end as yoy_change_twh,
    case when prev_year = year - 1 and prev_generation_twh > 0
         then (generation_twh - prev_generation_twh) / prev_generation_twh * 100 end as yoy_change_pct,
    -- Capacity factor = TWh*1000 / (GW * hours). Nameplate basis; capacity added during the year biases it
    -- low; 8784 hours in leap years.
    case when capacity_gw > 0 and generation_twh is not null
         then generation_twh * 1000
              / (capacity_gw * case when (year % 4 = 0 and year % 100 <> 0) or year % 400 = 0
                                    then 8784 else 8760 end) end as capacity_factor
from lagged
