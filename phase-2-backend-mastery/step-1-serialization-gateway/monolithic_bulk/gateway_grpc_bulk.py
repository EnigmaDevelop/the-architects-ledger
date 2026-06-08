import os
import sys
import asyncio
import duckdb
import grpc

# Explicitly append the application root to sys.path to eliminate container import serialization errors
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import proto.orders_pb2 as orders_pb2
import proto.orders_pb2_grpc as orders_pb2_grpc

DB_PATH = "/data_lake/retail_lakehouse.db"

class OrderGatewayServicer(orders_pb2_grpc.OrderGatewayServicer):
    
    async def GetOrdersBulk(self, request, context):
        print(f"[gRPC Bulk Server] Processing request for {request.record_count} records.")
        ctx = duckdb.connect(DB_PATH, read_only=True)
        raw_data = ctx.execute(f"""
            SELECT 
                order_id, user_id, product_id, quantity, 
                order_date::VARCHAR, partition_year, partition_month, line_item_revenue 
            FROM main.fct_orders 
            LIMIT {request.record_count};
        """).fetchall()
        ctx.close()
        
        protobuf_rows = [
            orders_pb2.OrderRow(
                order_id=int(row[0]), user_id=int(row[1]), product_id=int(row[2]), quantity=int(row[3]),
                order_date=str(row[4]), partition_year=str(row[5]), partition_month=str(row[6]), line_item_revenue=float(row[7])
            )
            for row in raw_data
        ]

        return orders_pb2.OrderResponse(orders=protobuf_rows)

async def serve():
    server = grpc.aio.server(options=[
        ('grpc.max_send_message_length', 100 * 1024 * 1024)
    ])
    orders_pb2_grpc.add_OrderGatewayServicer_to_server(OrderGatewayServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("[gRPC Bulk Server] Listening on port 50051...")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
