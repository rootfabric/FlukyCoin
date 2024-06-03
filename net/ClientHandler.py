import grpc
from protos import network_pb2, network_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed


def register_with_peers(stub, local_address):
    response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address))
    return response.peers


def get_peers(stub):
    response = stub.GetPeers(network_pb2.PeerRequest())
    return response.peers


# def get_node_info(stub):
#     response = stub.GetNodeInfo(network_pb2.NodeInfoRequest())
#     # print("response", response)
#
#     return response.version, response.state

class ClientHandler:
    def __init__(self, servicer):
        self.servicer = servicer
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sent_addresses = set()  # Уже отправленные адреса
        self.peer_status = {}  # Словарь статуса подключения пиров: address -> bool

    def connect_to_peers(self, initial_peers):
        # Асинхронно подключаемся к пирам
        futures = {self.executor.submit(self.connect_to_peer, address): address for address in initial_peers}
        for future in as_completed(futures):
            address = futures[future]
            try:
                future.result()
                # print(f"Successfully connected to {address}")
            except Exception as e:
                pass

    def ping_peers(self):
        """ """
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.servicer.check_active, peer): peer for peer in
                       self.servicer.known_peers}
            active_peers = {futures[future] for future in as_completed(futures) if future.result()}
            self.servicer.active_peers = active_peers
            print("Active peers updated.", active_peers)

    def connect_to_peer(self, address):
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        try:
            if address not in self.sent_addresses or not self.peer_status.get(address, False):
                self.reset_cache_for_peer(address)  # Сброс кеша при повторном подключении
                peers = register_with_peers(stub, self.servicer.local_address)
                self.sent_addresses.add(address)
                self.peer_status[address] = True  # Устанавливаем статус подключения в True
                print(f"Registered on {address}, current peers: {peers}")

                new_peers = set(peers) - self.servicer.peers
                if new_peers:
                    self.servicer.peers.update(new_peers)
                    self.resend_addresses(new_peers)

                # version, state = get_node_info(stub)
                # print(f"Node {address} - Version: {version}, State: {state}")

        except grpc.RpcError as e:
            self.peer_status[address] = False  # Устанавливаем статус подключения в False при ошибке
            raise e

    def reset_cache_for_peer(self, address):
        if address in self.sent_addresses:
            self.sent_addresses.remove(address)  # Удаляем адрес из кеша отправленных адресов

    def resend_addresses(self, new_peers):
        # Рассылка новых адресов существующим активным пирам
        for peer in new_peers:
            if peer not in self.sent_addresses:
                futures = {self.executor.submit(self.connect_to_peer, p): p for p in self.servicer.peers if p != peer}
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        pass

    def fetch_info_from_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.fetch_info, peer): peer for peer in self.servicer.active_peers}
            peer_info = {}
            for future in as_completed(futures):
                peer = futures[future]
                try:
                    info = future.result()
                    peer_info[
                        peer] = f"version: {info.version}, synced: {info.synced}, candidate: {info.block_candidate}"
                except Exception as e:
                    print(f"Failed to fetch info from {peer}: {e}")

            print("Fetched info from active peers:", peer_info)
            return peer_info

    def fetch_info(self, address):
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        response = stub.GetPeerInfo(network_pb2.Empty())
        return response

    def handle_new_transaction(self, transaction_data):
        # Предполагается, что transaction_data это объект с полем 'hash'
        transaction_hash = transaction_data.hash
        if transaction_hash not in self.servicer.known_transactions:
            channel = grpc.insecure_channel('address_of_node')
            stub = network_pb2_grpc.NetworkServiceStub(channel)
            stub.BroadcastTransactionHash(network_pb2.TransactionHash(hash=transaction_hash))

    def fetch_full_transaction(self, hash):
        if hash not in self.servicer.known_transactions:
            channel = grpc.insecure_channel('address_of_node')
            stub = network_pb2_grpc.NetworkServiceStub(channel)
            transaction = stub.GetFullTransaction(network_pb2.TransactionHash(hash=hash))
            print(f"Received full transaction: {transaction.data}")