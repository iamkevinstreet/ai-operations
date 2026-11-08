-- Every priced model call's recorded cost equals its tokens at the
-- list price valid on its run's date, to the workbench's rounding.
-- A row here means an app costed a call differently from its own price
-- list, or the list changed without a new version being loaded.
select
    call_key,
    app,
    run_id,
    model,
    cost_usd,
    list_cost_usd
from {{ ref('fct_model_calls') }}
where list_cost_usd is not null
    and abs(list_cost_usd - cost_usd) > 0.0000011
