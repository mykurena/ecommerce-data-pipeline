-- One row per real customer (customer_unique_id), with order history.
with customer_orders as (
    select
        c.customer_unique_id,
        c.city,
        c.state,
        o.order_id,
        o.purchased_at,
        o.order_status,
        o.items_value
    from {{ ref('stg_olist__customers') }} as c
    inner join {{ ref('int_orders__enriched') }} as o
        on c.customer_id = o.customer_id
)

select
    customer_unique_id,
    count(distinct order_id)                                                     as order_count,
    min(purchased_at)                                                            as first_order_at,
    max(purchased_at)                                                            as last_order_at,
    sum(if(order_status in ('canceled', 'unavailable'), 0, items_value))         as total_items_spent,
    array_agg(city  ignore nulls order by purchased_at desc limit 1)[safe_offset(0)] as last_city,
    array_agg(state ignore nulls order by purchased_at desc limit 1)[safe_offset(0)] as last_state,
    count(distinct order_id) > 1                                                 as is_repeat_customer
from customer_orders
group by customer_unique_id
