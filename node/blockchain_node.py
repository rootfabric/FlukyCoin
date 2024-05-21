import time

from core.block import Block
from core.transaction import Transaction
from core.protocol import Protocol
from storage.mempool import Mempool
from storage.chain import Chain
import signal
import datetime
from net.client import Client
from net.network_manager import NetworkManager
from tools.time_sync import NTPTimeSynchronizer


class BlockchainNode:
    def __init__(self, config):

        self.config = config
        # self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        # self.host = config.get("host", "localhost")
        # self.port = config.get("port", "5555")
        self.address = config.get("address")
        print(f"Blockchain Node address {self.address}")

        self.time_ntpt = NTPTimeSynchronizer()

        self.running = True

    def init_node(self):
        signal.signal(signal.SIGINT, self.signal_handler)  # Установка обработчика сигнала

        self.mempool = Mempool(dir=str(f'{self.config.get("host", "localhost")}:{self.config.get("port", "5555")}'))

        self.chain = Chain(config=self.config, mempool=self.mempool )

        self.network_manager = NetworkManager(self.handle_request, config=self.config, mempool=self.mempool,
                                              chain=self.chain, time_ntpt=self.time_ntpt)

        self.protocol = Protocol()
        self.uuid = self.protocol.hash_to_uuid(self.network_manager.server.address)

        print("Blockchain Node initialized", self.network_manager.server.address, "uuid", self.uuid)

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
            txid = request.get('tx_id')
            return self.get_transaction(txid)
        elif command == 'newpeer':
            peer = request.get('peer')
            return self.add_peer(peer)
        elif command == 'invt':
            return self.new_inv_transaction(request)
        elif command == 'invb':
            return self.new_inv_block(request)
        elif command == 'tx':
            tx_data = request.get('tx_data')
            return self.add_transaction(tx_data)
        elif command == 'mempool':
            # print("mempool", self.mempool.get_hashes())
            return {"mempool_hashes": self.mempool.get_hashes()}
        elif command == 'newblock':
            block = request.get('block_data')
            return self.receive_new_block(block)
        elif command == 'peerhello':
            peer = request.get('peer')
            return self.register_peer(peer)
        elif command == 'getpeers':
            return self.send_peers_list()
        else:
            return {'error': 'Unknown command'}

    def new_inv_transaction(self, request):
        """ новый хеш """

        tx_hash = request.get("tx")
        if tx_hash is not None:
            # сообщение с хешем транзакции , надо проверить на наличие
            if not self.mempool.chech_hash_transaction(tx_hash) and self.network_manager.synced:
                # транзакции нет
                return {"status": "get"}
            else:
                return {"status": "ok"}

    def new_inv_block(self, request):
        """ новый хеш """

        block_hash = request.get("block_hash")
        if block_hash is not None:
            # сообщение с хешем  , надо проверить на наличие

            if self.chain.check_hash(block_hash) is None:
                # транзакции нет
                return {"status": "get"}
            else:
                return {"status": "ok"}

    def add_transaction(self, transaction_data):
        """ Добавление транзакции """
        tx = Transaction.from_json(transaction_data['tx_json'])
        tx.sign = tx.sign_from_str(transaction_data['tx_sign'])
        tx.make_hash()

        if self.mempool.add_transaction(tx):
            print("Добавлена транзакция")
            self.network_manager.list_need_broadcast_transaction.append(tx)

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
        answ = {'synced': f'{self.network_manager.synced}', 'node': f'{self.network_manager.server.address}',
                'version': Protocol.VERSION,
                'peers': self.network_manager.known_peers,
                'block_count': self.chain.blocks_count(),
                'block_candidat': self.chain.block_candidate_hash,
                'last_block_hash': self.chain.last_block_hash()
                }
        # print("get_info", "block_candidat", answ['block_candidat'])
        return answ

    def get_block(self, block_number):
        block = self.chain.blocks[block_number]
        mess = {'block': block.to_json()}
        return mess

    def get_block_candidate(self):
        block_candidate = self.chain.block_candidate
        mess = {'block_candidate': block_candidate.to_json() if block_candidate is not None else None}
        return mess

    def get_transaction(self, txid):
        tx = self.mempool.transactions.get(txid)
        return {'command': 'tx', 'tx_data': {'tx_json': tx.to_json(), 'tx_sign': tx.sign}}

    def add_peer(self, peer):
        if peer not in self.network_manager.known_peers:
            print("Add new peer", peer)
            self.network_manager.add_known_peer(peer)

        # self.network_manager.list_need_broadcast_peers.append(peer)

        return {'status': 'success', 'message': f'Peer {peer} added'}

    def receive_new_block(self, block_json):
        """ Проверка блока """
        block = Block.from_json(block_json)
        if self.chain.add_block_candidate(block):
            # print(f"Кандидат из другой ноды доставлен:{block.datetime()} {block.hash}")
            self.network_manager.distribute_block(block)

            return {'status': 'success', 'message': 'New block received and distributed'}
        # print(f"Кандидат из другой ноды не подходит:{block.datetime()} {block.hash}")

        return {'status': 'fail', 'message': 'Block wrong', "block_candidate": self.chain.block_candidate.to_json()}

    def signal_handler(self, signal, frame):
        print('Ctrl+C captured, stopping server and shutting down...')
        self.stop()  # Ваш метод для остановки сервера и закрытия потоков

    def create_block(self):
        """ """

        last_block = self.chain.last_block()
        previousHash = None if last_block is None else last_block.hash_block()

        block = Block(previousHash)

        block.signer = self.address

        last_block_time = self.chain.last_block().time if self.chain.last_block() is not None else self.chain.time()

        # last_block_date = datetime.datetime.fromtimestamp(last_block_time)

        time_candidat = last_block_time + Protocol.BLOCK_TIME_INTERVAL
        # синхронизированное время цепи
        block.time = time_candidat if time_candidat > self.chain.time_ntpt.get_corrected_time() else self.chain.time_ntpt.get_corrected_time()

        # print(f"Create time: last_block_date{last_block_date}  candidat:{datetime.datetime.fromtimestamp(block.time)}")

        # is_key_block = self.protocol.is_key_block(block.previousHash)
        # print(f"Key block: {is_key_block}")

        # создание блока со своим адресом

        seq_hash = self.protocol.sequence(block.previousHash)

        reward, ratio, lcs = self.protocol.reward(self.address, seq_hash)
        # print("seq_hash", seq_hash)

        tr = Transaction(tx_type="coinbase", fromAddress="0000000000000000000000000000000000",
                         toAddress=self.address, amount=reward)
        block.add_transaction(tr)

        block.hash_block()

        return block

    def run_node(self):

        # blockchain_node = BlockchainNode(server)
        self.init_node()
        # self.add_peer(f"{address}:{port}")
        self.network_manager.run()

        # self.network_manager.sync_node()

        self.main_loop()

    def main_loop(self):
        """ В главный цикл работы попадаем когда нода синхронизованная """
        signal.signal(signal.SIGINT, self.signal_handler)

        print("Blockchain Node is running")

        while self.running:
            try:
                # не работаем без синхронизации
                if not self.network_manager.synced:
                    time.sleep(0.1)
                    # print("Node not sync!")
                    continue

                # print("mempool", len(self.mempool.transactions))

                # continue

                # сгенегрировать блок, и попробовать добавить его в блокчейн

                new_block = self.create_block()

                if self.chain.add_block_candidate(new_block):
                    print(f"{datetime.datetime.now()} Собственный Блок кандидат добавлен", new_block.hash,
                          new_block.datetime())
                    self.network_manager.distribute_block(self.chain.block_candidate)

                needClose = self.chain.need_close_block()

                print(
                    # f"Check: {self.chain.blocks_count()} peers[{self.network_manager.active_peers()}] txs[{self.mempool.size()}] delta: {self.chain.block_candidate.time - self.time_ntpt.get_corrected_time():0.2f}  {self.chain.block_candidate.hash_block()[:5]}...{self.chain.block_candidate.hash_block()[-5:]}  singer: ...{self.chain.block_candidate.signer[-5:]}")
                    f"Check: {self.chain.blocks_count()} peers[{len(self.network_manager.active_peers())}] txs[{self.mempool.size()}] delta: {self.chain.block_candidate.time - self.time_ntpt.get_corrected_time():0.2f}  {self.chain.block_candidate.hash_block()[:5]}...{self.chain.block_candidate.hash_block()[-5:]}  singer: ...{self.chain.block_candidate.signer[-5:]}")

                # print([(p.address(), "" if p.info.get('block_candidat') is None else f"{p.info['block_candidat'][:5]}")
                #        for p in self.network_manager.peers.values()])

                try:
                    if needClose and self.chain.block_candidate is not None:
                        print("*******************", self.network_manager.active_peers())
                        print(f"Время закрывать блок: {self.chain.blocks_count()}")
                        if not self.chain.close_block():
                            print("last_block", self.chain.last_block_hash())
                            print("candidate", self.chain.block_candidate_hash)
                            self.chain.reset_block_candidat
                            time.sleep(0.45)
                            continue
                        last_block = self.chain.last_block()
                        if last_block is not None:
                            print(f"Chain {len(self.chain.blocks)} blocks , последний: ", last_block.hash_block(),
                                  last_block.signer)

                        self.chain.save_chain_to_disk(dir=str(self.network_manager.server.address))

                        print(f"{datetime.datetime.now()} Дата закрытого блока: {self.chain.last_block().datetime()}")
                        if self.protocol.is_key_block(self.chain.last_block().hash):
                            print("СЛЕДУЮЩИЙ КЛЮЧЕВОЙ БЛОК")
                        print("*******************")
                        continue
                except Exception as e:
                    print("Ошибка основного цикла", e)
                # if needClose and self.chain.block_candidate is not None:
                #     self.chain.close_block()
                #     print("Закрываем блок", self.chain.last_block().hash)

                # current_datetime = self.time_ntpt.get_corrected_datetime()

                time_to_close = Protocol.BLOCK_TIME_INTERVAL_LOG
                if self.chain.last_block() is not None:
                    time_block = self.chain.last_block().time
                    time_to_close_block = self.time_ntpt.get_corrected_time() - time_block
                    if time_to_close_block < time_to_close and time_to_close_block > 0:
                        time_to_close = time_to_close - time_to_close_block

                time.sleep(time_to_close)

                #
                # # Вычисляем, сколько миллисекунд осталось до следующей секунды
                # milliseconds_to_wait = 1000 - (current_datetime.microsecond // 1000)
                # # Добавляем задержку в секундах (преобразуем миллисекунды в секунды)
                # time.sleep(milliseconds_to_wait / 1000.0)
                #
                # # print(f"Chain {len(self.chain.blocks)} blocks")
            except Exception as e:
                print("error main loop ", e)


if __name__ == "__main__":
    """ """
