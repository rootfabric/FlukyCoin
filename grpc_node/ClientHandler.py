import grpc
import network_pb2
import network_pb2_grpc

def register_with_peers(stub, local_address):
    response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address))
    return response.peers

def get_peers(stub):
    response = stub.GetPeers(network_pb2.PeerRequest())
    return response.peers

def get_node_info(stub):
    response = stub.GetNodeInfo(network_pb2.NodeInfoRequest())
    # print("response", response)

    return response.version, response.state

class ClientHandler:
    def __init__(self, servicer):
        self.servicer = servicer

    def connect_to_peers(self, initial_peers):
        for address in initial_peers:
            channel = grpc.insecure_channel(address)
            stub = network_pb2_grpc.NetworkServiceStub(channel)
            try:
                peers = register_with_peers(stub, self.servicer.local_address)
                print(f"Registered on {address}, current peers: {peers}")
                version, state = get_node_info(stub)
                print(f"Node {address} - Version: {version}, State: {state}")
                self.servicer.peers.update(peers)
            except grpc.RpcError as e:
                print(f"Failed to connect or register to {address}: {e}")
