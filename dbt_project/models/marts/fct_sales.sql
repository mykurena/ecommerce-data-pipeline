-- Daily sales. Canceled and unavailable orders are excluded.
select
    purchased_date                                as sales_date,
    count(*)                                      as orders,
    sum(items_value)                              as items_revenue,
    sum(freight_value)                            as freight_revenue,
    safe_divide(sum(items_value), count(*))       as avg_order_value
from {{ ref('int_orders__enriched') }}
where order_status not in ('canceled', 'unavailable')
  and purchased_date is not null
group by purchased_date
