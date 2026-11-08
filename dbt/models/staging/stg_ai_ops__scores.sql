-- Grain: one row per numeric score of a case.
select
    app,
    run_id,
    case_id,
    metric,
    metric_value
from {{ source('ai_ops', 'scores') }}
