-- Grain: one row per case of a run in the workbench's format. A case
-- that raised is not completed; its time and cost still count.
select
    app,
    run_id,
    case_id,
    ok as completed,
    error_message,
    latency_ms,
    cost_usd,
    model_calls
from {{ source('ai_ops', 'cases') }}
