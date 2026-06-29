with source as (
    select * from {{ silver_delta("customers") }}
)

select
    event_id,
    event_type,
    cast(customer_id as bigint) as customer_id,
    name as customer_name,
    lower(email) as email,
    country,
    cast(signup_date as date) as signup_date,
    loyalty_tier,
    event_timestamp,
    event_date,
    source_topic,
    source_partition,
    source_offset,
    event_key,
    bronze_ingested_at,
    silver_processed_at
from source
