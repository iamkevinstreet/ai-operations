-- Grain: one row per live run, beside the run before it of the same
-- name (live-hybrid after live-hybrid): how its judged metric, cost per
-- case and median time moved. Each window is written out in full, as
-- Snowflake has no WINDOW clause to name one.
with runs as (
    select
        r.app,
        r.run_id,
        r.run_name,
        r.run_at,
        r.cases,
        a.primary_metric,
        r.primary_metric_value,
        r.cost_per_case_usd,
        r.latency_p50_ms
    from {{ ref('fct_eval_runs') }} as r
    inner join {{ ref('dim_apps') }} as a
        on r.app = a.app
    where r.is_live
),

ordered as (
    select
        *,
        lag(run_id) over (partition by app, run_name order by run_at) as previous_run_id,
        lag(primary_metric_value) over (partition by app, run_name order by run_at)
            as previous_metric_value,
        lag(cost_per_case_usd) over (partition by app, run_name order by run_at)
            as previous_cost_per_case_usd,
        lag(latency_p50_ms) over (partition by app, run_name order by run_at)
            as previous_latency_p50_ms
    from runs
)

select
    {{ surrogate_key(['app', 'run_id']) }} as run_key,
    app,
    run_id,
    run_name,
    run_at,
    cases,
    primary_metric,
    primary_metric_value,
    previous_run_id,
    previous_metric_value,
    primary_metric_value - previous_metric_value as metric_change,
    cost_per_case_usd,
    cost_per_case_usd - previous_cost_per_case_usd as cost_per_case_change,
    latency_p50_ms,
    latency_p50_ms - previous_latency_p50_ms as latency_p50_change_ms
from ordered
