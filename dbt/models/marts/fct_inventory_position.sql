{{ config(location_root=var("gold_path")) }}

with inventory as (
    select * from {{ ref("stg_inventory") }}
),

ranked_inventory as (
    select
        *,
        row_number() over (
            partition by product_id, warehouse_id
            order by event_timestamp desc, source_offset desc
        ) as inventory_rank
    from inventory
)

select
    product_id,
    warehouse_id,
    available_quantity,
    quantity_delta as latest_quantity_delta,
    reason as latest_reason,
    event_timestamp as latest_inventory_timestamp,
    event_date as latest_inventory_date
from ranked_inventory
where inventory_rank = 1
