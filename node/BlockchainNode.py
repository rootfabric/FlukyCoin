
import sys
import time

from core.chain import Chain
from core.block import Block
from core.transaction import Transaction
from core.protocol import Protocol
import signal
import yaml
import datetime
from net.server import Server
from net.client import Client
from net.network_manager import NetworkManager
from tools.time_sync import NTPTimeSynchronizer

from tqdm import tqdm


class BlockchainNode:
    def __init__(self, config):

        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        self.host = config.get("host", "localhost")
        self.port = config.get("port", "5555")
        self.address = config.get("address")
        print(f"Blockchain Node address {self.address}")

        # синхронизирована нода с блокчейном
        self.synced = False

        self.time_ntpt = NTPTimeSynchronizer()

        self.running = True

    def init_node(self):
        signal.signal(signal.SIGINT, self.signal_handler)  # Установка обработчика сигнала


        self.network_manager = NetworkManager(self.running, self.handle_request, host=self.host, port=self.port, initial_peers=self.initial_peers)


        self.protocol = Protocol()
        self.uuid = self.protocol.hash_to_uuid(self.network_manager.server.address)

        print("Blockchain Node initialized", self.network_manager.server.address, "uuid", self.uuid)



        # self.chain = Chain()
        #
        # #  простая хранилка
        # self.chain.load_from_disk(dir=str(self.server.address))



    def stop(self):
        self.running = False
        if hasattr(self, 'network_manager'):
            self.network_manager.stop()

    def handle_request(self, request):
        command = request.get('command')

        # print(f"Command: {request}")

        if command == 'getinfo':
            return self.get_info()
        elif command == 'getblock':
            block_number = request.get('block_number')
            return self.get_block(block_number)
        elif command == 'getblockcandidate':
            return self.get_block_candidate()
        elif command == 'gettransaction':
            txid = request.get('txid')
            return self.get_transaction(txid)
        elif command == 'newpeer':
            peer = request.get('peer')
            return self.add_peer(peer)
        elif command == 'newblock':
            block = request.get('block')
            return self.receive_new_block(block)
        elif command == 'peerhello':
            peer = request.get('peer')
            return self.register_peer(peer)
        elif command == 'getpeers':
            return self.send_peers_list()
        else:
            return {'error': 'Unknown command'}

    def send_peers_list(self):
        return {'peers': self.network_manager.active_peers()}

    def send_hello(self, peer):
        client = Client(peer.split(":")[0], int(peer.split(":")[1]))
        response = client.send_request({'command': 'peerhello', 'peer': self.server.address})
        client.close()
        print("Hello response:", response)
        return response

    def register_peer(self, peer):
        if peer not in self.network_manager.get_active_peers():
            self.known_peers.append(peer)
            self.broadcast_new_peer(peer)
        return {'status': 'success', 'message': f'Welcome, {peer}, registered successfully'}

    def request_peers_list(self, peer):
        client = Client(peer.split(":")[0], int(peer.split(":")[1]))
        response = client.send_request({'command': 'getpeers'})
        print("Peers list response:", response)
        for p in response.get('peers', []):
            if p not in self.known_peers:
                self.known_peers.append(p)
        client.close()

    def get_info(self):
        return {'synced': f'{self.synced}', 'node': f'{self.network_manager.server.address}',
                'version': self.protocol.version,
                'peers': self.network_manager.known_peers,
                # 'block_count': self.chain.blocks_count()
                }

    def get_block(self, block_number):
        block = self.chain.blocks[block_number]
        return {'block': block.to_json()}

    def get_block_candidate(self):
        block_candidate = self.chain.block_candidate
        return {'block_candidate': block_candidate.to_json()}

    def get_transaction(self, txid):
        return {'transaction': 'details', 'txid': txid}

    def add_peer(self, peer):
        if peer not in self.network_manager.known_peers:
            print("Add new peer", peer)
            self.network_manager.add_known_peer(peer)

        # self.network_manager.list_need_broadcast_peers.append(peer)

        return {'status': 'success', 'message': f'Peer {peer} added'}

    def receive_new_block(self, block_json):

        block = Block.from_json(block_json)
        if self.chain.add_block_candidate(block):
            if self.chain.add_block_candidate(block):
                print(f"Кандидат из другой ноды доставлен:{block.datetime()} {block.hash}")
                self.distribute_block(block)

                return {'status': 'success', 'message': 'New block received and distributed'}

        return {'status': 'fail', 'message': 'Block wrong'}

    def distribute_block(self, block):
        print("distribute_block get_active_peers", self.network_manager.get_active_peers())
        for peer in self.network_manager.get_active_peers():

            # самому себе блок не транслируем
            if peer == self.server.address:
                continue
            client = Client(peer.split(":")[0], int(peer.split(":")[1]))
            print("distribute_block ", peer)
            client.send_request({'command': 'newblock', 'block': block.to_json()})
            client.close()

    def pull_candidat_block_from_peer(self, peer):
        client = Client(peer.split(":")[0], int(peer.split(":")[1]))
        #отдельно берем кандидата
        answer = client.send_request({'command': 'getblockcandidate'})

        blockcandidate_json = answer.get("block_candidate")
        if blockcandidate_json is not None:
            blockcandidate = Block.from_json(blockcandidate_json)
            if self.chain.add_block_candidate(blockcandidate):
                print("Добавлен кандидат с ноды", blockcandidate.hash)
        client.close()
    def pull_blocks_from_peer(self, peer, start_block, end_block):
        client = Client(peer.split(":")[0], int(peer.split(":")[1]))
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

    def sync_node(self):
        # Проверяем, есть ли у всех известных узлов такое же количество блоков, как и у текущего узла
        current_block_count = len(self.chain.blocks)
        print(f"Checking synchronization status with {len(self.known_peers)} peers...")
        for peer in self.network_manager.get_active_peers():

            if peer == self.server.address:
                continue

            client = Client(peer.split(":")[0], int(peer.split(":")[1]))

            response = client.send_request({'command': 'newpeer', 'peer': self.server.address})
            print(response)

            response = client.send_request({'command': 'getinfo'})
            peer_block_count = response.get('block_count', 0)
            client.close()

            # Если количество блоков различается, начинаем процесс синхронизации
            if peer_block_count != current_block_count:
                print(f"Synchronization needed with {peer}.")
                self.pull_blocks_from_peer(peer, current_block_count, peer_block_count)
            else:
                print(f"{peer} is synchronized.")

            self.pull_candidat_block_from_peer(peer)


        print(f"Synchronization check completed. Nodes count {len(self.network_manager.get_active_peers())}")
        print(f"Blocks: {self.chain.blocks_count()}")
        if self.chain.last_block() is not None:
            print(f"{datetime.datetime.fromtimestamp(self.chain.last_block().time)}")

        self.synced = True  # Обновляем статус синхронизации

    def signal_handler(self, signal, frame):
        print('Ctrl+C captured, stopping server and shutting down...')
        self.stop()  # Ваш метод для остановки сервера и закрытия потоков


    def create_block(self):
        """ """

        last_block = self.chain.last_block()
        previousHash = None if last_block is None else last_block.hash

        block = Block(previousHash)

        last_block_time =self.chain.last_block().time if self.chain.last_block() is not None else self.chain.time()

        last_block_date = datetime.datetime.fromtimestamp(last_block_time)

        time_candidat = last_block_time+Protocol.block_interval()
        # синхронизированное время цепи
        block.time = time_candidat if time_candidat>self.chain.time_ntpt.get_corrected_time() else self.chain.time_ntpt.get_corrected_time()

        # print(f"Create time: last_block_date{last_block_date}  candidat:{datetime.datetime.fromtimestamp(block.time)}")

        is_key_block = self.protocol.is_key_block(block.previousHash)
        # print(f"Key block: {is_key_block}")

        if is_key_block:
            # создание блока со своим адресом

            seq_hash = self.protocol.sequence(block.previousHash)

            reward, ratio, lcs = self.protocol.reward(self.address, seq_hash)
            # print("seq_hash", seq_hash)

            tr = Transaction("0000000000000000000000000000000000", self.address, reward)
            block.add_transaction(tr)
            # print(tr.to_json())

            block.winer_ratio = ratio
            block.winer_address = self.address

            block.hash_block()

            return block

        # если блок не ключевой, чекаем, есть ли мы в транзакциях
        if not is_key_block:

            # if self.address not in self.chain.transaction_storage.balances:
            #     return None

            # addrs = self.chain.transaction_storage.balances.keys()
            # if self.address in addrs:

                seq_hash = self.protocol.sequence(block.previousHash)

                reward, ratio, lcs = self.protocol.reward(self.address, seq_hash)

                tr = Transaction("0000000000000000000000000000000000", self.address, reward)
                block.add_transaction(tr)
                # print(tr.to_json())

                block.winer_ratio = ratio
                block.winer_address = self.address

                block.hash_block()

                return block

    def run_node(self):

        # blockchain_node = BlockchainNode(server)
        self.init_node()
        # self.add_peer(f"{address}:{port}")
        self.network_manager.run()
        # self.sync_node()
        self.main_loop()


    def main_loop(self):
        """ В главный цикл работы попадаем когда нода синхронизованная """
        # Здесь могут быть выполнены задачи по проверке блокчейна, созданию блоков, обновлению состояний и т.д.

        print("Blockchain Node is running")

        while self.running:
            time.sleep(1)
            continue

            # сгенегрировать блок, и попробовать добавить его в блокчейн

            new_block = self.create_block()

            if self.chain.add_block_candidate(new_block):
                print( f"{datetime.datetime.now()} Собственный Блок кандидат добавлен", new_block.hash, new_block.datetime())
                self.distribute_block(self.chain.block_candidate)
            # else:
            #     print("Собственный Блок ниже по уровню")

            needClose = self.chain.need_close_block()

            if needClose and self.chain.block_candidate is not None:
                print("Нужно закрывать блок: ", needClose)
                self.chain.close_block()
                print(f"Chain {len(self.chain.blocks)} blocks , последний: ", self.chain.last_block().hash,
                      self.chain.last_block().winer_address)

                self.chain.save_to_disk(dir=str(self.server.address))

                print(f"{datetime.datetime.now()} Дата закрытого блока: {self.chain.last_block().datetime()}")
            #
            # if needClose and self.chain.block_candidate is not None:
            #     self.chain.close_block()
            #     print("Закрываем блок", self.chain.last_block().hash)

            current_datetime = self.time_ntpt.get_corrected_datetime()
            # Вычисляем, сколько миллисекунд осталось до следующей секунды
            milliseconds_to_wait = 1000 - (current_datetime.microsecond // 1000)
            # Добавляем задержку в секундах (преобразуем миллисекунды в секунды)
            time.sleep(milliseconds_to_wait / 1000.0)


            # print(f"Chain {len(self.chain.blocks)} blocks")


if __name__ == "__main__":

    """ """