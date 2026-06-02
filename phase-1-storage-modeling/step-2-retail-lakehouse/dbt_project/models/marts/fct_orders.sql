with staging_orders as (
    select * from {{ ref('stg_orders') }}
),
staging_products as (
    select * from {{ ref('dim_products') }}
)

select
    o.order_id,
    o.user_id,
    o.product_id,
    o.quantity,
    o.order_date,
    o.partition_year,  -- References the correct alias fields mapped in stg_orders
    o.partition_month, -- References the correct alias fields mapped in stg_orders
    round(o.quantity * p.price, 2) as line_item_revenue
from staging_orders o
join staging_products p on o.product_id = p.product_id
