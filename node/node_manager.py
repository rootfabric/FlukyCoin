"""

Управление нодой

"""
import time

from core.Block import Block
from core.Transactions import Transaction
from core.protocol import Protocol
from storage.mempool import Mempool
from storage.miners_storage import MinerStorage
from storage.chain import Chain
import signal
import datetime
from net.client import Client
from net.network_manager import NetworkManager
from tools.time_sync import NTPTimeSynchronizer
from tools.logger import Log
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from net.GrpcServer import GrpcServer
from net.ClientHandler import ClientHandler

class NodeManager:
    """

    """

    def __init__(self, config, log=Log()):
        self.log = log
        self.config = config

        if "is_miner" not in self.config:
            self.config['is_miner'] = False
        # self.wallet_address = config.get("address")
        # self.log.info(f"Blockchain Node address {self.wallet_address}")



        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        # self.initial_peers.append(self.address)
        self.version = Protocol.VERSION

        self.time_ntpt = NTPTimeSynchronizer(log=log)


        self.mempool = Mempool(config)

        self.chain = Chain(config=self.config, mempool=self.mempool, log=self.log)

        self.miners_storage = MinerStorage(config)

        self.server = GrpcServer(self.config, self)
        self.client_handler = ClientHandler(self.server.servicer, self)

        self.server.start()

        self.block_candidate = "123"

        self.synced = False
        self.running = True

    def add_transaction_to_mempool(self, transaction):
        """ ДОбавление новой транзакции """

        if not self.mempool.chech_hash_transaction(transaction.txhash):

            """ Требуется провести валидацию, и возможно перетащить метод из основного класса """

            print("Добавлена новая транзакция", transaction.txhash)
            self.mempool.add_transaction(transaction)

    def create_block(self):
        """ """

        last_block = self.chain.block_candidate

        """ требуется откат индекса секретного колюча, если свой блок перебит"""

        if last_block is not None and last_block.signer in self.miners_storage.keys:
            return None

        for miner_address in list(self.miners_storage.keys.keys()):

            for address_miner in self.miners_storage.keys.keys():
                if self.chain.try_address_candidate(address_miner, miner_address):
                    miner_address = address_miner

            if last_block is not None:
                if self.chain.try_address_candidate(last_block.signer, miner_address):
                    # self.log.info("Кандидат сильнее")
                    return None

            # Лучший блок
            if last_block is not None and miner_address == last_block.signer:
                # self.log.info("кандидат устоял")
                return None

            if miner_address in self.miners_storage.keys and self.miners_storage.keys[miner_address].count_sign() <= 0:
                self.log.info("Кончились подписи", miner_address)
                del self.miners_storage.keys[miner_address]
                continue

            if miner_address not in self.miners_storage.keys:
                continue

            self.log.info(
                f"miner_address: {miner_address} count signs: {self.miners_storage.keys[miner_address].count_sign()}")

            # берем ключ из хранилища
            xmss = self.miners_storage.keys[miner_address]

            next_idx = self.chain.next_address_nonce(miner_address)
            if xmss.keyPair.SK.idx != next_idx - 1:
                self.log.info(f"xmss.keyPair.SK.idx {xmss.keyPair.SK.idx}")
                xmss.keyPair.SK.idx = next_idx - 1
                self.log.warning("Не верное количество подписей между ключом и цепью. Ставим количество цепи")

            """ Сбор блока под выбранный адрес """
            self.log.info("Свой адрес победил, создаем блок")

            last_block_time = self.chain.last_block().timestamp_seconds if self.chain.last_block() is not None else self.chain.time()

            time_candidat = last_block_time + Protocol.BLOCK_TIME_INTERVAL
            # синхронизированное время цепи
            block_timestamp_seconds = time_candidat if time_candidat > self.chain.time_ntpt.get_corrected_time() else self.chain.time_ntpt.get_corrected_time()

            # создание блока со своим адресом
            transacrions = []
            # block.hash_block()
            block_candidate = Block.create(self.chain.blocks_count(), self.chain.last_block_hash(),
                                           block_timestamp_seconds, transacrions, address_miner=xmss.address,
                                           address_reward=self.config.get("address_reward"))

            block_candidate.make_sign(xmss)

            self.log.info("Блок создан", block_candidate.hash_block())

            if not self.chain.validate_block(block_candidate):
                self.log.info("Блок не прошел валидацию")
                block_candidate = None
            else:
                self.miners_storage.save_storage_to_disk(block_candidate)

            return block_candidate

        self.log.error("Нет подписей")
        self.miners_storage.generate_keys()
        self.create_block()

    def run_node(self):
        """ Основной цикл  """
        timer_get_nodes = 0
        while True:

            self.client_handler.ping_peers()

            self.client_handler.connect_to_peers()

            self.client_handler.fetch_info_from_peers()

            if timer_get_nodes+Protocol.TIME_PAUSE_GET_PEERS<time.time():
                timer_get_nodes = time.time()

                self.client_handler.get_peers_list()

                self.client_handler.fetch_transactions_from_all_peers()

            if len(self.server.servicer.active_peers)==1:
                self.synced = True
                continue

            # if self.config.get('is_miner', "False"):
            #     print(f"---is_miner {self.config.get('is_miner', 'False')}----------------")
            #     print(len(self.mempool.transactions.keys()), self.mempool.transactions.keys())
            #     time.sleep(5)
            #     continue

            new_block = None
            if self.config.get('is_miner', "False"):
                new_block = self.create_block()
            else:
                print(f"---is_miner {self.config.get('is_miner', 'False')}----------------")
                print(len(self.mempool.transactions.keys()), self.mempool.transactions.keys())

            # new_block = self.create_block()

            if self.chain.add_block_candidate(new_block):
                self.log.info(f"{datetime.datetime.now()} Собственный Блок кандидат добавлен", new_block.hash,
                              new_block.signer)
                # self.network_manager.distribute_block(self.chain.block_candidate)
                print("self.server.servicer.active_peers", self.server.servicer.active_peers)
                self.client_handler.distribute_block(self.chain.block_candidate)

            needClose = self.chain.need_close_block()
            if needClose and self.chain.block_candidate is not None:
                self.log.info("*******************", )
                self.log.info(f"Время закрывать блок: {self.chain.blocks_count()}")
                if not self.chain.close_block():
                    self.log.info("last_block", self.chain.last_block_hash())
                    self.log.info("candidate", self.chain.block_candidate_hash)
                    self.chain.reset_block_candidat
                    time.sleep(0.45)
                    continue
                last_block = self.chain.last_block()
                if last_block is not None:
                    self.log.info(f"Chain {len(self.chain.blocks)} blocks , последний: ", last_block.hash_block(),
                                  last_block.signer)

                self.chain.save_chain_to_disk()

                self.log.info(f"{datetime.datetime.now()} Дата закрытого блока: {self.chain.last_block().datetime()}")
                if Protocol.is_key_block(self.chain.last_block().hash):
                    self.log.info("СЛЕДУЮЩИЙ КЛЮЧЕВОЙ БЛОК")
                self.log.info("*******************")
                continue

            if self.chain.block_candidate is not None:
                self.log.info(
                    # f"Check: {self.chain.blocks_count()} peers[{self.network_manager.active_peers()}] txs[{self.mempool.size()}] delta: {self.chain.block_candidate.time - self.time_ntpt.get_corrected_time():0.2f}  {self.chain.block_candidate.hash_block()[:5]}...{self.chain.block_candidate.hash_block()[-5:]}  singer: ...{self.chain.block_candidate.signer[-5:]}")
                    f"Check: {self.chain.blocks_count()} peers[{len(self.server.servicer.active_peers)}] txs[{self.mempool.size()}] delta: {self.chain.block_candidate.timestamp_seconds - self.time_ntpt.get_corrected_time():0.2f}  {self.chain.block_candidate.hash_block()[:5]}...{self.chain.block_candidate.hash_block()[-5:]}  singer: ...{self.chain.block_candidate.signer[-5:]}")


            print("-------------------")
            print(len(self.mempool.transactions.keys()), self.mempool.transactions.keys())
            time.sleep(5)

