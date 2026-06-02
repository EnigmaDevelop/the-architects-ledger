import os
import random
import time
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta

TOTAL_ORDERS = 10_000_000
CHUNK_SIZE = 1_000_000  # Process in chunks to prevent OOM under strict memory limits
NUM_USERS = 500_000
NUM_PRODUCTS = 50_000

def generate_static_dimensions():
    """Generates and writes core dimension snapshots into the local data lake layer."""
    print("[Data Generator] Generating 500,000 users...")
    os.makedirs("data/raw/users", exist_ok=True)
    user_ids = list(range(1, NUM_USERS + 1))
    users_table = pa.Table.from_pydict({
        "user_id": user_ids,
        "email": [f"user_{i}@architects-ledger.com" for i in user_ids],
        "country": [random.choice(['US', 'TR', 'DE', 'UK', 'JP', 'NL']) for _ in user_ids],
        "updated_at": [datetime(2026, 1, 1) for _ in user_ids]
    })
    pq.write_table(users_table, "data/raw/users/users.parquet", compression="SNAPPY")

    print("[Data Generator] Generating 50,000 products...")
    os.makedirs("data/raw/products", exist_ok=True)
    product_ids = list(range(1, NUM_PRODUCTS + 1))
    products_table = pa.Table.from_pydict({
        "product_id": product_ids,
        "product_name": [f"Product_SKU_{i}" for i in product_ids],
        "category": [random.choice(['Electronics', 'Apparel', 'Home', 'Books', 'Automotive']) for _ in product_ids],
        "price": [round(random.uniform(5.0, 2000.0), 2) for _ in product_ids],
        "updated_at": [datetime(2026, 1, 1) for _ in product_ids]
    })
    pq.write_table(products_table, "data/raw/products/products.parquet", compression="SNAPPY")

def generate_partitioned_orders():
    """Generates 10 million orders and chunks them directly into Hive-style partitioned layers."""
    print(f"[Data Generator] Generating {TOTAL_ORDERS} streaming orders partitioned by date...")
    os.makedirs("data/raw/orders", exist_ok=True)
    base_date = datetime(2026, 1, 1)
    
    for chunk_idx in range(0, TOTAL_ORDERS, CHUNK_SIZE):
        t0 = time.time()
        chunk_orders = CHUNK_SIZE if chunk_idx + CHUNK_SIZE <= TOTAL_ORDERS else TOTAL_ORDERS - chunk_idx
        
        # Simulate orders spread across a 5-month timeline (150 days)
        days_offsets = [random.randint(0, 149) for _ in range(chunk_orders)]
        order_dates = [base_date + timedelta(days=offset, seconds=random.randint(0, 86399)) for offset in days_offsets]
        
        # Fixed format code to %m for correct Month numbers (01-05) instead of Minutes (%M)
        years = [d.strftime('%Y') for d in order_dates]
        months = [d.strftime('%m') for d in order_dates]

        orders_chunk_table = pa.Table.from_pydict({
            "order_id": list(range(chunk_idx + 1, chunk_idx + chunk_orders + 1)),
            "user_id": [random.randint(1, NUM_USERS) for _ in range(chunk_orders)],
            "product_id": [random.randint(1, NUM_PRODUCTS) for _ in range(chunk_orders)],
            "quantity": [random.randint(1, 5) for _ in range(chunk_orders)],
            "order_date": order_dates,
            "year": years,
            "month": months
        })
        
        # Write dataset using native PyArrow Dataset API for strict Hive partitioning simulation
        pq.write_to_dataset(
            orders_chunk_table,
            root_path="data/raw/orders",
            partition_cols=["year", "month"],
            compression="SNAPPY",
            use_dictionary=True
        )
        print(f"Processed Chunk [{chunk_idx + chunk_orders}/{TOTAL_ORDERS}] in {time.time() - t0:.2f} seconds.")

if __name__ == "__main__":
    start_time = time.time()
    generate_static_dimensions()
    generate_partitioned_orders()
    print(f"\n[Data Lake Matured] 10,000,000 Rows serialized into Parquet in {time.time() - start_time:.2f} seconds.")
