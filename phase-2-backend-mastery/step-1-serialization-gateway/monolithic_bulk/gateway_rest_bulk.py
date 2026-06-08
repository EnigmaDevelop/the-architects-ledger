import duckdb
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Universal Data Gateway - Monolithic REST Bulk Spec")
DB_PATH = "/data_lake/retail_lakehouse.db"

class OrderRowModel(BaseModel):
    order_id: int
    user_id: int
    product_id: int
    quantity: int
    order_date: str
    partition_year: str
    partition_month: str
    line_item_revenue: float

class BulkOrderResponse(BaseModel):
    orders: List[OrderRowModel]

@app.get("/api/v1/orders/bulk", response_model=BulkOrderResponse)
async def get_orders_bulk(limit: int = 100000):
    ctx = duckdb.connect(DB_PATH, read_only=True)
    raw_data = ctx.execute(f"""
        SELECT 
            order_id, user_id, product_id, quantity, 
            order_date::VARCHAR, partition_year, partition_month, line_item_revenue 
        FROM main.fct_orders 
        LIMIT {limit};
    """).fetchall()
    ctx.close()
    
    orders_list = [
        OrderRowModel(
            order_id=row[0], user_id=row[1], product_id=row[2], quantity=row[3],
            order_date=row[4], partition_year=row[5], partition_month=row[6], line_item_revenue=row[7]
        )
        for row in raw_data
    ]
    return BulkOrderResponse(orders=orders_list)
