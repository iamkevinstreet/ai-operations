-- Grain: one row per number a run's summary published.
select
    app,
    run_id,
    metric as published_metric,
    metric_value as published_value
from {{ source('ai_ops', 'summaries') }}
