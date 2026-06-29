{% macro silver_delta(table_name) -%}
delta.`{{ var("silver_path") }}/{{ table_name }}`
{%- endmacro %}
