-- Grain: one row per tool call an intake scenario recorded.
select
    app,
    run_id,
    case_id,
    seq,
    step,
    tool as tool_name,
    ok as succeeded,
    error_message,
    latency_ms,
    cast(called_at as timestamp) as called_at,
    result_sha256
from {{ source('ai_ops', 'agent_tool_calls') }}
