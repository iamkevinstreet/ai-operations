-- Grain: one row per model per version of the price list.
select
    model,
    input_per_mtok,
    output_per_mtok,
    prices_as_of,
    source_commit
from {{ source('ai_ops', 'prices') }}
