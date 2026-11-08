-- Grain: one row per model call. A run's trace is the record of its
-- calls when it has one; otherwise the intake agent's own run file is.
-- No run is counted from both.
with traced_runs as (
    select distinct app, run_id
    from {{ ref('stg_ai_ops__spans') }}
),

from_traces as (
    select
        app,
        run_id,
        case_id,
        'trace' as call_source,
        span_id,
        cast(null as bigint) as step,
        coalesce(response_model, request_model) as model,
        provider,
        input_tokens,
        output_tokens,
        cost_usd,
        cast(round(duration_ms) as bigint) as latency_ms,
        finish_reason,
        started_at
    from {{ ref('int_ai_ops__spans') }}
    where operation = 'chat'
),

from_run_files as (
    select
        c.app,
        c.run_id,
        c.case_id,
        'run_file' as call_source,
        cast(null as {{ dbt.type_string() }}) as span_id,
        c.step,
        r.model,
        r.provider,
        c.input_tokens,
        c.output_tokens,
        c.cost_usd,
        c.latency_ms,
        c.finish_reason,
        cast(null as timestamp) as started_at
    from {{ ref('stg_ai_ops__agent_model_calls') }} as c
    inner join {{ ref('stg_ai_ops__runs') }} as r
        on c.app = r.app and c.run_id = r.run_id
    left join traced_runs as t
        on c.app = t.app and c.run_id = t.run_id
    where t.run_id is null
)

select * from from_traces
union all
select * from from_run_files
