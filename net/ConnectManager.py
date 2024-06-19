"""

Класс обеспечивающий связь пиров между собой

"""
import json
import random

import grpc
from protos import network_pb2, network_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed
from tools.logger import Log
import threading
import time
class ConnectManager():
    def __init__(self, local_address='127.0.0.1', log=Log(), known_peers = set({"95.154.71.53:9334", "95.154.71.53:9333", "5.35.98.126:9333"})):
        """ """
        """ """
        self.log = log

        self.local_address = local_address

        self.sent_addresses = set()  # Уже отправленные адреса
        self.peer_status = {}  # Словарь статуса подключения пиров: address -> bool
        self.peer_channels = {}

        self.active_peers = {}
        self.known_peers = known_peers

        self.load_known_peers()


    def ping_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.check_active, peer): peer for peer in self.known_peers}
            self.active_peers = {futures[future] for future in as_completed(futures, timeout=5) if
                                 future.result(timeout=5)}
            return self.active_peers
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

    def connect_to_peers(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.connect_to_peer, address): address for address in
                       self.active_peers}

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

    def connect_to_peer(self, address):
        if address not in self.peer_channels:
            channel = grpc.insecure_channel(address)
            self.peer_channels[address] = network_pb2_grpc.NetworkServiceStub(channel)

        stub = self.peer_channels[address]
        try:
            if address not in self.sent_addresses or not self.peer_status.get(address, False):
                self.reset_cache_for_peer(address)  # Сброс кеша при повторном подключении
                peers = self.register_with_peers(stub, self.local_address)
                self.sent_addresses.add(address)
                self.peer_status[address] = True  # Устанавливаем статус подключения в True
                self.log.info(f"Registered on {address}, current peers: {peers}")

                new_peers = set(peers) - self.active_peers

                if new_peers:
                    self.active_peers.update(new_peers)
                    # self.resend_addresses(new_peers)

                return True

        except grpc.RpcError as e:
            self.peer_status[address] = False  # Устанавливаем статус подключения в False при ошибке
            if address in self.peer_channels:
                del self.peer_channels[address]
            # print(f"RPC error connecting to {address}: {e}")
            return False

    def register_with_peers(self, stub, local_address):
        r = network_pb2.PeerRequest(address=local_address)
        response = stub.RegisterPeer(r, timeout=5)
        return response.peers

    def reset_cache_for_peer(self, address):
        if address in self.sent_addresses:
            self.sent_addresses.remove(address)  # Удаляем адрес из кеша отправленных адресов

    def save_known_peers(self):
        with open('known_peers.json', 'w') as f:
            json.dump(list(self.known_peers), f)

    def load_known_peers(self):
        try:
            with open('known_peers.json', 'r') as f:
                peers = json.load(f)
                self.known_peers.update(peers)
        except FileNotFoundError:
            self.log.info("No known_peers.json file found, starting with initial peers.")

    def get_peer(self):
        """ Выбор пира, в идеале с самым быстрым пингом в будущем """
        return random.choice(self.active_peers)
    def start_ping_thread(self):
        ping_thread = threading.Thread(target=self.ping_peers_continuously)
        ping_thread.daemon = True
        ping_thread.start()

    def ping_peers_continuously(self, pause_check = 60):
        while True:
            self.ping_peers()
            self.connect_to_peers()
            time.sleep(pause_check)  # Пауза в 60 секунд между пингами