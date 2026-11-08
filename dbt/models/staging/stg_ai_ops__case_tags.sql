-- Grain: one row per tag of a case or scenario.
select
    app,
    run_id,
    case_id,
    tag
from {{ source('ai_ops', 'case_tags') }}
