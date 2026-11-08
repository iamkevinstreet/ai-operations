-- Grain: one row per run and operation (retrieval, chat, verify, tool
-- calls...): where a traced run's time went.
select
    app,
    run_id,
    operation,
    count(*) as spans,
    sum(duration_ms) as total_ms,
    avg(duration_ms) as mean_ms,
    percentile_cont(0.5) within group (order by duration_ms) as p50_ms,
    percentile_cont(0.95) within group (order by duration_ms) as p95_ms
from {{ ref('fct_spans') }}
group by app, run_id, operation
