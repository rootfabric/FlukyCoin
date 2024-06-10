import grpc
from concurrent import futures
from protos import network_pb2_grpc
from net.NetworkService import NetworkService

class GrpcServer:
    def __init__(self, config, node_manager):

        self.config = config
        self.address = f"{self.config.get('host')}:{self.config.get('port')}"
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = NetworkService(self.config, node_manager)
        network_pb2_grpc.add_NetworkServiceServicer_to_server(self.servicer, self.server)
        self.server.add_insecure_port(self.address)

    def start(self):
        self.server.start()
        print(f"Server started on {self.address}")

    def stop(self):
        self.server.stop(0)
        print("Server stopped")
