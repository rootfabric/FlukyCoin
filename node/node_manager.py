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

        # self.wallet_address = config.get("address")
        # self.log.info(f"Blockchain Node address {self.wallet_address}")



        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        # self.initial_peers.append(self.address)
        self.version = Protocol.VERSION

        self.time_ntpt = NTPTimeSynchronizer(log=log)


        self.mempool = Mempool(config)

        self.chain = Chain(config=self.config, mempool=self.mempool, log=self.log)

        # self.miners_storage = MinerStorage(dir=str(self.address))

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


    def run_node(self):
        """ Основной цикл  """
        timer_get_nodes = time.time()
        while True:

            self.client_handler.ping_peers()

            self.client_handler.connect_to_peers()

            self.client_handler.fetch_info_from_peers()

            if timer_get_nodes+Protocol.TIME_PAUSE_GET_PEERS<time.time():
                timer_get_nodes = time.time()
                self.client_handler.get_peers_list()

            print("-------------------")
            print(self.mempool.transactions.keys())
            time.sleep(5)

