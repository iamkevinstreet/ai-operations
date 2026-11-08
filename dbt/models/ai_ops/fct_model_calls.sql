-- Grain: one row per model call, from the run's trace when it has one
-- and from the intake agent's run file otherwise. list_cost_usd prices
-- the call's tokens at the price list valid on the run's date, which
-- a test holds equal to the cost the app recorded.
with calls as (
    select
        c.*,
        cast(r.run_at as date) as run_date
    from {{ ref('int_ai_ops__model_calls') }} as c
    inner join {{ ref('stg_ai_ops__runs') }} as r
        on c.app = r.app and c.run_id = r.run_id
)

select
    {{ surrogate_key(['c.app', 'c.run_id', 'c.case_id', 'c.call_source', 'c.span_id', 'c.step']) }}
        as call_key,
    {{ surrogate_key(['c.app', 'c.run_id', 'c.case_id']) }} as case_key,
    c.app,
    c.run_id,
    c.case_id,
    c.call_source,
    c.span_id,
    c.step,
    c.model,
    c.provider,
    c.input_tokens,
    c.output_tokens,
    c.cost_usd,
    round(
        (c.input_tokens * p.input_per_mtok + c.output_tokens * p.output_per_mtok) / 1000000, 6
    ) as list_cost_usd,
    p.valid_from as prices_as_of,
    c.latency_ms,
    c.finish_reason,
    c.started_at
from calls as c
left join {{ ref('dim_model_prices') }} as p
    on c.model = p.model
    and c.run_date >= p.valid_from
    and (p.valid_to is null or c.run_date < p.valid_to)
