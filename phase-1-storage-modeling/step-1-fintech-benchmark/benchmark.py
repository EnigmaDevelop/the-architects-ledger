import asyncio
import time
import uuid6
import random
import asyncpg
import aiohttp
import numpy as np
from datetime import datetime, timedelta, timezone


# Hardcore stress test scaling configuration
TOTAL_RECORDS = 5_000_000
BATCH_SIZE = 50_000
READ_ITERATIONS = 50


def generate_fintech_batch_with_time(size, start_offset_minutes):
    """
    Generates realistic sequential financial data.
    Increments time vectors alongside UUIDv7 to test logical block alignment.
    """
    batch = []
    # Fixed timezone specification by leveraging strict timezone.utc subclass
    base_time = datetime.now(timezone.utc) - timedelta(minutes=start_offset_minutes)
    for i in range(size):
        # Format as naive datetime to prevent psql client adapter casting errors
        record_time = (base_time + timedelta(milliseconds=i * 10)).replace(tzinfo=None)
        batch.append((
            str(uuid6.uuid7()),
            random.randint(10000, 99999),
            round(random.uniform(1.0, 5000.0), 2),
            random.choice(['DEBIT', 'CREDIT', 'TRANSFER']),
            'PENDING',
            record_time
        ))
    return batch


def calculate_latencies(latency_list):
    """Calculates statistical percentiles for query execution arrays."""
    latencies = np.array(latency_list) * 1000  # Convert to milliseconds
    return {
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "p99": np.percentile(latencies, 99)
    }


async def audit_postgres_btree():
    """
    Evaluates PostgreSQL performance using a standard row-oriented layout
    backed by an implicit B-Tree Primary Key index under strict memory limitations.
    """
    print("\n=== Hardcore Auditing PostgreSQL (B-Tree Layout - 5M Rows) ===")
    conn = await asyncpg.connect(
        user='fintech_admin',
        password='secret_fin_pass',
        database='fintech_analytics',
        host='127.0.0.1',
        port=5439
    )

    await conn.execute("SET work_mem = '4MB';")

    await conn.execute("DROP TABLE IF EXISTS transactions_btree;")
    await conn.execute("""
        CREATE TABLE transactions_btree (
            transaction_id UUID PRIMARY KEY,
            account_id INT NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            tx_type VARCHAR(10) NOT NULL,
            status VARCHAR(10) NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
    """)

    print("[PostgreSQL B-Tree] Ingesting 5,000,000 Rows...")
    start_time = time.time()
    for step in range(0, TOTAL_RECORDS, BATCH_SIZE):
        minutes_offset = int((TOTAL_RECORDS - step) / 1000)
        batch = generate_fintech_batch_with_time(BATCH_SIZE, minutes_offset)
        await conn.executemany("""
            INSERT INTO transactions_btree (transaction_id, account_id, amount, tx_type, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, batch)
    print(f"B-Tree Ingestion completed in: {time.time() - start_time:.2f} seconds.")

    # Perform manual database optimization after ingestion to clear dead pages
    print("[PostgreSQL B-Tree] Running Manual VACUUM FULL & ANALYZE...")
    await conn.execute("VACUUM FULL transactions_btree;")
    await conn.execute("ANALYZE transactions_btree;")

    row = await conn.fetchrow("SELECT MIN(created_at), MAX(created_at) FROM transactions_btree;")
    min_dt, max_dt = row

    # Narrow window to exactly 30 seconds for high index selectivity
    start_filter = min_dt + timedelta(minutes=10)
    end_filter = start_filter + timedelta(seconds=30)

    # Force optimizer to leverage indexes by disabling sequential scans during read benchmarks
    await conn.execute("SET enable_seqscan = off;")

    print(f"Capturing EXPLAIN (ANALYZE, BUFFERS) with Sharp Time Filter...")
    plan_records = await conn.fetch(f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
        SELECT tx_type, SUM(amount) FROM transactions_btree
        WHERE created_at BETWEEN '{start_filter}' AND '{end_filter}'
        GROUP BY tx_type;
    """)
    for record in plan_records:
        print(record)

    latencies = []
    for _ in range(READ_ITERATIONS):
        t0 = time.time()
        await conn.fetch(f"""
            SELECT tx_type, SUM(amount) FROM transactions_btree
            WHERE created_at BETWEEN '{start_filter}' AND '{end_filter}'
            GROUP BY tx_type;
        """)
        latencies.append(time.time() - t0)

    stats = calculate_latencies(latencies)
    print(f"B-Tree Aggr Latency (ms) -> p50: {stats['p50']:.2f} | p95: {stats['p95']:.2f} | p99: {stats['p99']:.2f}")
    await conn.close()
    return start_filter, end_filter


