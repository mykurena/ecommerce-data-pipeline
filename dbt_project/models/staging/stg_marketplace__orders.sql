select
    marketplace_order_id,
    safe_cast(ordered_at as timestamp)                    as ordered_at,
    date(safe_cast(ordered_at as timestamp))              as order_date,
    status,
    safe_cast(units as int64)                             as units,
    safe_cast(gross_amount_brl as numeric)                as gross_amount_brl,
    safe_cast(marketplace_fee_brl as numeric)             as marketplace_fee_brl,
    shipping_state,
    _loaded_at
from {{ source('raw_marketplace', 'marketplace_orders') }}
