-- Grain: one row per evaluation run (retrieval runs are in
-- fct_retrieval_scores). Percentiles are nearest-rank, as the apps
-- publish them, so a run's figures here equal its own summary's.
with runs as (
    select * from {{ ref('stg_ai_ops__runs') }}
    where run_format <> 'retrieval'
),

cases as (
    select
        app,
        run_id,
        count(*) as cases,
        cast(sum(case when completed then 0 when not completed then 1 end) as bigint)
            as failed_cases,
        sum(cost_usd) as cost_usd,
        avg(cost_usd) as cost_per_case_usd,
        percentile_disc(0.5) within group (order by latency_ms) as latency_p50_ms,
        percentile_disc(0.95) within group (order by latency_ms) as latency_p95_ms,
        cast(sum(model_calls) as bigint) as model_calls
    from {{ ref('int_ai_ops__cases') }}
    group by app, run_id
),

tokens as (
    select
        app,
        run_id,
        cast(sum(input_tokens) as bigint) as input_tokens,
        cast(sum(output_tokens) as bigint) as output_tokens
    from {{ ref('int_ai_ops__model_calls') }}
    group by app, run_id
),

judged as (
    select
        m.app,
        m.run_id,
        avg(m.metric_value) as primary_metric_value
    from {{ ref('int_ai_ops__case_metrics') }} as m
    inner join {{ ref('dim_apps') }} as a
        on m.app = a.app and m.metric = a.primary_metric
    where coalesce(m.completed, true)
    group by m.app, m.run_id
)

select
    {{ surrogate_key(['r.app', 'r.run_id']) }} as run_key,
    r.app,
    r.run_id,
    r.run_name,
    r.run_format,
    r.model,
    r.provider,
    r.is_live,
    r.run_at,
    r.started_at,
    r.finished_at,
    {{ dbt.datediff('r.started_at', 'r.finished_at', 'second') }} as run_seconds,
    c.cases,
    c.failed_cases,
    c.cost_usd,
    c.cost_per_case_usd,
    c.latency_p50_ms,
    c.latency_p95_ms,
    c.model_calls,
    t.input_tokens,
    t.output_tokens,
    j.primary_metric_value,
    r.prices_as_of,
    r.source_commit,
    r.run_file
from runs as r
left join cases as c on r.app = c.app and r.run_id = c.run_id
left join tokens as t on r.app = t.app and r.run_id = t.run_id
left join judged as j on r.app = j.app and r.run_id = j.run_id
