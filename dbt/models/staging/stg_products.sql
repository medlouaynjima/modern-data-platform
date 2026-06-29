with source as (
    select * from {{ silver_delta("products") }}
)

select
    event_id,
    event_type,
    cast(product_id as bigint) as product_id,
    sku,
    name as product_name,
    category,
    cast(price as double) as price,
    cast(cost as double) as cost,
    active,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
