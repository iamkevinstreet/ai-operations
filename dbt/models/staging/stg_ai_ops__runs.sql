-- Grain: one row per run file an app committed, at its pinned commit.
-- A live run is one a real model answered; the offline stand-in's
-- provider is "fake", and retrieval runs call no model.
select
    app,
    run_id,
    run_format,
    run_name,
    model,
    provider,
    coalesce(provider not in ('fake'), false) as is_live,
    prices_as_of,
    cast(run_at as timestamp) as run_at,
    cast(started_at as timestamp) as started_at,
    cast(finished_at as timestamp) as finished_at,
    cases,
    failures,
    run_file,
    source_commit,
    source_blob_sha,
    cast(loaded_at as timestamp) as loaded_at
from {{ source('ai_ops', 'runs') }}
