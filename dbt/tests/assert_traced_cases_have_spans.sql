-- Every case of a run that committed a trace has spans in it. A row
-- here means a trace file is missing cases, so its run's latency and
-- token figures would cover only part of the run.
with traced_runs as (
    select distinct run_key
    from {{ ref('fct_eval_cases') }} as c
    where exists (
        select 1
        from {{ ref('fct_spans') }} as s
        where s.app = c.app and s.run_id = c.run_id
    )
)

select
    c.case_key,
    c.app,
    c.run_id,
    c.case_id
from {{ ref('fct_eval_cases') }} as c
inner join traced_runs as t
    on c.run_key = t.run_key
where not exists (
    select 1
    from {{ ref('fct_spans') }} as s
    where s.case_key = c.case_key
)
