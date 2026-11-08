-- Grain: one row per figure a run's summary published that the
-- warehouse can rebuild from case rows, with both values side by side.
-- A test fails the build when any pair differs by more than rounding.
with mapping as (
    select * from {{ ref('published_metrics') }}
),

published as (
    select
        s.app,
        s.run_id,
        r.run_format,
        s.published_metric,
        s.published_value
    from {{ ref('stg_ai_ops__summaries') }} as s
    inner join {{ ref('stg_ai_ops__runs') }} as r
        on s.app = r.app and s.run_id = r.run_id
),

matched as (
    select
        p.app,
        p.run_id,
        p.published_metric,
        p.published_value,
        case when m.metric = '*' then p.published_metric else m.metric end as metric,
        m.denominator,
        m.aggregate,
        m.completed_only,
        m.tolerance,
        row_number() over (
            partition by p.app, p.run_id, p.published_metric
            order by case when m.published_metric = '*' then 1 else 0 end
        ) as preference
    from published as p
    inner join mapping as m
        on p.run_format = m.run_format and m.published_metric in (p.published_metric, '*')
),

targets as (
    select * from matched where preference = 1
),

rebuilt as (
    select
        t.app,
        t.run_id,
        t.published_metric,
        t.aggregate,
        case t.aggregate
            when 'mean' then avg(case when c.metric = t.metric then c.metric_value end)
            when 'sum' then sum(case when c.metric = t.metric then c.metric_value end)
            when 'count' then count(case when c.metric = t.metric then c.metric_value end)
            when 'ratio' then sum(case when c.metric = t.metric then c.metric_value end)
                / nullif(sum(case when c.metric = t.denominator then c.metric_value end), 0)
            when 'p50' then percentile_disc(0.5) within group (
                order by case when c.metric = t.metric then c.metric_value end)
            when 'p95' then percentile_disc(0.95) within group (
                order by case when c.metric = t.metric then c.metric_value end)
        end as warehouse_value
    from targets as t
    inner join {{ ref('int_ai_ops__case_metrics') }} as c
        on t.app = c.app
        and t.run_id = c.run_id
        and c.metric in (t.metric, coalesce(t.denominator, t.metric))
        and (not t.completed_only or coalesce(c.completed, true))
    group by t.app, t.run_id, t.published_metric, t.aggregate
)

select
    {{ surrogate_key(['t.app', 't.run_id']) }} as run_key,
    t.app,
    t.run_id,
    t.published_metric,
    t.metric,
    t.aggregate,
    t.published_value,
    b.warehouse_value,
    b.warehouse_value - t.published_value as difference,
    t.tolerance,
    abs(b.warehouse_value - t.published_value) <= t.tolerance as matches
from targets as t
left join rebuilt as b
    on t.app = b.app and t.run_id = b.run_id and t.published_metric = b.published_metric
