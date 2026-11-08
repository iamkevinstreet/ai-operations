-- Grain: one row per case of a run, in either app format. The intake
-- format reports no failed scenarios, so its completed is unknown.
select
    app,
    run_id,
    case_id,
    completed,
    latency_ms,
    cost_usd,
    model_calls,
    cast(null as bigint) as tool_calls
from {{ ref('stg_ai_ops__cases') }}

union all

select
    app,
    run_id,
    case_id,
    cast(null as boolean) as completed,
    latency_ms,
    cost_usd,
    model_calls,
    tool_calls
from {{ ref('stg_ai_ops__scenarios') }}
