import network_pb2
import network_pb2_grpc
import datetime

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
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return network_pb2.NodeInfoResponse(version=self.version, state="active", current_time=current_time)