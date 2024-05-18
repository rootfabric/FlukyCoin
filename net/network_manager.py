import copy

from net.server import Server
from net.client import Client
from core.protocol import Protocol
from core.transaction import Transaction
from storage.chain import Chain
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
    def __init__(self, handle_request, config, mempool, chain: Chain, time_ntpt):

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
        self.no_need_pause_sinc= False
        print("Start networc manager", self.known_peers)

    def signal_handler(self, signal, frame):
        print('Ctrl+C captured, stopping server and shutting down...')
        self.stop()  # Ваш метод для остановки сервера и закрытия потоков

    def run(self):
        # Запуск фонового потока для периодической проверки узлов
        signal.signal(signal.SIGINT, self.signal_handler)
        self.background_thread = threading.Thread(target=self.check_peers)
        self.background_thread.daemon = True
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

    def handle_request(self, request):
        """ Сообщение с сервера сначала попадает сюда """
        command = request.get('command')

        if command == 'version':
            # print("Server connect", command)
            new_address = request.get('address')
            # self.server.clients[client_id] = new_address
            self.add_known_peer(new_address, False)

            # новый адрес, отправить всем активным пирам
            self.distribute_peer(new_address)

            # print("New server connect", new_address)
            return {'connected': True, "address": self.server.address}

        # if client_id not in self.server.clients:
        #     return {"error": "need authorisation"}

        # print("Server command", command, self.server.clients[client_id])
        # работа ноды на входящее сообщение
        return self.handle_request_node(request)

    def distribute_peer(self, new_address):
        # print("distribute_peer get_active_peers", self.active_peers())
        # заготов ка на рассылку блоков клиентам
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
        try:
            for peer in list(self.known_peers):
                thread = threading.Thread(target=self.ping_peer, args=(peer,))
                thread.daemon = True
                thread.start()
        except Exception as e:
            print("error ping_all_peers", e)

    def ping_active_peers(self):
        for peer in list(self.peers.values()):
            self.ping_peer(peer)

    def active_peers(self):
        return [peer for peer in self.peers]

    def _ping_all_peers_and_save(self):
        while self.running:
            try:
                self.ping_all_peers()
                self.save_to_disk()
                # print(self.active_peers())
            except Exception as e:
                print(" Error _ping_all_peers_and_save", e)

            time.sleep(60)

    def _connect_to_address(self, address):
        try:
            client = Client(address.split(":")[0], int(address.split(":")[1]))
            if client is not None:
                self.peers[address] = client

            else:
                return None

            response = client.send_request(
                {'command': 'version', 'ver': Protocol.VERSION, 'address': self.server.address})
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
                # сервер возвращает свой реальный адрес.
                client.server_address = response.get('address')
                # print("connect to ", address)

            client.send_request({'command': 'newpeer', 'peer': self.server.address})

            # при первом коннекте шлем своего кандидата
            # self.distribute_block(self.chain.block_candidate, address)
            # client.send_request(req = {'command': 'invb', 'block_hash': self.chain.block_candidate.hash_block()}

            return client

        except Exception as e:

            if address in self.peers:
                del self.peers[address]

    def ping_peer(self, address):
        """ установка связи и проверка соединеня """
        try:
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
            # response = client.send_request({'command': 'getinfo'})
            response = client.get_info()

            # print(f"{address} ping response ", response)
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
        except Exception as e:
            print("Error ping_peer!", e)

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
        self.server.close()
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

    def distribute_block(self, block, address=None, ban_address=None):

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
            if ban_address is not None and ban_address == peer:
                # задан конеретный адрес куда не надо отослать
                continue
            blocks_to_brodcast = self.blocks_to_broadcast.get(peer, [])
            blocks_to_brodcast.append(copy.deepcopy(block))
            self.blocks_to_broadcast[peer] = blocks_to_brodcast

    # def pull_blocks_from_peer(self, peer, start_block, end_block):
    #     client = self.peers[peer]
    #     # Запрашиваем блоки, которые отсутствуют
    #     for block_number in range(start_block, end_block):
    #         response = client.send_request({'command': 'getblock', 'block_number': block_number})
    #         block_data = response.get('block')
    #         if block_data:
    #             # Проверяем и добавляем блок в локальную цепочку
    #             block = Block.from_json(block_data)
    #             if self.chain.validate_and_add_block(block):
    #                 print(f"Block {block_number} added from {peer}. {block.hash}")
    #                 if int(block_number)%100==0:
    #                     self.chain.save_to_disk()
    #             else:
    #                 print(f"Invalid block {block_number} received from {peer}.")
    #
    #     client.close()

    def broadcast_blocks(self):
        """ передать всем клиентам информацию о новом блоке """

        for adress in list(self.blocks_to_broadcast):
            if adress in self.peers:

                blocks = self.blocks_to_broadcast.get(adress)

                # if (len(blocks) > 0 and
                #         self.time_ntpt.get_corrected_time() - (blocks[0].time -Protocol.BLOCK_TIME_INTERVAL) < Protocol.BLOCK_TIME_INTERVAL / 10):
                #     # выжидаем некоторое время перед рассылкой блока, чтобы все пири закрылись
                #      continue

                block_to_brodcast: Block = None
                if len(blocks) > 0:
                    block_to_brodcast = blocks.pop(0)
                else:
                    del self.blocks_to_broadcast[adress]
                    continue

                client = self.peers[adress]

                # if client.last_broadcast_block ==  block_to_brodcast.hash_block():
                #     """ Блок клиенту уже кидали """
                #     continue

                if client.is_connected:
                    req = {'command': 'invb', 'block_hash': block_to_brodcast.hash_block()}
                    response = client.send_request(req)

                    if response is not None and response.get('status') == 'ok':
                        # client.last_broadcast_block == block_to_brodcast.hash_block()
                        if len(blocks) > 0:
                            self.blocks_to_broadcast[adress] = blocks

                    if response is not None and response.get('status') == 'get':
                        # клиенту нужен блок
                        response = client.send_request(
                            {'command': 'newblock',
                             'block_data': block_to_brodcast.to_json()})

                        # print(f"Broadcast new block {block_to_brodcast.hash_block()}")

                        if "block_candidate" in response:
                            candidate_json = response.get("block_candidate")
                            candidate = Block.from_json(candidate_json)
                            if self.chain.add_block_candidate(candidate):
                                print(f"Блок от {adress} верный. Добавляем в цепь")
                                self.distribute_block(self.chain.block_candidate, ban_address=adress)
                            # else:
                            # print("!!!!!!!!!!!!!!!!!!!!!!!!!")
                            # print("Нода считает верным блок", candidate.hash_block() )
                            # self.chain.add_block_candidate(candidate)
                        # print(response)



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
                self.distribute_block(self.chain.block_candidate, ban_address=peer)
            else:
                # print("Кандидат с ноды не подходит", blockcandidate.hash)
                self.distribute_block(self.chain.block_candidate, address=peer)

    def check_synk_with_peers(self):
        """ Проверка синхронности с пирами """

        count_peers = 0
        count_sync_peers = 0
        # print("check_synk_with_peers",  self.peers.keys())
        block_sync = True
        chain_size = 0
        self.no_need_pause_sinc = True


        for client in list(self.peers.values()):

            # себя не смотрим
            if client.address() == self.server.address or client.address() == self.server.address:
                continue

            count_peers += 1

            # client.info = client.send_request({'command': 'getinfo'})
            client.get_info()

            peer_info = client.info
            # print("peer_info", peer_info)

            if peer_info is None:
                continue

            if peer_info is not None and "synced" in peer_info:

                if peer_info.get('synced') == "True":
                    # print(peer_info)
                    count_sync_peers+=1
                    chain_size = max(chain_size, peer_info['block_count'])
                    # print("Узел синхронный, проверяем состояние")
                    # print(peer_info)

                    # нода синхронна
                    if self.synced:

                        if peer_info['block_candidat'] != self.chain.block_candidate_hash:
                            if not self.chain.check_hash(peer_info['block_candidat']):
                                print(f"Расхождение блока кандидата {peer_info['block_candidat']}, на ноде{client.address()}делаем запрос")
                                self.pull_candidat_block_from_peer(client.address())

                        continue


                    if peer_info['block_count'] > self.chain.blocks_count():

                        # print(f"На узле {client.address()} блоков больше, подгружаем")
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
                                if int(block_num) % 100 == 0:
                                    self.chain.save_chain_to_disk(dir=str(self.server.address))
                                self.no_need_pause_sinc = True
                            else:
                                print(f"Invalid block {block_num} received from {client.address()}.")
                                "Возникает ситуация, когда своя цепочка не сопадает с присылаемой"
                                "Тут надо делать более сложный форк"
                                "Пока просто откатываемся на несколько блоков назад"
                                "Нужна правильная отработка отката транзакций"
                                self.chain.blocks = self.chain.blocks[:-1]
                                self.chain.reset_block_candidat()
                        continue
                    # if peer_info['block_count'] < self.chain.blocks_count():
                    #     print("На синхронной ноде меньше блоков чем на текущей!")
                    #     """ тут требуется более глубокий синхрон """
                    #     """ Как временное решение срубание блоков """
                    #     self.chain.blocks = self.chain.blocks[:-1]
                    #     self.chain.reset_block_candidat()

                    # если количество блоков равно, доп проверки
                    if peer_info['block_count'] == self.chain.blocks_count():

                        if self.chain.block_candidate_hash is not None and peer_info['block_candidat'] is not None:
                            if peer_info['block_candidat'] != self.chain.block_candidate_hash:
                                # print("!!! Не совпадает кандидат, требуется обмен")
                                self.pull_candidat_block_from_peer(client.address())
                                # self.distribute_block(self.chain.block_candidate, address=client.address())

                        # if peer_info['last_block_hash'] != self.chain.last_block_hash():
                        #     # print("!!! Не совпадает последний блок", peer_info['last_block_hash'])
                        #     # self.ping_peer(client.address())
                        #     self.distribute_block(self.chain.block_candidate)

        if block_sync and not self.synced and self.chain.blocks_count() == chain_size and chain_size != 0:

            # if  (self.time_ntpt.get_corrected_time() - self.chain.last_block().time>3 and
            # если блок близок к закрытию, то ждем следующий
            if self.time_ntpt.get_corrected_time() - self.chain.last_block().time < Protocol.BLOCK_TIME_INTERVAL / 5:
                print("Блоки синхронизированные:", self.chain.blocks_count())
                print(self.chain.last_block_hash())

                self.synced = True
                print("Нода синхронизированна!")


        # if self.synced and self.chain.blocks_count() < chain_size and chain_size != 0:
        #     self.synced = False
        #     print("Нода потеряла синхронизацию!")
        #
        # # примерный алгоритм отслеживания синхронизации сети
        # count_s = 0
        # all_peers = 0
        # for client in list(self.peers.values()):
        #
        #     if client.info is None:
        #         continue
        #
        #     if client.info.get('synced') != "True":
        #         continue
        #     # себя не смотрим
        #     if client.address() == self.server.address or client.server_address == self.server.address:
        #         continue
        #
        #     all_peers += 1
        #     if client.info['block_count'] >= self.chain.blocks_count():
        #         if client.info['last_block_hash'] == self.chain.last_block_hash():
        #             count_s += 1
        # # простая проверка, количества нод с которыми совпадают блоки
        # if self.chain.last_block() is not None:
        #     if (time.time() - self.chain.last_block().time > 10
        #     and time.time() - self.chain.last_block().time < Protocol.BLOCK_TIME_INTERVAL-10
        #             and count_s < all_peers):
        #         # print("CCCCC")
        #         if self.synced:
        #             print(f"в сети есть рассинхрон {count_s} из {all_peers}")
        #             if all_peers > 1 and count_s == 0:
        #                 print(f"Текущая цепь в меньшинстве")
        #                 print("Нода потеряла синхронизацию!")
        #                 self.synced = False

        if count_sync_peers == 0:
            if self.time_ntpt.get_corrected_time() > self.start_time + Protocol.WAIT_ACTIVE_PEERS_BEFORE_START:
                if not self.synced:
                    print("Ноды не обнаружены, включаем синхронизацию")
                    self.synced = True

    def check_peers(self):
        """ Проверка доступных нод, выбор ближайших соседей """

        t = time.time() - 11
        pause_mempool = time.time()
        pause_synced = time.time()

        try:
            thread = threading.Thread(target=self._ping_all_peers_and_save)
            thread.daemon = True
            thread.start()
        except Exception as e:
            print("_ping_all_peers_and_save", e)

        while self.running:

            # try:

                # if time.time() - t > 10:
                #     # thread = threading.Thread(target=self._ping_all_peers_and_save)
                #     # thread.daemon = True
                #     # thread.start()
                #     self._ping_all_peers_and_save()
                #     t = time.time()

                if len(self.peers_to_broadcast) > 0:
                    self.broadcast_new_peer()

                if time.time() - pause_synced > 1:
                    # если засинхрились, то проверка реже

                    self.check_synk_with_peers()
                    if not self.no_need_pause_sinc:
                        pause_synced = time.time()

                if not self.synced:
                    # self.check_synk_with_peers()
                    time.sleep(0.1)
                    continue

                    # if len(self.list_need_broadcast_transaction) > 0:
                #     for tx in self.list_need_broadcast_transaction:
                #         self.broadcast_new_transaction(tx)

                if len(self.blocks_to_broadcast) > 0:
                    try:
                        self.broadcast_blocks()
                    except Exception as e:
                        print("blocks_to_broadcast", e)

                if time.time() - pause_mempool > 10:
                    for peer in list(self.active_peers()):
                        if self.server.address != peer:
                            try:
                                self.take_mempool(peer)
                            except Exception as e:
                                print(e)

                    pause_mempool = time.time()

                time.sleep(0.1)  # Пауза перед следующей проверкой
            # except Exception as e:
            #     print("check_peers", e)
