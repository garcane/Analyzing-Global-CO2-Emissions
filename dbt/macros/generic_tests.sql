{# Generic tests kept in-project (no external dbt packages, so `dbt deps` is not needed). #}

{% test accepted_range(model, column_name, min_value=none, max_value=none) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and (
    {% if min_value is not none %}{{ column_name }} < {{ min_value }}{% else %}false{% endif %}
    or
    {% if max_value is not none %}{{ column_name }} > {{ max_value }}{% else %}false{% endif %}
  )
{% endtest %}

{% test unique_combination_of_columns(model, combination_of_columns) %}
select {{ combination_of_columns | join(', ') }}, count(*) as n_rows
from {{ model }}
group by {{ combination_of_columns | join(', ') }}
having count(*) > 1
{% endtest %}
