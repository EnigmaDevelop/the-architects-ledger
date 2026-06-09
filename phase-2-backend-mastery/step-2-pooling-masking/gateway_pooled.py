import json
import logging
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GatewayPooled")

DB_DSN = "postgres://ledger_admin:secure_vault_password@gateway_transactional_postgres:5432/core_transactional_db"
db_pool = None

async def initialize_database_records(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                email VARCHAR(100),
                credit_card VARCHAR(30),
                country VARCHAR(5),
                risk_score DOUBLE PRECISION
            );
        """)
        row_check = await conn.fetchval("SELECT COUNT(*) FROM users;")
        if row_check >= 100000:
            return

        chunk_size = 20000
        total_records = 100000
        countries = ['US', 'TR', 'DE', 'UK', 'JP', 'NL']
        
        for chunk_idx in range(0, total_records, chunk_size):
            records = []
            for i in range(chunk_idx + 1, chunk_idx + chunk_size + 1):
                records.append((
                    f"customer_id_{i}",
                    f"user_profile_{i}@architects-ledger.com",
                    f"4532-8871-9923-{1000 + (i % 8999)}",
                    countries[i % len(countries)],
                    float(round(0.1 + (i % 9) * 0.11, 2))
                ))
            await conn.executemany("""
                INSERT INTO users (username, email, credit_card, country, risk_score)
                VALUES ($1, $2, $3, $4, $5);
            """, records)

async def async_masked_user_generator(pool: asyncpg.Pool, mask_data: bool, limit: int):
    """
    Explicit connection management layer bypassing implicitly closed context handlers.
    Guarantees the TCP handle remains active across the entire FastAPI Streaming lifecycle.
    """
    # Manually acquire the network handle straight from the global pool allocation grid
    conn = await pool.acquire()
    try:
        await conn.execute("SET work_mem = '64MB';")
        
        # Enforce explicit transactional block to preserve cursor operational lifespan
        async with conn.transaction():
            async for row in conn.cursor(f"""
                SELECT user_id, username, email, credit_card, country, risk_score 
                FROM users 
                LIMIT {limit};
            """):
                raw_email = row["email"]
                raw_cc = row["credit_card"]
                
                if mask_data:
                    at_idx = raw_email.find("@")
                    masked_email = raw_email[:1] + "***" + raw_email[at_idx:]
                    masked_cc = "****-****-****-" + raw_cc[-4:]
                else:
                    masked_email = raw_email
                    masked_cc = raw_cc

                record = {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "email": masked_email,
                    "credit_card": masked_cc,
                    "country": row["country"],
                    "risk_score": row["risk_score"]
                }
                yield json.dumps(record) + "\n"
    finally:
        # Enforce absolute execution guarantee: release connection back to pool frame
        await pool.release(conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            DB_DSN, min_size=10, max_size=20, max_queries=50000, command_timeout=30.0
        )
        await initialize_database_records(db_pool)
    except Exception as e:
        logger.error(f"[Gateway Startup Failure] Pool configuration aborted: {str(e)}")
        raise e
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(title="Universal Data Gateway - Pooled Architecture Core", lifespan=lifespan)

@app.get("/health")
async def health_check():
    if db_pool:
        return {"status": "healthy", "pool_free_slots": db_pool.get_size()}
    raise HTTPException(status_code=500, detail="Database connection layer uninitialized")

@app.get("/api/v1/users/stream")
async def stream_users_ledger(limit: int = 100000, x_role: str = Header(default="Analyst")):
    """
    Gateway pipeline streaming data from Postgres with role-based security enforcement.
    """
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database infrastructure offline")
        
    # Enforce role boundaries explicitly at the entrance network gate
    if x_role.lower() not in ["admin", "analyst"]:
        raise HTTPException(status_code=403, detail="Access Denied: Invalid Authorization Credentials")
        
    # Determine masking toggle dynamically via role taxonomy
    apply_masking = True if x_role.lower() == "analyst" else False
    
    return StreamingResponse(
        async_masked_user_generator(db_pool, apply_masking, limit), 
        media_type="application/x-ndjson"
    )
