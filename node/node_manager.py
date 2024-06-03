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

        self.wallet_address = config.get("address")
        self.log.info(f"Blockchain Node address {self.wallet_address}")


        self.address = f"{self.config.get('host')}:{self.config.get('port')}"
        self.initial_peers = config.get("initial_peers", ["localhost:5555"])
        self.initial_peers.append(self.address)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", "5555")

        self.time_ntpt = NTPTimeSynchronizer(log=log)

        self.running = True

    def run_node(self):
        """ """
        # local_address = 'localhost:50051'
        local_address = self.address
        version = Protocol.VERSION
        # initial_peers = ['localhost:50051'] + [local_address]
        node_manager = NodeManager(self.config)
        server = GrpcServer(local_address, version, node_manager)
        client_handler = ClientHandler(server.servicer)

        server.start()


        while True:



            client_handler.connect_to_peers(set(list(server.servicer.active_peers)))

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(server.servicer.check_active, peer): peer for peer in server.servicer.known_peers}
                active_peers = {futures[future] for future in as_completed(futures) if future.result()}
                server.servicer.active_peers = active_peers
                print("Active peers updated.", active_peers)
            # Обновляем список активных пиров
            # server.servicer.active_peers = {peer for peer in server.servicer.known_peers if
            #                                 server.servicer.check_active(peer)}
            print("-------------------")
            time.sleep(5)

