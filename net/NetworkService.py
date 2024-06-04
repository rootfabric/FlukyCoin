from protos import network_pb2, network_pb2_grpc
import datetime
import grpc
# from core.protocol import Protocol
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.protocol import Protocol
from core.Transactions import Transaction


# from node.node_manager import NodeManager

class NetworkService(network_pb2_grpc.NetworkServiceServicer):
    def __init__(self, local_address, node_manager):

        self.version = Protocol.VERSION
        self.node_manager = node_manager
        self.known_peers = set(node_manager.initial_peers)  # Все известные адреса
        self.active_peers = set()  # Активные адреса

        self.known_transactions = set()  # Хранение известных хешей транзакций

        self.local_address = local_address
        self.peer_addresses = {}  # Клиентский адрес -> серверный адрес
        self.executor = ThreadPoolExecutor(max_workers=5)  # Пул потоков для асинхронной работы

    # Реализация метода Ping
    def Ping(self, request, context):
        return network_pb2.Empty()  # Просто возвращает пустой ответ

    def RegisterPeer(self, request, context):
        client_address = context.peer()
        server_address = request.address
        self.known_peers.add(server_address)
        self.peer_addresses[client_address] = server_address
        if self.check_active(server_address):
            self.active_peers.add(server_address)
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
        # if request.hash not in self.known_transactions:
        if not self.node_manager.mempool.chech_hash_transaction(request.hash):
            # если транзакции нет, делаем сразу запрос в ответ, с запросом полной транзакции
            self.request_full_transaction(request.hash, request.from_host)
        return network_pb2.Ack(success=True)

    def request_full_transaction(self, transaction_hash, source_peer):
        """Запрашиваем полную транзакцию от источника, если не удастся - от других пиров."""
        # Сначала пытаемся получить транзакцию от источника
        if self.try_fetch_transaction_from_peer(transaction_hash, source_peer):
            print(f"Successfully retrieved full transaction from source {source_peer}.")
        else:
            print(f"Failed to retrieve transaction from {source_peer}, trying other peers.")
            # Если не удастся, запрашиваем от всех активных пиров
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {}
                for peer in self.active_peers:
                    if peer != self.local_address and peer != source_peer:  # Исключаем себя и источник
                        future = executor.submit(self.try_fetch_transaction_from_peer,
                                                 transaction_hash, peer)
                        futures[future] = peer

                # Обработка результатов асинхронных вызовов
                for future in as_completed(futures):
                    peer = futures[future]
                    try:
                        if future.result():
                            print(f"Received full transaction from {peer}.")
                            break  # Прерываем цикл, так как получили данные
                    except Exception as e:
                        print(f"Exception while fetching full transaction from {peer}: {str(e)}")

    def try_fetch_transaction_from_peer(self, transaction_hash, peer):
        """Пытаемся получить транзакцию от указанного пира."""
        try:

            # server_address = self.peer_addresses.get(peer, peer)  # Получаем серверный адрес, если он есть
            channel = grpc.insecure_channel(peer)
            stub = network_pb2_grpc.NetworkServiceStub(channel)
            response = stub.GetFullTransaction(
                network_pb2.TransactionHash(hash=transaction_hash, from_host=self.local_address), timeout=3)
            if response.json_data:
                transaction = Transaction.from_json(response.json_data)
                """ Добавление транзакции """
                self.node_manager.add_transaction_to_mempool(transaction)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error fetching transaction from {peer}: {str(e)}")
            return False

    def GetFullTransaction(self, request, context):
        # Здесь код для извлечения полных данных транзакции по хешу из хранилища
        transaction = self.node_manager.mempool.get_transaction(request.hash)
        transaction_json_data = transaction.to_json()
        return network_pb2.Transaction(json_data=transaction_json_data)

    # def retrieve_transaction(self, hash):
    #     # Здесь код для получения данных транзакции из вашего хранилища
    #     return "Some transaction data based on the hash"

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
                                             network_pb2.TransactionHash(hash=transaction_hash,
                                                                         from_host=self.local_address))
                    futures[future] = peer

            # Обработка результатов асинхронных вызовов
            for future in as_completed(futures):
                peer = futures[future]
                try:
                    response = future.result()
                    if response.success:
                        print(f"Broadcast tx: {transaction_hash} successfully broadcasted to peer {peer}.")
                    else:
                        print(f"Failed to broadcast hash {transaction_hash} to peer {peer}.")
                except Exception as e:
                    print(f"Exception during broadcasting hash {transaction_hash} to peer {peer}: {str(e)}")

    def add_new_transaction(self, transaction: Transaction):
        if not self.node_manager.mempool.chech_hash_transaction(transaction.txhash):
            # новая транзакция
            # self.save_transaction(transaction_hash, transaction_data)

            """ добавить валидацию транзакции в цепи """
            self.node_manager.add_transaction_to_mempool(transaction)

            self.distribute_transaction_hash(transaction.txhash)

            print("New transaction added and hash distributed.")

    def AddTransaction(self, request, context):
        # Логика обработки транзакции
        transaction = Transaction.from_json(request.json_data)
        self.add_new_transaction(transaction)
        return network_pb2.Ack(success=True)

    def GetAllTransactions(self, request, context):

        transactions = [tr.to_json() for tr in self.node_manager.mempool.get_transactions().values()]

        return network_pb2.TransactionList(transactions=[network_pb2.Transaction(json_data=tr) for tr in transactions])

    # def add_new_transaction(self, transaction: Transaction):
    #     if not self.node_manager.mempool.chech_hash_transaction(transaction.txhash):
    #         """ добавить валидацию транзакции в цепи """
    #         self.node_manager.add_transaction_to_mempool(transaction)
    #
    #         # Запускаем дистрибуцию хэша в отдельном потоке
    #         self.executor.submit(self.distribute_transaction_hash, transaction.txhash)
    #
    #         print("New transaction added and hash distributed.")
    #
    # def distribute_transaction_hash(self, transaction_hash):
    #     # Логика распределения хэша
    #     with ThreadPoolExecutor(max_workers=10) as executor:
    #         futures = {}
    #         for peer in self.active_peers:
    #             if peer != self.local_address:  # Исключаем себя из рассылки
    #                 channel = grpc.insecure_channel(peer)
    #                 stub = network_pb2_grpc.NetworkServiceStub(channel)
    #                 future = executor.submit(stub.BroadcastTransactionHash,
    #                                          network_pb2.TransactionHash(hash=transaction_hash))
    #                 futures[future] = peer
    #
    #         # Обработка результатов асинхронных вызовов
    #         for future in as_completed(futures):
    #             peer = futures[future]
    #             try:
    #                 response = future.result()
    #                 if response.success:
    #                     print(f"Hash {transaction_hash} successfully broadcasted to peer {peer}.")
    #                 else:
    #                     print(f"Failed to broadcast hash {transaction_hash} to peer {peer}.")
    #             except Exception as e:
    #                 print(f"Exception during broadcasting hash {transaction_hash} to peer {peer}: {str(e)}")
    #
    # def AddTransaction(self, request, context):
    #     transaction = Transaction.from_json(request.json_data)
    #     self.add_new_transaction(transaction)
    #     return network_pb2.Ack(success=True)
