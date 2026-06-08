import os
import sys
import asyncio
import duckdb
import grpc

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import proto.orders_pb2 as orders_pb2
import proto.orders_pb2_grpc as orders_pb2_grpc

DB_PATH = "/data_lake/retail_lakehouse.db"

class OrderGatewayServicer(orders_pb2_grpc.OrderGatewayServicer):
    
    async def GetOrdersStream(self, request, context):
        print(f"[gRPC Stream Server] Active streaming pipeline for {request.record_count} records.")
        ctx = duckdb.connect(DB_PATH, read_only=True)
        
        cursor = ctx.execute(f"""
            SELECT 
                order_id, user_id, product_id, quantity, 
                order_date::VARCHAR, partition_year, partition_month, line_item_revenue 
            FROM main.fct_orders 
            LIMIT {request.record_count};
        """)
        
        while True:
            rows = cursor.fetchmany(2000)
            if not rows:
                break
                
            for row in rows:
                yield orders_pb2.OrderRow(
                    order_id=int(row[0]), user_id=int(row[1]), product_id=int(row[2]), quantity=int(row[3]),
                    order_date=str(row[4]), partition_year=str(row[5]), partition_month=str(row[6]), line_item_revenue=float(row[7])
                )

        ctx.close()

async def serve():
    server = grpc.aio.server()
    orders_pb2_grpc.add_OrderGatewayServicer_to_server(OrderGatewayServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("[gRPC Stream Server] Listening on port 50052...")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
