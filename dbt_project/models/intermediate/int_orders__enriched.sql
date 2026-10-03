-- One row per order with item and payment totals and delivery status.
select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchased_at,
    date(o.purchased_at)                         as purchased_date,
    o.delivered_to_customer_at,
    o.estimated_delivery_at,
    coalesce(i.item_count, 0)                    as item_count,
    coalesce(i.items_value, 0)                   as items_value,
    coalesce(i.freight_value, 0)                 as freight_value,
    coalesce(p.payment_value, 0)                 as payment_value,
    o.delivered_to_customer_at > o.estimated_delivery_at as is_delivered_late
from {{ ref('stg_olist__orders') }} as o
left join {{ ref('int_orders__items') }} as i
    on o.order_id = i.order_id
left join {{ ref('int_orders__payments') }} as p
    on o.order_id = p.order_id
