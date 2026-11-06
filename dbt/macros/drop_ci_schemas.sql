{#
  Clean-up for CI / throwaway dev runs: drops the schemas a run with DBT_DEV_SUFFIX=ci_<id> created.
    dbt run-operation drop_ci_schemas --args '{suffix: ci_12345}'
  Guards: only suffixes starting with "ci_", and never the prod target, so it cannot drop real schemas.
#}
{% macro drop_ci_schemas(suffix) %}
    {% if target.name == 'prod' %}
        {{ exceptions.raise_compiler_error("drop_ci_schemas refuses to run against the prod target") }}
    {% endif %}
    {% if suffix is none or not (suffix | string).startswith('ci_') or (suffix | string) == 'ci_' %}
        {{ exceptions.raise_compiler_error("drop_ci_schemas: suffix must start with 'ci_' and name a run") }}
    {% endif %}
    {% set base = target.database ~ '.dbt_' ~ suffix %}
    {% for layer in ['staging', 'intermediate', 'marts'] %}
        {% do run_query('drop schema if exists ' ~ base ~ '_' ~ layer ~ ' cascade') %}
        {{ log('dropped ' ~ base ~ '_' ~ layer, info=True) }}
    {% endfor %}
    {% do run_query('drop schema if exists ' ~ base ~ ' cascade') %}
    {{ log('dropped ' ~ base, info=True) }}
{% endmacro %}
