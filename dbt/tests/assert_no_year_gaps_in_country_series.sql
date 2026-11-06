{{ config(severity='warn') }}
-- WARNS. A country's generation series should be continuous between its first and last year.
-- Gaps are real in some countries; they are reported, not blocked, because they change what a
-- year-on-year chart can show (growth is only computed against the immediately preceding year).
select
    geography_key,
    min(year)                           as first_year,
    max(year)                           as last_year,
    count(distinct year)                as n_years,
    max(year) - min(year) + 1           as expected_years
from {{ ref('mart_country_energy_profile') }}
group by geography_key
having count(distinct year) <> max(year) - min(year) + 1
