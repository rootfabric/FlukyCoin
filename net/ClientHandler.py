import grpc
from protos import network_pb2, network_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.Transactions import Transaction
from core.Block import Block
import time

class ClientHandler:
    def __init__(self, servicer, node_manager):
        self.servicer = servicer
        self.node_manager = node_manager
        self.log = node_manager.log
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.sent_addresses = set()  # Уже отправленные адреса
        self.peer_status = {}  # Словарь статуса подключения пиров: address -> bool

    # def connect_to_peers(self):
    #     with ThreadPoolExecutor(max_workers=5) as executor:
    #         futures = {executor.submit(self.connect_to_peer, address): address for address in self.servicer.active_peers}
    #
    #         active_peers = {futures[future] for future in as_completed(futures, timeout=1) if future.result()}
    #         self.servicer.active_peers = active_peers  # Обновление списка активных пиров

    def ping_peers(self):
        """ """
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.check_active, peer): peer for peer in
                       self.servicer.known_peers}
            active_peers = {futures[future] for future in as_completed(futures, timeout=5) if future.result(timeout=5)}
            self.servicer.active_peers = active_peers
            # print("Active peers updated.", active_peers)

    def check_active(self, address):
        try:
            with grpc.insecure_channel(address) as channel:
                stub = network_pb2_grpc.NetworkServiceStub(channel)
                stub.Ping(network_pb2.Empty(), timeout=1)  # Установка таймаута для пинга
                return True
        except grpc.RpcError as e:
            # print(f"Failed to ping {address}: {str(e)}")
            return False
    def register_with_peers(self, stub, local_address):
        response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address), timeout=5)
        return response.peers

    def connect_to_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.connect_to_peer, address): address for address in self.servicer.active_peers}

            active_peers = set()
            try:
                for future in as_completed(futures, timeout=10):  # Добавление таймаута для завершения задач
                    address = futures[future]
                    try:
                        result = future.result(timeout=5)  # Таймаут для получения результата задачи

                        if result:
                            active_peers.add(address)
                    except TimeoutError:
                        print(f"Timeout connecting to {address}")
                    except Exception as e:
                        print(f"Error connecting to {address}: {e}")
                print(" OK connect_to_peers")
            except TimeoutError:
                print("Timeout while waiting for futures to complete")

            # self.servicer.active_peers = active_peers  # Обновление списка активных пиров
            # print(f"Active peers updated: {self.servicer.active_peers}")

    def reset_cache_for_peer(self, address):
        if address in self.sent_addresses:
            self.sent_addresses.remove(address)  # Удаляем адрес из кеша отправленных адресов

    def connect_to_peer(self, address):
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        try:
            if address not in self.sent_addresses or not self.peer_status.get(address, False):
                self.reset_cache_for_peer(address)  # Сброс кеша при повторном подключении
                peers = self.register_with_peers(stub, self.servicer.local_address)
                self.sent_addresses.add(address)
                self.peer_status[address] = True  # Устанавливаем статус подключения в True
                self.log.info(f"Registered on {address}, current peers: {peers}")

                new_peers = set(peers) - self.servicer.active_peers

                if new_peers:
                    self.servicer.active_peers.update(new_peers)
                    # self.resend_addresses(new_peers)

                return True

        except grpc.RpcError as e:
            self.peer_status[address] = False  # Устанавливаем статус подключения в False при ошибке
            # print(f"RPC error connecting to {address}: {e}")
            return False

    def resend_addresses(self, new_peers):
        # Рассылка новых адресов существующим активным пирам
        for peer in new_peers:
            if peer not in self.sent_addresses:
                futures = {self.executor.submit(self.connect_to_peer, p): p for p in self.servicer.active_peers if p != peer}
                for future in as_completed(futures, timeout=10):
                    try:
                        future.result(timeout=5)
                    except Exception as e:
                        pass

    def fetch_info_from_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.fetch_info, peer): peer for peer in self.servicer.active_peers}
            peer_info = {}
            for future in as_completed(futures, timeout=5):
                peer = futures[future]
                try:
                    peer_info[peer] = future.result(timeout=1)
                except Exception as e:
                    print(f"Failed to fetch info from {peer}: {e}")

            # print("Fetched info from active peers:", peer_info)
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

    def get_peers_list(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.get_peer, peer): peer for peer in self.servicer.active_peers}
            peer_adress = []
            for future in as_completed(futures, timeout=10):
                peer = futures[future]
                try:
                    peers = future.result(timeout=5)
                    peer_adress += peers
                except Exception as e:
                    print(f"Failed to get_peers info from {peer}: {e}")

            self.servicer.known_peers.update(peer_adress)
            # print("get_peers_list:", self.servicer.known_peers)

    def get_peer(self, address):
        channel = grpc.insecure_channel(address)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        response = stub.GetPeers(network_pb2.PeerRequest())
        return response.peers

    def fetch_transactions_from_peer(self, peer):
        """Запрос всех транзакций с указанной ноды."""
        try:
            channel = grpc.insecure_channel(peer)
            stub = network_pb2_grpc.NetworkServiceStub(channel)
            response = stub.GetAllTransactions(network_pb2.Empty())  # Предполагается, что такой метод существует
            # if response.transactions:
            #     print(f"Received {len(response.transactions)} transactions from {peer}.")
            return response.transactions  # Список транзакций
        except Exception as e:
            print(f"Error fetching transactions from {peer}: {str(e)}")
            return []

    def fetch_transactions_from_all_peers(self):
        """Запрашивает транзакции со всех пингованных нод."""
        # некому отсылать
        if len(self.servicer.active_peers) == 0:
            return

        transactions = []
        with ThreadPoolExecutor(max_workers=len(self.servicer.active_peers)) as executor:
            futures = {executor.submit(self.fetch_transactions_from_peer, peer): peer for peer in
                       self.servicer.active_peers}
            for future in as_completed(futures, timeout=10):
                peer_transactions = future.result(timeout=5)
                transactions.extend(peer_transactions)
                # print(f"Received {len(peer_transactions)} transactions from {futures[future]}.")

        # все полученные транзакции добавляем
        for tr_proto in transactions:
            self.node_manager.add_transaction_to_mempool(Transaction.from_json(tr_proto.json_data))

    def distribute_block(self, block):
        """Распространение блока среди всех активных пиров."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            try:
                futures = {}
                for peer in self.servicer.active_peers:
                    if peer != self.servicer.local_address:  # Исключаем себя из рассылки
                        futures[executor.submit(self.send_block_to_peer, peer, block)] = peer

                for future in as_completed(futures, timeout=10):
                    peer = futures[future]
                    try:
                        future.result(timeout=5)
                        # print(f"Block successfully sent to {peer}.")
                    except TimeoutError:
                        self.log.error(f"Timeout error: Block sending to {peer} took too long.")
                    except Exception as e:
                        self.log.error(f"Failed to send block to {peer}: {str(e)}")

            except Exception as e:
                self.log.error(f"distribute_block: {str(e)}")

    def send_block_to_peer(self, peer, block):
        """Отправка блока одному пиру."""
        channel = grpc.insecure_channel(peer)
        stub = network_pb2_grpc.NetworkServiceStub(channel)
        try:
            # Предполагается, что блок сериализуется в соответствии с вашей схемой
            block_data = block.to_json()  # Сериализация блока в JSON
            stub.BroadcastBlock(network_pb2.Block(data=block_data))
        except grpc.RpcError as e:
            pass
            # self.log.info(f"RPC failed for {peer}: {str(e)}")

    def get_block_by_number(self, block_number, address):
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                with grpc.insecure_channel(address) as channel:
                    stub = network_pb2_grpc.NetworkServiceStub(channel)
                    request = network_pb2.BlockRequest(block_number=block_number)

                    response = stub.GetBlockByNumber(request, timeout=5)  # Добавление таймаута

                    if response.block_data:
                        block = Block.from_json(response.block_data)
                        return block
                    else:
                        raise Exception("Block not found or error occurred")
                        return None
            except grpc.RpcError as e:
                attempt += 1
                self.log.error(f"Attempt {attempt} failed: {str(e)}")
                if attempt == max_attempts:
                    self.log.error(f"Max attempts reached. Unable to connect to {address}")
                    # raise Exception("Max attempts reached. Unable to connect to node.")
                time.sleep(0.1)  # Добавление задержки перед повторной попыткой

    def get_block_candidate(self, address):
        # print("get_block_candidate from", address)
        #
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                with grpc.insecure_channel(address) as channel:
                    stub = network_pb2_grpc.NetworkServiceStub(channel)
                    request = network_pb2.Empty()
                    response = stub.GetBlockCandidate(request, timeout=5)  # Добавление таймаута
                    if response.block_data:
                        block = Block.from_json(response.block_data)
                        return block
                    else:
                        self.log.error("Block not found or error occurred")
                        return None


            except grpc.RpcError as e:

                if e.args[0].code ==grpc.StatusCode.NOT_FOUND:
                    return None

                attempt += 1
                self.log.error(f"Attempt {attempt} failed: {str(e)}")
                if attempt == max_attempts:
                    self.log.error(f"Max attempts reached. Unable to connect to {address}")
                    # raise Exception("Max attempts reached. Unable to connect to node.")
                time.sleep(0.1)  # Добавление задержки перед повторной попыткой
