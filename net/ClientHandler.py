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
        self.executor = ThreadPoolExecutor(max_workers=100)
        self.sent_addresses = set()  # Уже отправленные адреса
        self.peer_status = {}  # Словарь статуса подключения пиров: address -> bool
        self.peer_channels = {}

    def ping_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.check_active, peer): peer for peer in self.servicer.known_peers}
            active_peers = {futures[future] for future in as_completed(futures, timeout=5) if future.result(timeout=5)}
            self.servicer.active_peers = active_peers
            # print("active_peers", active_peers)

    def check_active(self, address):
        try:
            if address not in self.peer_channels:
                channel = grpc.insecure_channel(address)
                self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

            stub = self.peer_channels[address]
            stub.Ping(network_pb2.Empty(), timeout=2)  # Установка таймаута для пинга
            return True
        except grpc.RpcError as e:
            if address in self.peer_channels:
                del self.peer_channels[address]
            return False

    def register_with_peers(self, stub, local_address):
        response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address), timeout=5)
        return response.peers
    def register_with_peers(self, stub, local_address):
        response = stub.RegisterPeer(network_pb2.PeerRequest(address=local_address), timeout=5)
        return response.peers

    def connect_to_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.connect_to_peer, address): address for address in
                       self.servicer.active_peers}

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
                # print(" OK connect_to_peers")
            except TimeoutError:
                print("Timeout while waiting for futures to complete")

    def reset_cache_for_peer(self, address):
        if address in self.sent_addresses:
            self.sent_addresses.remove(address)  # Удаляем адрес из кеша отправленных адресов

    def connect_to_peer(self, address):
        if address not in self.peer_channels:
            channel = grpc.insecure_channel(address)
            self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[address]
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
            if address in self.peer_channels:
                del self.peer_channels[address]
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
                    # print(f"Failed to fetch info from {peer}: {e}")
                    """ """
            return peer_info

    def fetch_info(self, address):
        if address not in self.peer_channels:
            channel = grpc.insecure_channel(address)
            self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[address]
        try:
            response = stub.GetPeerInfo(network_pb2.Empty(), timeout=2)  # Установка таймаута для получения информации
            return response
        except grpc.RpcError as e:
            if address in self.peer_channels:
                del self.peer_channels[address]
            # print(f"Failed to fetch info from {address}: {e}")
            return None

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
                    print(f"Failed to get peers info from {peer}: {e}")

            self.servicer.known_peers.update(peer_adress)
            # print("get_peers_list:", self.servicer.known_peers)

    def get_peer(self, address):
        if address not in self.peer_channels:
            channel = grpc.insecure_channel(address)
            self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[address]
        try:
            response = stub.GetPeers(network_pb2.PeerRequest(), timeout=2)
            return response.peers
        except grpc.RpcError as e:
            if address in self.peer_channels:
                del self.peer_channels[address]
            # print(f"Failed to get peers info from {address}: {e}")
            return []

    def fetch_transactions_from_all_peers(self):
        """Запрашивает транзакции со всех пингованных нод."""
        if len(self.servicer.active_peers) == 0:
            return

        transactions = []
        with ThreadPoolExecutor(max_workers=len(self.servicer.active_peers)) as executor:
            futures = {executor.submit(self.fetch_transactions_from_peer, peer): peer for peer in
                       self.servicer.active_peers}
            for future in as_completed(futures, timeout=10):
                try:
                    peer_transactions = future.result(timeout=5)
                    transactions.extend(peer_transactions)
                except Exception as e:
                    print(f"Error fetching transactions: {e}")

        # все полученные транзакции добавляем
        for tr_proto in transactions:
            self.node_manager.add_transaction_to_mempool(Transaction.from_json(tr_proto.json_data))

    def fetch_transactions_from_peer(self, peer):
        """Запрос всех транзакций с указанной ноды."""
        try:
            if peer not in self.peer_channels:
                channel = grpc.insecure_channel(peer)
                self.peer_channels[peer] = network_pb2_grpc.NetworkServiceStub(channel)

            stub = self.peer_channels[peer]
            response = stub.GetAllTransactions(network_pb2.Empty(),
                                               timeout=2)  # Установка таймаута для получения информации
            return response.transactions  # Список транзакций
        except grpc.RpcError as e:
            if peer in self.peer_channels:
                del self.peer_channels[peer]
            # print(f"Error fetching transactions from {peer}: {str(e)}")
            return []

    def send_block_hash_to_peer(self, peer, block_hash):
        """Отправка хеша блока одному пиру."""
        if peer not in self.peer_channels:
            channel = grpc.insecure_channel(peer)
            self.peer_channels[peer] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[peer]
        try:
            response = stub.BroadcastBlockHash(network_pb2.BlockHash(hash=block_hash), timeout=1)
            self.log.info(f"Send hash to {peer}: {block_hash}")
            return response.need_block  # True если пир запросил блок целиком
        except grpc.RpcError as e:
            if peer in self.peer_channels:
                del self.peer_channels[peer]
            # self.log.info(f"RPC failed for {peer}: {str(e)}")
            return False

    def distribute_block(self, block):
        """Распространение блока среди всех активных пиров."""
        block_hash = block.hash_block()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for peer in self.servicer.active_peers:
                if peer != self.servicer.local_address:  # Исключаем себя из рассылки
                    futures[executor.submit(self.send_block_hash_to_peer, peer, block_hash)] = peer

            for future in as_completed(futures, timeout=2):
                peer = futures[future]
                try:
                    need_block = future.result(timeout=5)
                    if need_block:
                        self.executor.submit(self.send_block_to_peer, peer, block)
                except TimeoutError:
                    self.log.error(f"Timeout error: Block hash sending to {peer} took too long.")
                except Exception as e:
                    self.log.error(f"Failed to send block hash to {peer}: {str(e)}")

    def send_block_to_peer(self, peer, block):
        """Отправка блока одному пиру."""
        if peer not in self.peer_channels:
            channel = grpc.insecure_channel(peer)
            self.peer_channels[peer] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[peer]
        try:
            block_data = block.to_json()  # Сериализация блока в JSON
            stub.BroadcastBlock(network_pb2.Block(data=block_data), timeout=2)
            self.log.info(f"Send to {peer} block {block.hash_block()}")
        except grpc.RpcError as e:
            if peer in self.peer_channels:
                del self.peer_channels[peer]
            self.log.info(f"RPC failed for {peer}: {str(e)}")
            self.request_block_candidate_from_peer(peer)  # Запрос блока-кандидата при RPC ошибке

    def request_block_candidate_from_peer(self, peer):
        """Запрашивает блок-кандидат у пира."""
        try:
            if peer not in self.peer_channels:
                channel = grpc.insecure_channel(peer)
                self.peer_channels[peer] = network_pb2_grpc.NetworkServiceStub(channel)

            stub = self.peer_channels[peer]
            request = network_pb2.Empty()
            response = stub.GetBlockCandidate(request, timeout=5)  # Добавление таймаута

            if response.block_data:
                candidate_block = Block.from_json(response.block_data)
                # self.log.info(f"Received block candidate from peer {peer} {candidate_block.hash_block()}")
                # Можно добавить обработку кандидата блока, например, валидацию и добавление в цепь
                if self.node_manager.chain.validate_block(candidate_block):
                    if self.node_manager.chain.add_block_candidate(candidate_block):
                        self.log.info(f"Block candidate from peer {peer} added to chain.  {candidate_block.hash_block()}")

                        # пересылаем всем кого знаем
                        self.node_manager.client_handler.distribute_block(candidate_block)
            else:
                self.log.error(f"No block candidate received from peer {peer}")

        except grpc.RpcError as e:
            if peer in self.peer_channels:
                del self.peer_channels[peer]
            # self.log.error(f"Failed to get block candidate from {peer}: {str(e)}")

    def get_block_by_number(self, block_number, address):
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            # try:
                if address not in self.peer_channels:
                    channel = grpc.insecure_channel(address)
                    self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

                stub = self.peer_channels[address]
                request = network_pb2.BlockRequest(block_number=block_number)
                response = stub.GetBlockByNumber(request, timeout=5)  # Добавление таймаута

                if response.block_data:
                    block = Block.from_json(response.block_data)
                    return block
                else:
                    raise Exception("Block not found or error occurred")
            # except grpc.RpcError as e:
            #     attempt += 1
            #     self.log.error(f"Attempt {attempt} failed: {str(e)}")
            #     if attempt == max_attempts:
            #         if address in self.peer_channels:
            #             del self.peer_channels[address]
            #         self.log.error(f"Max attempts reached. Unable to connect to {address}")
            #     time.sleep(0.1)  # Добавление задержки перед повторной попыткой
        return None

    def get_block_candidate(self, address):
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                if address not in self.peer_channels:
                    channel = grpc.insecure_channel(address)
                    self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

                stub = self.peer_channels[address]
                request = network_pb2.Empty()
                response = stub.GetBlockCandidate(request, timeout=5)  # Добавление таймаута

                if response.block_data:
                    block = Block.from_json(response.block_data)
                    return block
                else:
                    self.log.error("Block not found or error occurred")
                    return None
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    return None

                attempt += 1
                self.log.error(f"Attempt {attempt} failed: {str(e)}")
                if attempt == max_attempts:
                    if address in self.peer_channels:
                        del self.peer_channels[address]
                    self.log.error(f"Max attempts reached. Unable to connect to {address}")
                time.sleep(0.1)  # Добавление задержки перед повторной попыткой
        return None

    def distribute_transaction_hash(self, transaction_hash):
        """Логика распределения хэша."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for peer in self.servicer.active_peers:
                if peer != self.servicer.local_address:  # Исключаем себя из рассылки
                    if peer not in self.peer_channels:
                        channel = grpc.insecure_channel(peer)
                        self.peer_channels[peer] = network_pb2_grpc.NetworkServiceStub(channel)

                    stub = self.peer_channels[peer]
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
                    if peer in self.peer_channels:
                        del self.peer_channels[peer]
                    print(f"Exception during broadcasting hash {transaction_hash} to peer {peer}: {str(e)}")
