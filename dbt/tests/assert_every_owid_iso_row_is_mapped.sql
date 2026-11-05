-- BLOCKS. Every OWID row that carries an ISO code must resolve to the reference. (OWID rows without an ISO
-- code are aggregates and are dropped by design, except Kosovo, which is matched by name.)
select distinct o.iso_code, o.country
from {{ ref('stg_owid__co2') }} as o
left join {{ ref('ref_country') }} as r on o.iso_code = r.iso3
where o.iso_code is not null
  and r.iso3 is null
