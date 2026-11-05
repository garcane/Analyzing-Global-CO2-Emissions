{#
  dbt's default builds "<target schema>_<custom schema>" everywhere. Here:
  - prod writes to the exact STAGING / INTERMEDIATE / MARTS schemas, because GEI_REPORTER's grants
    (Power BI, later the AI assistant) are defined on GEI_ANALYTICS.MARTS exactly;
  - every other target (dev, CI) is prefixed with the target schema, so personal runs never touch prod.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim | upper }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
