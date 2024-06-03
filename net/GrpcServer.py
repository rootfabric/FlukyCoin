import grpc
from concurrent import futures
from protos import network_pb2_grpc
from net.NetworkService import NetworkService

class GrpcServer:
    def __init__(self, local_address, version, node_manager):
        self.local_address = local_address
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = NetworkService(local_address, version, node_manager)
        network_pb2_grpc.add_NetworkServiceServicer_to_server(self.servicer, self.server)
        self.server.add_insecure_port(local_address)

    def start(self):
        self.server.start()
        print(f"Server started on {self.local_address}")

    def stop(self):
        self.server.stop(0)
        print("Server stopped")
