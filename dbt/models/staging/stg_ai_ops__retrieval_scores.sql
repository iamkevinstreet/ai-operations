-- Grain: one row per measure of a question under one search mode.
select
    app,
    run_id,
    retrieval_mode,
    case_id,
    metric,
    metric_value
from {{ source('ai_ops', 'retrieval_scores') }}
