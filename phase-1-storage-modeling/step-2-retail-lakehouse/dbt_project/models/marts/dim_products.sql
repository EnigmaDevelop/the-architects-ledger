select
    product_id,
    product_name,
    category,
    price
from {{ source('raw_lake', 'products') }}
