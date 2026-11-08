-- Grain: one row per run and field, for apps that score each field
-- (EEOC's f_ scores): how often the model read the field right, over
-- the cases that completed. Where an extraction goes wrong, by field.
select
    app,
    run_id,
    substr(metric, 3) as field_name,
    count(*) as cases,
    avg(metric_value) as accuracy,
    cast(sum(case when metric_value < 1 then 1 else 0 end) as bigint) as wrong_cases
from {{ ref('fct_case_metrics') }}
where substr(metric, 1, 2) = 'f_'
    and coalesce(completed, true)
group by app, run_id, substr(metric, 3)
