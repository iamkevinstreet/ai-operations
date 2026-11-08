-- Grain: one row per metric of a case. The workbench's scores come as
-- they are; a case's time, cost and failure become metrics too, so a
-- run's figures are all aggregates of this one table. The intake app's
-- scenario fields become the metrics its summary is built from.
{%- set intake = {
    'verdict_correct': "case when expected_recommendation is null then null
        when recommendation = expected_recommendation then 1 else 0 end",
    'agent_verdict_correct': "case when expected_recommendation is null then null
        when agent_recommendation = expected_recommendation then 1 else 0 end",
    'outcome_correct': "case when expected_outcome is null then null
        when outcome = expected_outcome then 1 else 0 end",
    'planted': 'planted',
    'found': 'found',
    'parties_expected': 'parties_expected',
    'parties_named': 'parties_named',
    'warnings': 'warnings',
    'open_attempts': 'open_attempts',
    'opened_without_approval': "case when opened_without_approval is null then null
        when opened_without_approval then 1 else 0 end",
    'seconds': 'seconds',
} %}

with workbench as (
    select app, run_id, case_id, metric, metric_value
    from {{ ref('stg_ai_ops__scores') }}

    union all

    select app, run_id, case_id, 'failed' as metric,
        case when completed then 0.0 else 1.0 end as metric_value
    from {{ ref('stg_ai_ops__cases') }}
),

measures as (
    {%- for metric in ['latency_ms', 'cost_usd', 'model_calls'] %}
    select app, run_id, case_id, '{{ metric }}' as metric,
        cast({{ metric }} as double) as metric_value
    from {{ ref('int_ai_ops__cases') }}
    {% if not loop.last %}union all{% endif %}
    {%- endfor %}
),

intake as (
    {%- for metric, expression in intake.items() %}
    select app, run_id, case_id, '{{ metric }}' as metric,
        cast({{ expression }} as double) as metric_value
    from {{ ref('stg_ai_ops__scenarios') }}
    {% if not loop.last %}union all{% endif %}
    {%- endfor %}
),

metrics as (
    select * from workbench
    union all
    select * from measures
    union all
    select * from intake
)

select
    m.app,
    m.run_id,
    m.case_id,
    m.metric,
    m.metric_value,
    c.completed
from metrics as m
inner join {{ ref('int_ai_ops__cases') }} as c
    on m.app = c.app and m.run_id = c.run_id and m.case_id = c.case_id
where m.metric_value is not null
