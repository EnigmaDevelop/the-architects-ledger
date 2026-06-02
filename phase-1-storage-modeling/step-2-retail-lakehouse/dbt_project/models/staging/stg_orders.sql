select
    order_id::int as order_id,
    user_id::int as user_id,
    product_id::int as product_id,
    quantity::int as quantity,
    order_date::timestamp as order_date,
    year as partition_year,
    month as partition_month
from {{ source('raw_lake', 'orders') }}
