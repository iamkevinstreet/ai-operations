-- Grain: one row per measure of a question under one search mode in
-- one retrieval run.
select
    {{ surrogate_key(['s.app', 's.run_id']) }} as run_key,
    s.app,
    s.run_id,
    r.run_at,
    r.model as embedding_model,
    s.retrieval_mode,
    s.case_id,
    s.metric,
    s.metric_value
from {{ ref('stg_ai_ops__retrieval_scores') }} as s
inner join {{ ref('stg_ai_ops__runs') }} as r
    on s.app = r.app and s.run_id = r.run_id
