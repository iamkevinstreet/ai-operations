-- A group's values as one sorted, comma-separated string. dbt's own
-- listagg ignores its order on Spark and Databricks, so each adapter
-- gets the form it sorts with.
{% macro sorted_list(column) -%}
    {{ return(adapter.dispatch('sorted_list', 'data_platform')(column)) }}
{%- endmacro %}

{% macro default__sorted_list(column) -%}
    string_agg({{ column }}, ', ' order by {{ column }})
{%- endmacro %}

{% macro databricks__sorted_list(column) -%}
    array_join(array_sort(collect_list({{ column }})), ', ')
{%- endmacro %}
