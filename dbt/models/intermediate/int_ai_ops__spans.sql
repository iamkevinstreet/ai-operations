-- Grain: one row per span. Only a trace's eval span names its case, so
-- every span of the trace takes the case from it.
select
    app,
    run_id,
    trace_id,
    span_id,
    parent_id,
    max(eval_case) over (partition by app, run_id, trace_id) as case_id,
    span_name,
    operation,
    span_kind,
    started_at,
    ended_at,
    duration_ms,
    status_code,
    service_name,
    service_version,
    provider,
    request_model,
    response_model,
    input_tokens,
    output_tokens,
    cost_usd,
    finish_reason,
    error_type,
    tool_name,
    observation_type
from {{ ref('stg_ai_ops__spans') }}
