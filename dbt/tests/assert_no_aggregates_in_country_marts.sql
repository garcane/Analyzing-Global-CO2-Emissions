-- BLOCKS. Country-level marts must contain only real countries (no World, regions, income groups):
-- every geography_key must exist in the ISO country reference and none may be a REG_ aggregate key.
select geography_key, 'mart_country_energy_profile' as model_name
from {{ ref('mart_country_energy_profile') }}
where left(geography_key, 4) = 'REG_'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
union all
select geography_key, 'mart_renewable_growth'
from {{ ref('mart_renewable_growth') }}
where left(geography_key, 4) = 'REG_'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
union all
select geography_key, 'mart_energy_transition'
from {{ ref('mart_energy_transition') }}
where left(geography_key, 4) = 'REG_'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
