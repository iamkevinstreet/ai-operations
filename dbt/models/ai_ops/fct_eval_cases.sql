-- Grain: one row per case of an evaluation run, with its tags and the
-- tokens its recorded model calls used.
with tags as (
    select
        app,
        run_id,
        case_id,
        {{ sorted_list('tag') }} as tags
    from {{ ref('stg_ai_ops__case_tags') }}
    group by app, run_id, case_id
),

calls as (
    select
        app,
        run_id,
        case_id,
        count(*) as recorded_calls,
        cast(sum(input_tokens) as bigint) as input_tokens,
        cast(sum(output_tokens) as bigint) as output_tokens
    from {{ ref('int_ai_ops__model_calls') }}
    group by app, run_id, case_id
)

select
    {{ surrogate_key(['c.app', 'c.run_id', 'c.case_id']) }} as case_key,
    {{ surrogate_key(['c.app', 'c.run_id']) }} as run_key,
    c.app,
    c.run_id,
    c.case_id,
    c.completed,
    c.latency_ms,
    c.cost_usd,
    c.model_calls,
    c.tool_calls,
    k.recorded_calls,
    k.input_tokens,
    k.output_tokens,
    t.tags
from {{ ref('int_ai_ops__cases') }} as c
left join tags as t
    on c.app = t.app and c.run_id = t.run_id and c.case_id = t.case_id
left join calls as k
    on c.app = k.app and c.run_id = k.run_id and c.case_id = k.case_id
