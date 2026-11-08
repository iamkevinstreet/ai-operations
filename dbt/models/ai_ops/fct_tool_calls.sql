-- Grain: one row per tool call the intake agent made, in order.
select
    {{ surrogate_key(['app', 'run_id', 'case_id', 'seq']) }} as tool_call_key,
    {{ surrogate_key(['app', 'run_id', 'case_id']) }} as case_key,
    app,
    run_id,
    case_id,
    seq,
    step,
    tool_name,
    succeeded,
    error_message,
    latency_ms,
    called_at
from {{ ref('stg_ai_ops__agent_tool_calls') }}
