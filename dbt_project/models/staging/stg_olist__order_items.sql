select
    order_id,
    safe_cast(order_item_id as int64)               as order_item_id,
    product_id,
    seller_id,
    safe_cast(shipping_limit_date as timestamp)     as shipping_limit_at,
    safe_cast(price as numeric)                     as price,
    safe_cast(freight_value as numeric)             as freight_value
from {{ source('raw', 'olist_order_items') }}
