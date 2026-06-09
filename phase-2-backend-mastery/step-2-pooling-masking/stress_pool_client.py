import asyncio
import time
import random
import numpy as np
import httpx

TARGET_URL = "http://localhost:8002/api/v1/users/stream?limit=5000"
CONCURRENT_REQUESTS = 40  # Blasting 40 concurrent lines over a max_size=20 server pool
ITERATIONS_PER_LOOP = 5

async def execute_async_inbound_request(client: httpx.AsyncClient, request_id: int):
    """
    Simulates an isolated microservice client worker pulling chunked data profiles.
    Dynamically alternates between roles to stress the masking filter pipelines.
    """
    role = "Admin" if request_id % 2 == 0 else "Analyst"
    headers = {"X-Role": role}
    
    t0 = time.time()
    try:
        row_count = 0
        # Open an async stream socket connection straight down the gateway bridge
        async with client.stream("GET", TARGET_URL, headers=headers, timeout=60.0) as response:
            if response.status_code == 200:
                async for line in response.aiter_lines():
                    if line.strip():
                        row_count += 1
                latency = time.time() - t0
                return {"success": True, "latency": latency, "rows": row_count, "role": role}
            else:
                return {"success": False, "error_code": response.status_code}
    except Exception as e:
        return {"success": False, "error_msg": str(e)}

async def run_concurrent_stress_wave():
    print(f"=== Initiating Async Pooling & Masking Stress Pipeline ===")
    print(f"Target Concurrency Level: {CONCURRENT_REQUESTS} Simultaneous Connections")
    print(f"Database Pool Configuration Capacity: min_size=10, max_size=20")
    
    all_latencies = []
    success_count = 0
    failure_count = 0
    
    # Configure high-capacity async connection pools on the client side
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    
    async with httpx.AsyncClient(limits=limits) as client:
        # Construct the execution task array to blast the servers concurrently
        tasks = [execute_async_inbound_request(client, i) for i in range(CONCURRENT_REQUESTS)]
        
        t_start = time.time()
        # Fire all 40 concurrent lines into the single core container simultaneously
        results = await asyncio.gather(*tasks)
        total_wall_time = time.time() - t_start
        
        for res in results:
            if res.get("success"):
                success_count += 1
                all_latencies.append(res["latency"])
            else:
                failure_count += 1
                print(f"  -> [Inbound Line Drop] Failure Signature: {res.get('error_msg', res.get('error_code'))}")
                
    print("\n" + "="*60)
    print("📋 STRESS TEST CONCURRENCY MATRIX RESULTS")
    print("="*60)
    print(f"Total Successful Transactions Processed: {success_count}/{CONCURRENT_REQUESTS}")
    print(f"Total Server Block Failures Registered: {failure_count}")
    print(f"Total Wall Execution Time (Throughput Window): {total_wall_time:.4f} seconds")
    
    if all_latencies:
        latencies_ms = np.array(all_latencies) * 1000
        p50 = np.percentile(latencies_ms, 50)
        p95 = np.percentile(latencies_ms, 95)
        p99 = np.percentile(latencies_ms, 99)
        variance = np.var(latencies_ms)
        
        print(f"\n📈 Statistical Network Latency Percentiles (Population N={len(all_latencies)})")
        print(f"  -> p50 (Median): {p50:.2f} ms")
        print(f"  -> p95 (Tail):   {p95:.2f} ms")
        print(f"  -> p99 (Peak):   {p99:.2f} ms")
        print(f"  -> Statistical Population Variance (σ²): {variance:.4f} ms²")

if __name__ == "__main__":
    # Ensure correct event loop execution path across cross-platform OS grids
    asyncio.run(run_concurrent_stress_wave())
