-- Grain: one row per app, with the metric its runs are judged by.
select
    app,
    title,
    primary_metric,
    primary_metric_label,
    repository_url
from {{ ref('apps') }}
