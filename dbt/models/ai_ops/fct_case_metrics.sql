-- Grain: one row per metric of a case: its scores, time, cost and,
-- for the intake agent, the fields its summary is built from.
select
    {{ surrogate_key(['app', 'run_id', 'case_id']) }} as case_key,
    app,
    run_id,
    case_id,
    metric,
    metric_value,
    completed
from {{ ref('int_ai_ops__case_metrics') }}
