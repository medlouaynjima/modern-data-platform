with source as (
    select * from {{ silver_delta("inventory") }}
)

select
    event_id,
    event_type,
    inventory_event_id,
    cast(product_id as bigint) as product_id,
    warehouse_id,
    cast(quantity_delta as int) as quantity_delta,
    cast(available_quantity as int) as available_quantity,
    reason,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
