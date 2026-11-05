-- BLOCKS. Country-level marts must contain only real countries (no World, regions, income groups).
select geography_key, 'mart_country_energy_profile' as model
from {{ ref('mart_country_energy_profile') }}
where geography_key like 'REG\_%' escape '\'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
union all
select geography_key, 'mart_renewable_growth'
from {{ ref('mart_renewable_growth') }}
where geography_key like 'REG\_%' escape '\'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
union all
select geography_key, 'mart_energy_transition'
from {{ ref('mart_energy_transition') }}
where geography_key like 'REG\_%' escape '\'
   or geography_key not in (select iso3 from {{ ref('ref_country') }})
