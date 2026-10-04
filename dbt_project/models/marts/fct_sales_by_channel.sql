-- Daily sales for both channels: Olist (direct store) and the marketplace feed.
-- Canceled, unavailable and returned orders are excluded.
with olist as (
    select
        purchased_date              as sales_date,
        'olist'                     as channel,
        count(*)                    as orders,
        sum(items_value)            as gross_revenue
    from {{ ref('int_orders__enriched') }}
    where order_status not in ('canceled', 'unavailable')
      and purchased_date is not null
    group by purchased_date
),

marketplace as (
    select
        order_date                  as sales_date,
        'marketplace'               as channel,
        count(*)                    as orders,
        sum(gross_amount_brl)       as gross_revenue
    from {{ ref('stg_marketplace__orders') }}
    where status not in ('cancelled', 'returned')
      and order_date is not null
    group by order_date
),

unioned as (
    select * from olist
    union all
    select * from marketplace
)

select
    concat(cast(sales_date as string), '|', channel)   as sales_id,
    sales_date,
    channel,
    orders,
    gross_revenue,
    safe_divide(gross_revenue, orders)                 as avg_order_value
from unioned
