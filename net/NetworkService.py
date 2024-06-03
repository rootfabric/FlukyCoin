from protos import network_pb2, network_pb2_grpc
import datetime
import grpc
# from core.protocol import Protocol
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkService(network_pb2_grpc.NetworkServiceServicer):
    def __init__(self, local_address, version, node_manager):
        self.local_address = local_address
        self.version = version
        self.node_manager = node_manager
        self.known_peers = set(node_manager.initial_peers)  # Все известные адреса
        self.active_peers = set()  # Активные адреса

        self.known_transactions = set()  # Хранение известных хешей транзакций

    # Реализация метода Ping
    def Ping(self, request, context):
        return network_pb2.Empty()  # Просто возвращает пустой ответ

    def RegisterPeer(self, request, context):
        address = request.address
        self.known_peers.add(address)
        # Проверяем, является ли адрес активным
        if self.check_active(address):
            self.active_peers.add(address)
        return network_pb2.PeerResponse(peers=list(self.active_peers))

    def GetPeers(self, request, context):
        # Возвращаем только активные адреса
        return network_pb2.PeerResponse(peers=list(self.active_peers))

    def GetNodeInfo(self, request, context):
        data = self.node_manager.fetch_data()
        return network_pb2.PeerInfoResponse(version=self.version, state="active", current_time=data)

    def check_active(self, address):
        try:
            with grpc.insecure_channel(address) as channel:
                stub = network_pb2_grpc.NetworkServiceStub(channel)
                stub.Ping(network_pb2.Empty(), timeout=1)  # Установка таймаута для пинга
                return True
        except grpc.RpcError as e:
            # print(f"Failed to ping {address}: {str(e)}")
            return False


    def check_active(self, address):
        try:
            with grpc.insecure_channel(address) as channel:
                stub = network_pb2_grpc.NetworkServiceStub(channel)
                stub.Ping(network_pb2.Empty(), timeout=1)  # Установка таймаута для пинга
                return True
        except grpc.RpcError as e:
            # print(f"Failed to ping {address}: {str(e)}")
            return False

    def GetPeerInfo(self, request, context):
        # print(
        #     f"Sending version: {self.node_manager.version}, synced: {self.node_manager.synced}, candidate: {self.node_manager.block_candidate}")
        response = network_pb2.PeerInfoResponse(
            version=self.node_manager.version,
            synced=self.node_manager.synced,
            block_candidate=self.node_manager.block_candidate
        )
        return response

    def BroadcastTransactionHash(self, request, context):
        if request.hash not in self.known_transactions:
            self.known_transactions.add(request.hash)
            self.distribute_transaction_hash(request.hash)
        return network_pb2.Ack(success=True)

    def GetFullTransaction(self, request, context):
        # Здесь код для извлечения полных данных транзакции по хешу из хранилища
        transaction_data = self.retrieve_transaction(request.hash)
        return network_pb2.Transaction(hash=request.hash, data=transaction_data)


    def retrieve_transaction(self, hash):
        # Здесь код для получения данных транзакции из вашего хранилища
        return "Some transaction data based on the hash"

    def distribute_transaction_hash(self, transaction_hash):
        # Используем ThreadPoolExecutor для параллельной рассылки хеша
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for peer in self.active_peers:
                if peer != self.local_address:  # Исключаем себя из рассылки
                    channel = grpc.insecure_channel(peer)
                    stub = network_pb2_grpc.NetworkServiceStub(channel)
                    # Асинхронный вызов метода BroadcastTransactionHash
                    future = executor.submit(stub.BroadcastTransactionHash,
                                             network_pb2.TransactionHash(hash=transaction_hash))
                    futures[future] = peer

            # Обработка результатов асинхронных вызовов
            for future in as_completed(futures):
                peer = futures[future]
                try:
                    response = future.result()
                    if response.success:
                        print(f"Hash {transaction_hash} successfully broadcasted to peer {peer}.")
                    else:
                        print(f"Failed to broadcast hash {transaction_hash} to peer {peer}.")
                except Exception as e:
                    print(f"Exception during broadcasting hash {transaction_hash} to peer {peer}: {str(e)}")

    def GetFullTransaction(self, request, context):
        transaction_data = self.retrieve_transaction(request.hash)
        if transaction_data:
            return network_pb2.Transaction(hash=request.hash, data=transaction_data)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Transaction not found')
            return network_pb2.Transaction()

    def add_new_transaction(self, transaction_hash, transaction_data):
        if transaction_hash not in self.known_transactions:

            # self.save_transaction(transaction_hash, transaction_data)
            self.distribute_transaction_hash(transaction_hash)

            self.known_transactions.add(transaction_hash)
            print("New transaction added and hash distributed.")

    def AddTransaction(self, request, context):
        # Логика обработки транзакции
        self.add_new_transaction(request.hash, request.data)
        return network_pb2.Ack(success=True)