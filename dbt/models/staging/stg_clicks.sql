with source as (
    select * from {{ silver_delta("clicks") }}
)

select
    event_id,
    event_type,
    session_id,
    cast(customer_id as bigint) as customer_id,
    cast(product_id as bigint) as product_id,
    device,
    country,
    referrer,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
