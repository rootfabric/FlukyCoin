from net.server import Server
from net.client import Client
from core.protocol import Protocol
from core.transaction import Transaction
from core.block import Block
import os
import pickle
import threading
import json
import time
import datetime
from tools.time_sync import NTPTimeSynchronizer
import signal

"""

Связь с нодами, организация обмена данными

"""


class NetworkManager:
    def __init__(self, handle_request, config, mempool, chain, time_ntpt):

        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        self.host = config.get("host", "localhost")
        self.port = config.get("port", "5555")

        # синхронизирована нода с блокчейном
        self.synced = False

        self.mempool = mempool
        self.chain = chain
        self.time_ntpt: NTPTimeSynchronizer = time_ntpt

        # валидные сообщения с сервера приходят в ноду:
        self.handle_request_node = handle_request

        self.known_peers = set(self.initial_peers)

        self.server = Server(self.handle_request, host=self.host, port=self.port)

        self.dir = self.server.address
        # self.lock = threading.Lock()

        self.load_from_disk()

        self.known_peers = list(self.known_peers)

        self.running = True

        self.peers: {Client: dict} = {}

        # добавляем самого себя
        self.add_known_peer(self.server.address, ping=False)

        # self.list_need_broadcast_peers = []
        self.peers_to_broadcast = {}
        self.list_need_broadcast_transaction = []
        self.blocks_to_broadcast = {}

        self.start_time = self.time_ntpt.get_corrected_time()

        self.num_blocks_need_load = []

    def signal_handler(self, signal, frame):
        print('Ctrl+C captured, stopping server and shutting down...')
        self.stop()  # Ваш метод для остановки сервера и закрытия потоков

    def run(self):
        # Запуск фонового потока для периодической проверки узлов
        signal.signal(signal.SIGINT, self.signal_handler)
        self.background_thread = threading.Thread(target=self.check_peers)
        self.background_thread.start()

    def add_known_peer(self, new_address, ping=True):

        # print(f"New peer to known_peers")
        if new_address not in self.known_peers:
            self.known_peers = set(self.known_peers)
            self.known_peers.add(new_address)

            self.known_peers = list(self.known_peers)
        if ping:
            self.ping_peer(new_address)
            # self.broadcast_new_peer(new_address)

    def handle_request_node(self):
        """"""
        raise "Метод должен быть назначен в ноде"

    def handle_request(self, request, client_id):
        """ Сообщение с сервера сначала попадает сюда """
        command = request.get('command')

        if command == 'version':
            print("Server connect", command)
            new_address = request.get('address')
            self.server.clients[client_id] = new_address
            self.add_known_peer(new_address, False)

            # новый адрес, отправить всем активным пирам
            self.distribute_peer(new_address)

            print("New server connect", new_address)
            return {'connected': True}

        if client_id not in self.server.clients:
            return {"error": "need authorisation"}

        # print("Server command", command, self.server.clients[client_id])
        # работа ноды на входящее сообщение
        return self.handle_request_node(request, client_id)

    def distribute_peer(self, new_address):
        print("distribute_peer get_active_peers", self.active_peers())
        # заготовка на рассылку блоков клиентам
        for peer in self.active_peers():
            if peer == self.server.address:
                continue
            peers_to_brodcast = self.peers_to_broadcast.get(peer, [])
            peers_to_brodcast.append(new_address)
            self.peers_to_broadcast[peer] = peers_to_brodcast

    def save_to_disk(self, filename='peers.json'):

        # print("no save peers")
        # retur
        dir = self.dir.replace(":", "_")  # Замена недопустимых символов в имени директории

        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        full_path = os.path.join(dir_path, filename)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)  # Создание директории, если необходимо

        with open(full_path, 'w') as file:
            json.dump(self.known_peers, file, indent=4)

    def load_from_disk(self, filename='peers.json'):
        dir = self.dir.replace(":", "_")

        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        full_path = os.path.join(dir_path, filename)

        if os.path.exists(full_path):
            with open(full_path, 'r') as file:
                try:
                    a = set(json.load(file))
                    self.known_peers = self.known_peers | a
                except:
                    pass
        else:
            print(f"No data file found at {full_path}. Starting with an empty list of peers.")

    def ping_all_peers(self):
        for peer in list(self.known_peers):
            self.ping_peer(peer)

    def ping_active_peers(self):
        for peer in list(self.peers.values()):
            self.ping_peer(peer)

    def active_peers(self):
        return [peer for peer in self.peers]

    def _ping_all_peers_and_save(self):
        self.ping_all_peers()
        self.save_to_disk()
        # print(self.active_peers())

    def _connect_to_address(self, address):
        try:
            client = Client(address.split(":")[0], int(address.split(":")[1]))
            if client is not None:
                self.peers[address] = client

            response = client.send_request(
                {'command': 'version', 'ver': Protocol.version, 'address': self.server.address})
            if response is None:
                del self.peers[address]
                return None
            elif 'error' in response:
                del self.peers[address]
                return None
            else:
                message = response.get('connected')
                if message is not True:
                    # нода не принимает соединение
                    print(f"wrong version {address}")
                    del self.peers[address]
                    return None

            client.send_request({'command': 'newpeer', 'peer': address})

            # при первом коннекте шлем своего кандидата
            # self.distribute_block(self.chain.block_candidate, address)
            # client.send_request(req = {'command': 'invb', 'block_hash': self.chain.block_candidate.hash_block()}

            return client

        except Exception as e:

            if address in self.peers:
                del self.peers[address]

    def ping_peer(self, address):
        """ установка связи и проверка соединеня """

        client = self.peers.get(address)
        if client is None:
            client = self._connect_to_address(address)

        if client is None:
            # если клиента нет, выполняем подключение
            # print(f"Ошибка клиента {address}")
            # пир не отвечает, удаляем из активных
            if address in self.peers:
                del self.peers[address]
            return False

        # try:
        response = client.send_request({'command': 'getinfo'})
        if response is not None:
            if 'error' not in response:

                if address not in self.known_peers:
                    self.add_known_peer(address, False)
                    print(f"New active peer {address}")

                new_peers = response.get('peers', [])
                for new_peer in new_peers:
                    self.add_known_peer(new_peer, ping=False)

                # Ответ клиента несет самую важную информацию для синхронизации
                client.info = response

                return True

            print(f"Error send: {response}")
            del self.peers[address]
            return False

        else:
            print(f"Failed to connect to {address}")
            del self.peers[address]
            return False

    def take_mempool(self, address):
        """ установка связи и проверка соединеня """

        client = self.peers.get(address)
        if client is None:
            client = self._connect_to_address(address)

        if client is None:
            # если клиента нет, выполняем подключение
            # print(f"Ошибка клиента {address}")
            return False

        # try:
        response = client.send_request({'command': 'mempool'})
        if response is not None:
            if 'error' not in response:

                mem_hashes = response.get("mempool_hashes")
                if mem_hashes is None:
                    return False

                # если есть транзакция, которой нет у клиента, пополняем на бродкаст
                #
                for t in self.mempool.transactions:
                    if t not in mem_hashes:
                        self.list_need_broadcast_transaction.append(self.mempool.transactions[t])

                for h in mem_hashes:
                    if not self.mempool.chech_hash_transaction(h):
                        response = client.send_request({'command': 'gettransaction', 'tx_id': h})
                        self.handle_request_node(response)

                return True

            print(f"Error send: {response}")
            if address in self.peers:
                del self.peers[address]
            return False

        else:
            print(f"Failed to connect to {address}")
            if address in self.peers:
                del self.peers[address]
            return False

    def stop(self):
        self.running = False
        self.background_thread.join()  # Дожидаемся завершения фонового потока

    def broadcast_new_peer(self):
        """ передать всем клиентам информацию о новом пире """
        # print("distribute_block get_active_peers", self.active_peers())

        for adress in list(self.peers_to_broadcast):
            if adress in self.peers:
                peers = self.peers_to_broadcast.get(adress)

                for peer_to_broadcast in peers:
                    client = self.peers[adress]
                    if client.is_connected:
                        answer = client.send_request({'command': 'newpeer', 'peer': peer_to_broadcast})
                        # if answer.get('status') == 'success':
                        #     print(f"Broadcast peer to {peer_to_broadcast}")

            del self.peers_to_broadcast[adress]

    def broadcast_new_transaction(self, tx_to_broadcast: Transaction):
        """ передать всем клиентам информацию о новом пире """

        print(f"Broadcast to {tx_to_broadcast}")
        for client in list(self.peers.values()):

            if self.server.address == client.address():
                # сами себе не бродкастим
                continue

            if client.is_connected:
                response = client.send_request({'command': 'invt', 'tx': tx_to_broadcast.hash})
                if response.get('status') == 'ok':
                    if tx_to_broadcast in self.list_need_broadcast_transaction:
                        self.list_need_broadcast_transaction.remove(tx_to_broadcast)

                if response.get('status') == 'get':
                    # клиенту нужна эта транзакция
                    response = client.send_request(
                        {'command': 'tx',
                         'tx_data': {'tx_json': tx_to_broadcast.to_json(), 'tx_sign': tx_to_broadcast.sign}})
                    print(response)

    def distribute_block(self, block, address=None):

        if block is None:
            return
        # print("distribute_block get_active_peers", self.active_peers())
        # заготовка на рассылку блоков клиентам
        for peer in self.active_peers():
            if peer == self.server.address:
                continue
            if address is not None and address != peer:
                # задан конеретный адрес куда отослать
                continue
            blocks_to_brodcast = self.blocks_to_broadcast.get(peer, [])
            blocks_to_brodcast.append(block)
            self.blocks_to_broadcast[peer] = blocks_to_brodcast

    def pull_blocks_from_peer(self, peer, start_block, end_block):
        client = self.peers[peer]
        # Запрашиваем блоки, которые отсутствуют
        for block_number in range(start_block, end_block):
            response = client.send_request({'command': 'getblock', 'block_number': block_number})
            block_data = response.get('block')
            if block_data:
                # Проверяем и добавляем блок в локальную цепочку
                block = Block.from_json(block_data)
                if self.chain.validate_and_add_block(block):
                    print(f"Block {block_number} added from {peer}. {block.hash}")
                else:
                    print(f"Invalid block {block_number} received from {peer}.")

        client.close()

    def broadcast_blocks(self):
        """ передать всем клиентам информацию о новом блоке """

        # print(f"Broadcast new block {self.block_to_brodcast.hash}")

        for adress in list(self.blocks_to_broadcast):
            if adress in self.peers:
                blocks = self.blocks_to_broadcast.get(adress)

                block_to_brodcast: Block = None
                if len(blocks) > 0:
                    block_to_brodcast = blocks.pop(0)
                else:
                    del self.blocks_to_broadcast[adress]
                    continue

                client = self.peers[adress]
                if client.is_connected:
                    req = {'command': 'invb', 'block_hash': block_to_brodcast.hash_block()}
                    response = client.send_request(req)

                    if response is not None and response.get('status') == 'ok':

                        if len(blocks) > 0:
                            self.blocks_to_broadcast[adress] = blocks

                    if response is not None and response.get('status') == 'get':
                        # клиенту нужен блок
                        response = client.send_request(
                            {'command': 'newblock',
                             'block_data': block_to_brodcast.to_json()})

                        if "block_candidate" in response:
                            candidate_json = response.get("block_candidate")
                            candidate = Block.from_json(candidate_json)
                            if self.chain.add_block_candidate(candidate):
                                print(f"Блок от {adress} верный. Добавляем в цепь")
                                self.distribute_block(self.chain.block_candidate, adress)
                            # else:
                            # print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                            # print("Нода считает верным блок", candidate.hash_block() )
                            # self.chain.add_block_candidate(candidate)
                        # print(response)

    # def sync_node(self):
    #     # Проверяем, есть ли у всех известных узлов такое же количество блоков, как и у текущего узла
    #     current_block_count = len(self.chain.blocks)
    #     print(f"Checking synchronization status with {len(self.active_peers())} peers...")
    #     for peer in self.active_peers():
    #
    #         if peer == self.server.address:
    #             continue
    #
    #         client = self.peers.get(peer)
    #
    #         if client is None:
    #             continue
    #
    #         response = client.send_request({'command': 'newpeer', 'peer': self.server.address})
    #         if "error" in response:
    #             continue
    #         print(response)
    #
    #         response = client.send_request({'command': 'getinfo'})
    #         peer_block_count = response.get('block_count', 0)
    #         client.close()
    #
    #         # Если количество блоков различается, начинаем процесс синхронизации
    #         if peer_block_count != current_block_count:
    #             print(f"Synchronization needed with {peer}.")
    #             self.pull_blocks_from_peer(peer, current_block_count, peer_block_count)
    #
    #             # берем очередной блок которого нет в ноде
    #             block_num = self.chain.blocks_count()
    #             response = client.send_request({'command': 'getblock', 'block_number': block_num})
    #             block_data = response.get('block')
    #             if block_data:
    #                 # Проверяем и добавляем блок в локальную цепочку
    #                 block = Block.from_json(block_data)
    #                 if self.chain.validate_and_add_block(block):
    #                     print(f"Block {block.block_num} added from {peer}. {block.hash}")
    #                 else:
    #                     print(f"Invalid block {block_num} received from {peer}.")
    #
    #         else:
    #             print(f"{peer} is synchronized.")
    #
    #         # self.pull_candidat_block_from_peer(peer)
    #
    #     print(f"Synchronization check completed. Nodes count {len(self.active_peers())}")
    #     print(f"Blocks: {self.chain.blocks_count()}")
    #     if self.chain.last_block() is not None:
    #         print(f"{datetime.datetime.fromtimestamp(self.chain.last_block().time)}")

    def pull_candidat_block_from_peer(self, peer):

        if peer not in self.peers:
            return

        client = self.peers[peer]
        # отдельно берем кандидата
        answer = client.send_request({'command': 'getblockcandidate'})

        blockcandidate_json = answer.get("block_candidate")
        if blockcandidate_json is not None:
            blockcandidate = Block.from_json(blockcandidate_json)
            if self.chain.add_block_candidate(blockcandidate):
                print("Добавлен кандидат с ноды", blockcandidate.hash)
                self.distribute_block(self.chain.block_candidate, peer)
            else:
                # print("Кандидат с ноды не подходит", blockcandidate.hash)
                self.distribute_block(self.chain.block_candidate, peer)

    def check_synk_with_peers(self):
        """ Проверка синхронности с пирами """

        count_peers = 0
        # print("check_synk_with_peers",  self.peers.keys())
        block_sync = True
        chain_size = 0

        # if not self.synced:
        #     # пингуем если не засинхрины активно
        #     self.ping_all_peers()

        for client in list(self.peers.values()):

            # себя не смотрим
            if client.address() == self.server.address:
                continue

            count_peers += 1


            client.info = client.send_request({'command': 'getinfo'})

            peer_info = client.info
            # print("peer_info", peer_info)



            if peer_info is not None and "synced" in peer_info:
                # print(peer_info)
                if peer_info['synced'] == "True":

                    chain_size = max(chain_size, peer_info['block_count'])
                    # print("Узел синхронный, проверяем состояние")
                    # print(peer_info)
                    if peer_info['block_count'] > self.chain.blocks_count():

                        # print("На узле блоков больше, подгружаем")
                        block_sync = False
                        # берем очередной блок которого нет в ноде
                        block_num = self.chain.blocks_count()
                        response = client.send_request({'command': 'getblock', 'block_number': block_num})
                        block_data = response.get('block')
                        if block_data:
                            # Проверяем и добавляем блок в локальную цепочку
                            block = Block.from_json(block_data)
                            if self.chain.validate_and_add_block(block):
                                print(f"Block {block_num} added from {client.address()}. {block.hash}")
                            else:
                                print(f"Invalid block {block_num} received from {client.address()}.")
                                "Возникает ситуация, когда своя цепочка не соподает с присылаемой"
                                "Тут надо делать более сложный форк"
                                "Пока просто откатываемся на несколько блоков назад"
                                "Нужна правильная отработка отката транзакций"
                                self.chain.blocks =self.chain.blocks[:-10]
                                self.chain.reset_block_candidat()
                        continue

                    # если количество блоков равно, доп проверки
                    if peer_info['block_count'] == self.chain.blocks_count():

                        if self.chain.block_candidate_hash is not None and peer_info['block_candidat'] is not None:
                            if peer_info['block_candidat'] != self.chain.block_candidate_hash:
                                # print("!!! Не совпадает кандидат, требуется обмен")
                                self.distribute_block(self.chain.block_candidate)
                                self.pull_candidat_block_from_peer(client.address())

                        # if peer_info['last_block_hash'] != self.chain.last_block_hash():
                        #     # print("!!! Не совпадает последний блок", peer_info['last_block_hash'])
                        #     # self.ping_peer(client.address())
                        #     self.distribute_block(self.chain.block_candidate)

        if  block_sync and not self.synced and self.chain.blocks_count() ==chain_size and chain_size!=0:

            # if  (self.time_ntpt.get_corrected_time() - self.chain.last_block().time>3 and
            if   self.time_ntpt.get_corrected_time() - self.chain.last_block().time < 1:
                print("Блоки синхронизированные:", self.chain.blocks_count())
                print(self.chain.last_block_hash())

                self.synced = True
                print("Нода синхронизированна!")

        # print("Всего активныйх пиров", count_peers)
        if self.synced and self.chain.blocks_count()< chain_size and chain_size != 0:
            self.synced = False
            print("Нода потеряла синхронизацию!")


        if count_peers == 0:
            if self.time_ntpt.get_corrected_time() > self.start_time + Protocol.wait_active_peers_before_start:
                if not self.synced:
                    print("Ноды не обнаружены, включаем синхронизацию")
                    self.synced = True

    def check_peers(self):
        """ Проверка доступных нод, выбор ближайших соседей """

        t = time.time() - 11
        pause_mempool = time.time()
        pause_synced = time.time()
        while self.running:


            if time.time() - t > 10:
                thread = threading.Thread(target=self._ping_all_peers_and_save)
                thread.start()
                # self._ping_all_peers_and_save()
                t = time.time()

            if len(self.peers_to_broadcast) > 0:
                self.broadcast_new_peer()

            if not self.synced:
                self.check_synk_with_peers()
                time.sleep(0.01)
                continue

            if time.time() - pause_synced > 1:
                # если засинхрились, то проверка реже
                pause_synced = time.time()
                self.check_synk_with_peers()

                # if len(self.list_need_broadcast_transaction) > 0:
            #     for tx in self.list_need_broadcast_transaction:
            #         self.broadcast_new_transaction(tx)

            if len(self.blocks_to_broadcast) > 0:
                self.broadcast_blocks()

            if time.time() - pause_mempool > 10:
                for peer in list(self.active_peers()):
                    if self.server.address != peer:
                        self.take_mempool(peer)

                pause_mempool = time.time()

            time.sleep(0.1)  # Пауза перед следующей проверкой
