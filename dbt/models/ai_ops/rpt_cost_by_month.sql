-- Grain: one row per month, app and model, over live runs only: what
-- the evaluations cost and how much each case cost on average.
select
    cast({{ dbt.date_trunc('month', 'run_at') }} as date) as month,
    app,
    model,
    count(*) as runs,
    cast(sum(cases) as bigint) as cases,
    sum(cost_usd) as cost_usd,
    sum(cost_usd) / nullif(sum(cases), 0) as cost_per_case_usd,
    cast(sum(input_tokens) as bigint) as input_tokens,
    cast(sum(output_tokens) as bigint) as output_tokens
from {{ ref('fct_eval_runs') }}
where is_live
group by {{ dbt.date_trunc('month', 'run_at') }}, app, model
