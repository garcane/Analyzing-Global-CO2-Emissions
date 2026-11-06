-- BLOCKS. Every Ember country/economy must resolve to the ISO reference (data/reference/ref_country.csv).
-- A new country or code in a future release fails here until the reference is updated deliberately.
select distinct s.iso3_code, s.area
from {{ ref('stg_ember__generation_yearly') }} as s
left join {{ ref('ref_country') }} as r on s.iso3_code = r.iso3
where s.area_type = 'Country or economy'
  and (s.iso3_code is null or r.iso3 is null)