async def audit_postgres_brin(start_filter, end_filter):
    """
    Evaluates PostgreSQL performance using a raw heap layout model optimized with
    a post-ingest compiled Block Range Index (BRIN) tracking sequential chronological ranges.
    """
    print("\n=== Hardcore Auditing PostgreSQL (BRIN Layout - 5M Rows) ===")
    conn = await asyncpg.connect(
        user='fintech_admin',
        password='secret_fin_pass',
        database='fintech_analytics',
        host='127.0.0.1',
        port=5439
    )
    await conn.execute("SET work_mem = '4MB';")

    await conn.execute("DROP TABLE IF EXISTS transactions_brin;")
    await conn.execute("""
        CREATE TABLE transactions_brin (
            transaction_id UUID,
            account_id INT NOT NULL,
            amount NUMERIC(10,2) NOT NULL,
            tx_type VARCHAR(10) NOT NULL,
            status VARCHAR(10) NOT NULL,
            created_at TIMESTAMP NOT NULL
        );
    """)

    print("[PostgreSQL BRIN] Ingesting 5,000,000 Rows...")
    start_time = time.time()
    for step in range(0, TOTAL_RECORDS, BATCH_SIZE):
        minutes_offset = int((TOTAL_RECORDS - step) / 1000)
        batch = generate_fintech_batch_with_time(BATCH_SIZE, minutes_offset)
        await conn.executemany("""
            INSERT INTO transactions_brin (transaction_id, account_id, amount, tx_type, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, batch)
    print(f"BRIN Ingestion completed in: {time.time() - start_time:.2f} seconds.")

    print("[PostgreSQL BRIN] Running Manual VACUUM FULL & ANALYZE...")
    await conn.execute("VACUUM FULL transactions_brin;")
    await conn.execute("ANALYZE transactions_brin;")

    t_idx = time.time()
    # Create composite BRIN index matching our query pattern exactly
    await conn.execute("CREATE INDEX idx_tx_brin ON transactions_brin USING BRIN (created_at, tx_type);")
    print(f"BRIN Index Build Completed in: {time.time() - t_idx:.4f} seconds.")

    await conn.execute("SET enable_seqscan = off;")

    print("Capturing EXPLAIN (ANALYZE, BUFFERS) with Sharp Time Filter...")
    plan_records = await conn.fetch(f"""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
        SELECT tx_type, SUM(amount) FROM transactions_brin
        WHERE created_at BETWEEN '{start_filter}' AND '{end_filter}'
        GROUP BY tx_type;
    """)
    for record in plan_records:
        print(record)

    latencies = []
    for _ in range(READ_ITERATIONS):
        t0 = time.time()
        await conn.fetch(f"""
            SELECT tx_type, SUM(amount) FROM transactions_brin
            WHERE created_at BETWEEN '{start_filter}' AND '{end_filter}'
            GROUP BY tx_type;
        """)
        latencies.append(time.time() - t0)

    stats = calculate_latencies(latencies)
    print(f"BRIN Aggr Latency (ms) -> p50: {stats['p50']:.2f} | p95: {stats['p95']:.2f} | p99: {stats['p99']:.2f}")
    await conn.close()


async def audit_clickhouse(start_filter, end_filter):
    """
    Evaluates ClickHouse performance using a native columnar layout orchestrated
    via a specialized MergeTree index structure under identical isolation levels.
    """
    print("\n=== Hardcore Auditing ClickHouse (5M Rows) ===")
    ch_url = "http://localhost:8123/"
    headers = {
        "X-ClickHouse-User": "default",
        "X-ClickHouse-Key": ""
    }

    setup_query = """
    DROP TABLE IF EXISTS default.transactions;
    CREATE TABLE default.transactions (
        transaction_id String,
        account_id Int32,
        amount Float64,
        tx_type String,
        status String,
        created_at DateTime
    ) ENGINE = MergeTree()
    ORDER BY (created_at, tx_type);
    """

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(ch_url, data=setup_query) as resp:
            await resp.text()

        print("[ClickHouse] Ingesting 5,000,000 Rows...")
        start_time = time.time()
        for step in range(0, TOTAL_RECORDS, BATCH_SIZE):
            minutes_offset = int((TOTAL_RECORDS - step) / 1000)
            batch = generate_fintech_batch_with_time(BATCH_SIZE, minutes_offset)

            values_str = ",".join([
                f"('{tx_id}',{acc_id},{amt},'{tx_type}','{status}','{dt.strftime('%Y-%m-%d %H:%M:%S')}')"
                for tx_id, acc_id, amt, tx_type, status, dt in batch
            ])

            insert_query = (
                f"INSERT INTO default.transactions (transaction_id, account_id, amount, tx_type, status, created_at) "
                f"VALUES {values_str}"
            )
            async with session.post(ch_url, data=insert_query) as insert_resp:
                await insert_resp.text()
        print(f"ClickHouse Ingestion completed in: {time.time() - start_time:.2f} seconds.")

        ch_start = start_filter.strftime('%Y-%m-%d %H:%M:%S')
        ch_end = end_filter.strftime('%Y-%m-%d %H:%M:%S')

        latencies = []
        for _ in range(READ_ITERATIONS):
            t0 = time.time()
            query = (
                f"SELECT tx_type, sum(amount) FROM default.transactions "
                f"WHERE created_at BETWEEN '{ch_start}' AND '{ch_end}' "
                f"GROUP BY tx_type;"
            )
            async with session.post(ch_url, data=query) as read_resp:
                await read_resp.text()
            latencies.append(time.time() - t0)

        stats = calculate_latencies(latencies)
        print(f"ClickHouse Aggr Latency (ms) -> p50: {stats['p50']:.2f} | p95: {stats['p95']:.2f} | p99: {stats['p99']:.2f}")


async def main():
    print("Starting Rigorous Configured Audit Framework...")
    start_f, end_f = await audit_postgres_btree()
    print("-" * 60)
    await audit_postgres_brin(start_f, end_f)
    print("-" * 60)
    await audit_clickhouse(start_f, end_f)


if __name__ == "__main__":
    asyncio.run(main())