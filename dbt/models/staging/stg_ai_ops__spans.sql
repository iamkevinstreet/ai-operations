-- Grain: one row per span of a committed trace. A span with no GenAI
-- operation (eval, answer, extract, verify) is named by its first word.
select
    app,
    run_id,
    trace_id,
    span_id,
    parent_id,
    span_name,
    coalesce(operation, split_part(span_name, ' ', 1)) as operation,
    span_kind,
    cast(started_at as timestamp) as started_at,
    cast(ended_at as timestamp) as ended_at,
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
    observation_type,
    eval_case
from {{ source('ai_ops', 'spans') }}
