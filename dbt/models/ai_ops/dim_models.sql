-- Grain: one row per model a run or a call used, with its current
-- list prices when the price list has it.
with seen as (
    select model, provider from {{ ref('stg_ai_ops__runs') }} where model is not null
    union
    select model, provider from {{ ref('int_ai_ops__model_calls') }} where model is not null
)

select
    s.model,
    max(s.provider) as provider,
    max(case when p.is_current then p.input_per_mtok end) as input_per_mtok,
    max(case when p.is_current then p.output_per_mtok end) as output_per_mtok
from seen as s
left join {{ ref('dim_model_prices') }} as p
    on s.model = p.model
group by s.model
