# Data dictionary

Models built by dbt in BigQuery. Raw tables (dataset `raw`) are loaded as-is; types are cast in the `staging` layer.

| Layer | Dataset | Materialization | Purpose |
|---|---|---|---|
| Staging | `staging` | view | Cast types, rename columns, no business logic |
| Intermediate | `intermediate` | view | Joins and aggregations reused downstream |
| Marts | `marts` | table | Business-facing facts and dimensions |

## Business rules

- **Revenue** is the sum of item prices (`price`), excluding freight.
- **Excluded orders:** Olist orders with status `canceled` or `unavailable`; marketplace orders with status `cancelled` or `returned`.
- **Customers:** Olist assigns a new `customer_id` to every order. A real customer is identified by `customer_unique_id`.
- **Currency:** all amounts are in Brazilian reais (BRL).

## Marts

### `fct_sales`

Daily sales for the Olist channel only. Grain: one row per day.

| Column | Description |
|---|---|
| `sales_date` | Order purchase date |
| `orders` | Number of orders (excluded statuses removed) |
| `items_revenue` | Sum of item prices |
| `freight_revenue` | Sum of freight values |
| `avg_order_value` | `items_revenue / orders` |

### `fct_sales_by_channel`

Daily sales for both channels. Grain: one row per day and channel.

| Column | Description |
|---|---|
| `sales_id` | Surrogate key: `date\|channel` |
| `sales_date` | Order date |
| `channel` | `olist` or `marketplace` |
| `orders` | Number of orders |
| `gross_revenue` | Olist: sum of item prices. Marketplace: gross order amount |
| `avg_order_value` | `gross_revenue / orders` |

### `dim_customers`

One row per real customer (`customer_unique_id`).

| Column | Description |
|---|---|
| `customer_unique_id` | Real customer identifier |
| `order_count` | Number of orders |
| `first_order_at` / `last_order_at` | Timestamps of first and last order |
| `total_items_spent` | Sum of item prices, excluded statuses removed |
| `last_city` / `last_state` | Location on the most recent order |
| `is_repeat_customer` | `true` if the customer has more than one order |

### `fct_ad_performance`

Daily ad performance (synthetic data). Grain: one row per day, platform and campaign.

| Column | Description |
|---|---|
| `ad_performance_id` | Surrogate key: `date\|platform\|campaign` |
| `spend_date` | Date of the spend |
| `platform` | `meta_ads` or `google_ads` |
| `campaign_name` | Campaign |
| `spend_brl` | Spend in BRL |
| `impressions`, `clicks` | Volume metrics |
| `ctr` | `clicks / impressions` |
| `cpc_brl` | `spend_brl / clicks` |

## Intermediate

### `int_orders__enriched`

One row per Olist order with item and payment totals.

| Column | Description |
|---|---|
| `order_id`, `customer_id` | Keys |
| `order_status` | Olist order status |
| `purchased_at`, `purchased_date` | Purchase timestamp and date |
| `delivered_to_customer_at`, `estimated_delivery_at` | Delivery timestamps |
| `item_count`, `items_value`, `freight_value` | Totals from order items |
| `payment_value` | Total paid |
| `is_delivered_late` | `true` if delivered after the estimated date |

`int_orders__items` and `int_orders__payments` aggregate order items and payments to one row per order.

## Staging

| Model | Source table | Notes |
|---|---|---|
| `stg_olist__orders` | `raw.olist_orders` | Timestamps cast from strings |
| `stg_olist__customers` | `raw.olist_customers` | |
| `stg_olist__order_items` | `raw.olist_order_items` | Price and freight as `NUMERIC` |
| `stg_olist__order_payments` | `raw.olist_order_payments` | |
| `stg_olist__products` | `raw.olist_products` | Joined with the English category translation |
| `stg_olist__sellers` | `raw.olist_sellers` | |
| `stg_ad_spend` | `raw.ad_spend` | Synthetic |
| `stg_marketplace__orders` | `raw.marketplace_orders` | Synthetic |

Olist reviews and geolocation are loaded into `raw` but not modeled, since no metric in this project uses them.

## Tests

- Generic tests (`unique`, `not_null`, `accepted_values`, `relationships`) are declared in the `_*.yml` files next to the models.
- Custom test: `dbt_project/tests/assert_ad_spend_not_negative.sql`.
- Failures are summarized and sent to n8n by `monitoring/run_dbt_tests.py`. See [monitoring.md](monitoring.md).
