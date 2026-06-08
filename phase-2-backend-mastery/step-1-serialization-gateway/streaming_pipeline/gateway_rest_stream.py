import json
import duckdb
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="Universal Data Gateway - Async JSON Stream Spec")
DB_PATH = "/data_lake/retail_lakehouse.db"

async def json_order_generator(limit: int):
    ctx = duckdb.connect(DB_PATH, read_only=True)
    # Explicitly enforce database engine level internal memory caps
    ctx.execute("SET memory_limit = '128MB';")
    
    cursor = ctx.execute(f"""
        SELECT 
            order_id, user_id, product_id, quantity, 
            order_date::VARCHAR, partition_year, partition_month, line_item_revenue 
        FROM main.fct_orders 
        LIMIT {limit};
    """)
    
    yield '{"orders": [\n'
    first_row = True
    
    while True:
        rows = cursor.fetchmany(2000)
        if not rows:
            break
            
        for row in rows:
            record = {
                "order_id": row[0], "user_id": row[1], "product_id": row[2], "quantity": row[3],
                "order_date": row[4], "partition_year": row[5], "partition_month": row[6], "line_item_revenue": row[7]
            }
            chunk = ("" if first_row else ",\n") + json.dumps(record)
            first_row = False
            yield chunk
            
    yield '\n]}'
    ctx.close()

@app.get("/api/v1/orders/stream")
async def get_orders_stream(limit: int = 100000):
    return StreamingResponse(json_order_generator(limit), media_type="application/json")
