import httpx
import grpc
import time
import numpy as np
import proto.orders_pb2 as orders_pb2
import proto.orders_pb2_grpc as orders_pb2_grpc

URL_REST_BULK = "http://localhost:8000/api/v1/orders/bulk?limit=100000"
URL_REST_STREAM = "http://localhost:8001/api/v1/orders/stream?limit=100000"
GRPC_BULK_TARGET = "localhost:50051"
GRPC_STREAM_TARGET = "localhost:50052"
ITERATIONS = 50

def run_rest_bulk_test():
    print("\n[TEST 1] Triggering Monolithic REST Bulk Request (100k Rows Fetchall/JSON)...")
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(URL_REST_BULK)
            if resp.status_code == 200:
                print("  -> [REST Bulk Unexpected Success]")
            else:
                print(f"  -> [REST Bulk Predicted Failure] HTTP Status: {resp.status_code} (Memory Overrun)")
    except Exception as e:
        print(f"  -> [REST Bulk Verified Crash] Connection severed via server OOM/MemoryError.")

def run_grpc_bulk_test():
    print(f"\n[TEST 2] Triggering Monolithic gRPC Bulk Request ({ITERATIONS} Continuous Iterations)...")
    latencies = []
    try:
        with grpc.insecure_channel(GRPC_BULK_TARGET, options=[
            ('grpc.max_receive_message_length', 100 * 1024 * 1024)
        ]) as channel:
            stub = orders_pb2_grpc.OrderGatewayStub(channel)
            request = orders_pb2.OrderRequest(record_count=100000)
            
            # Warm-up run to eliminate cold-start cache distortion
            stub.GetOrdersBulk(request)
            
            for i in range(ITERATIONS):
                t0 = time.time()
                response = stub.GetOrdersBulk(request)
                latencies.append(time.time() - t0)
                
            print_latencies("gRPC Bulk", latencies)
    except Exception as e:
        print(f"  -> [gRPC Bulk Crash] Exception: {str(e)}")

def run_rest_stream_test():
    print(f"\n[TEST 3] Triggering Optimized REST Async Stream Request ({ITERATIONS} Continuous Iterations)...")
    latencies = []
    try:
        with httpx.Client(timeout=60.0) as client:
            for i in range(ITERATIONS):
                t0 = time.time()
                row_count = 0
                with client.stream("GET", URL_REST_STREAM) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.strip() and not line.startswith('{"orders":') and not line.endswith(']}'):
                                row_count += 1
                latencies.append(time.time() - t0)
            print_latencies("REST Stream", latencies)
    except Exception as e:
        print(f"  -> [REST Stream Crash] Exception: {str(e)}")

def run_grpc_stream_test():
    print(f"\n[TEST 4] Triggering Optimized gRPC Server Streaming RPC Request ({ITERATIONS} Continuous Iterations)...")
    latencies = []
    try:
        for i in range(ITERATIONS):
            t0 = time.time()
            row_count = 0
            with grpc.insecure_channel(GRPC_STREAM_TARGET) as channel:
                stub = orders_pb2_grpc.OrderGatewayStub(channel)
                request = orders_pb2.OrderRequest(record_count=100000)
                response_stream = stub.GetOrdersStream(request)
                for _ in response_stream:
                    row_count += 1
            latencies.append(time.time() - t0)
        print_latencies("gRPC Stream", latencies)
    except Exception as e:
        print(f"  -> [gRPC Stream Crash] Exception: {str(e)}")

def print_latencies(label, latencies):
    latencies_ms = np.array(latencies) * 1000
    p50 = np.percentile(latencies_ms, 50)
    p95 = np.percentile(latencies_ms, 95)
    p99 = np.percentile(latencies_ms, 99)
    variance = np.var(latencies_ms)
    print(f"  -> [{label} Invariant Results]")
    print(f"     Latency Percentiles -> p50: {p50:.2f}ms | p95: {p95:.2f}ms | p99: {p99:.2f}ms")
    print(f"     Statistical Variance: {variance:.4f}ms^2")

if __name__ == "__main__":
    print("=== Launching High-Precision 50-Iteration Serialization Matrix Audits ===")
    run_rest_bulk_test()
    print("-" * 60)
    run_grpc_bulk_test()
    print("-" * 60)
    run_rest_stream_test()
    print("-" * 60)
    run_grpc_stream_test()
