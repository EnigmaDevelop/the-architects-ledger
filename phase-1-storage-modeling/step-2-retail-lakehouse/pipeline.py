import duckdb
import time

def run_in_process_benchmarks():
    """
    Initializes a volatile, in-memory DuckDB connection to benchmark 
    columnar vectorized reads directly over partitioned Parquet files.
    """
    print("--- Starting In-Process Compute Audit (DuckDB Vectorized Engine) ---")
    
    # Initialize a clean, local file-based database metadata connection
    ctx = duckdb.connect("retail_lakehouse.db")
    
    # Create virtual view references pointing directly to partitioned raw data lake files
    print("[DuckDB] Registering virtual storage layouts over Parquet footprints...")
    ctx.execute("CREATE OR REPLACE VIEW raw_users AS SELECT * FROM read_parquet('data/raw/users/*.parquet');")
    ctx.execute("CREATE OR REPLACE VIEW raw_products AS SELECT * FROM read_parquet('data/raw/products/*.parquet');")
    
    # Leveraging Hive-style partitioning auto-discovery for the 10 million orders
    ctx.execute("CREATE OR REPLACE VIEW raw_orders AS SELECT * FROM read_parquet('data/raw/orders/*/*/*.parquet', hive_partitioning=True);")
    
    print("[DuckDB] Virtual metadata schema mapped successfully.")
    
    # ------------------------------------------------------------------------
    # BENCHMARK SCENARIO 1: Global Scan (Un-pruned Heavy Aggregation)
    # Calculates global revenue metrics across the entire 10 million order history.
    # ------------------------------------------------------------------------
    print("\n[Benchmark 1] Executing Global Scan (Full Data Lake Survey)...")
    t0 = time.time()
    global_res = ctx.execute("""
        SELECT 
            p.category,
            SUM(o.quantity) as total_quantity,
            ROUND(SUM(o.quantity * p.price), 2) as total_revenue
        FROM raw_orders o
        JOIN raw_products p ON o.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_revenue DESC;
    """).fetchall()
    
    global_latency = time.time() - t0
    print("Global Aggregation Results:")
    for row in global_res:
        print(f"  Category: {row[0]:<15} | Qty: {row[1]:<8} | Revenue: ${row[2]:,}")
    print(f"Global Scan Execution Time: {global_latency:.4f} seconds.")
    
    # ------------------------------------------------------------------------
    # BENCHMARK SCENARIO 2: Directory Pruning Scan (Targeted Partition)
    # Scans ONLY month=03 to analyze DuckDB's native execution path exclusion.
    # ------------------------------------------------------------------------
    print("\n[Benchmark 2] Executing Targeted Partition Scan (Month=03 Directory Pruning)...")
    t0 = time.time()
    pruned_res = ctx.execute("""
        SELECT 
            p.category,
            SUM(o.quantity) as target_quantity
        FROM raw_orders o
        JOIN raw_products p ON o.product_id = p.product_id
        WHERE o.month = '03'  -- Explicit filter to trigger pyarrow/duckdb directory skipping
        GROUP BY p.category
        ORDER BY target_quantity DESC;
    """).fetchall()
    
    pruned_latency = time.time() - t0
    print("Targeted Month=03 Aggregation Results:")
    for row in pruned_res:
        print(f"  Category: {row[0]:<15} | Target Qty: {row[1]}")
    print(f"Directory Pruned Scan Execution Time: {pruned_latency:.4f} seconds.")
    
    ctx.close()

if __name__ == "__main__":
    run_in_process_benchmarks()
