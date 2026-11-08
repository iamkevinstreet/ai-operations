-- Grain: one row per model call an intake scenario recorded.
select
    app,
    run_id,
    case_id,
    step,
    input_tokens,
    output_tokens,
    cost_usd,
    latency_ms,
    stop_reason as finish_reason
from {{ source('ai_ops', 'agent_model_calls') }}
