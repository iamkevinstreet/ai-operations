-- Grain: one row per model per version of the price list, as a type 2
-- dimension: a version is valid from its as-of date until the next
-- version's, and the latest has no end.
with versions as (
    select
        model,
        input_per_mtok,
        output_per_mtok,
        prices_as_of as valid_from,
        lead(prices_as_of) over (partition by model order by prices_as_of) as valid_to,
        source_commit
    from {{ ref('stg_ai_ops__prices') }}
)

select
    {{ surrogate_key(['model', 'valid_from']) }} as price_key,
    model,
    input_per_mtok,
    output_per_mtok,
    valid_from,
    valid_to,
    valid_to is null as is_current,
    source_commit
from versions
