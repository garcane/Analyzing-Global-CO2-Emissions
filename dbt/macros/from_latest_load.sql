{#
  Restrict a RAW table to the rows of the latest SUCCESSFUL load of a source.
  RAW tables keep every load (snapshot-per-release); this is the only place that picks "the current one".
#}
{% macro from_latest_load(relation, source_name) -%}
(
    select t.*
    from {{ relation }} as t
    inner join {{ source('raw_meta', 'latest_successful_load') }} as l
        on t._load_id = l.load_id
       and l.source_name = '{{ source_name }}'
)
{%- endmacro %}
