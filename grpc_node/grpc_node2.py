import grpc
from concurrent import futures
import network_pb2
import network_pb2_grpc
import time

class NetworkService(network_pb2_grpc.NetworkServiceServicer):
    def __init__(self, local_address, version):
        self.local_address = local_address
        self.version = version
        self.peers = set()

    def RegisterPeer(self, request, context):
        self.peers.add(request.address)
        return network_pb2.PeerResponse(peers=list(self.peers))

    def GetPeers(self, request, context):
        return network_pb2.PeerResponse(peers=list(self.peers))

    def GetNodeInfo(self, request, context):
        return network_pb2.NodeInfoResponse(version=self.version, state="active")


def run_server(local_address, version):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = NetworkService(local_address, version)
    network_pb2_grpc.add_NetworkServiceServicer_to_server(servicer, server)
    server.add_insecure_port(local_address)
    server.start()
    print(f"Server started on {local_address}")
    return server, servicer


def register_with_peers(stub, local_address):
    response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address))
    return response.peers

def get_peers(stub):
    response = stub.GetPeers(network_pb2.PeerRequest())
    return response.peers

def connect_to_peers(servicer, initial_peers):
    for address in initial_peers:
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        try:
            # Регистрируемся на узле
            peers = register_with_peers(stub, servicer.local_address)
            print(f"Registered on {address}, current peers: {peers}")
            # Получаем список пиров от узла
            peers = get_peers(stub)
            print(f"Peers from {address}: {peers}")
            servicer.peers.update(peers)
        except grpc.RpcError as e:
            print(f"Failed to connect or register to {address}: {e}")

def get_node_info(stub):
    response = stub.GetNodeInfo(network_pb2.NodeInfoRequest())
    return response.version, response.state


def connect_to_peers(servicer, initial_peers):
    for address in initial_peers:
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        try:
            peers = register_with_peers(stub, servicer.local_address)
            print(f"Registered on {address}, current peers: {peers}")
            version, state = get_node_info(stub)
            print(f"Node {address} - Version: {version}, State: {state}")
            servicer.peers.update(peers)
        except grpc.RpcError as e:
            print(f"Failed to connect or register to {address}: {e}")

def main():
    local_address = 'localhost:50052'
    version = "1.0"
    initial_peers = ['localhost:50051']

    server, servicer = run_server(local_address, version)

    try:
        if initial_peers:
            connect_to_peers(servicer, initial_peers)

        while True:
            time.sleep(30)
            new_peers = list(servicer.peers)
            connect_to_peers(servicer, new_peers)
    except KeyboardInterrupt:
        server.stop(0)
        print("Server stopped")

if __name__ == '__main__':
    main()