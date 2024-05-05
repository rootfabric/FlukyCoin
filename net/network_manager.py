from net.server import Server
from net.client import Client
from core.protocol import Protocol
import os
import pickle
import threading
import json
import time

"""

Связь с нодами, организация gossip protocol

"""


class NetworkManager:
    def __init__(self, running, handle_request, host, port, initial_peers, dir=''):

        # валидные сообщения с сервера приходят в ноду:
        self.handle_request_node = handle_request

        self.known_peers = initial_peers

        self.server = Server(self.handle_request, host=host, port=port)

        self.dir = self.server.address
        # self.lock = threading.Lock()

        self.load_from_disk()

        self.running = True

        self.peers = {}

        # добавляем самого себя
        self.add_known_peer(self.server.address, ping=False)

        self.list_need_broadcast_peers = []

    def run(self):
        # Запуск фонового потока для периодической проверки узлов
        self.background_thread = threading.Thread(target=self.check_peers)
        self.background_thread.start()

    def add_known_peer(self, new_address, ping=True):

        # print(f"New peer to known_peers")
        if new_address not in self.known_peers:
            self.known_peers.append(new_address)
        if ping:
            self.ping_peer(new_address)
            # self.broadcast_new_peer(new_address)

    def handle_request_node(self):
        """"""
        raise "Метод должен быть назначен в ноде"

    def handle_request(self, request, client_id):
        command = request.get('command')
        print("Server command", command)

        if command == 'version':
            new_address = request.get('address')
            self.server.clients[client_id] = new_address
            self.add_known_peer(new_address, False)

            # новый адрес, отправить всем активным пирам
            self.list_need_broadcast_peers.append(new_address)

            print("New server connect", new_address)
            return {'connected': True}

        return self.handle_request_node(request)

    def save_to_disk(self, filename='peers.json'):

        # print("no save peers")
        # return
        dir = self.dir.replace(":", "_")  # Замена недопустимых символов в имени директории
        full_path = os.path.join(dir, filename)

        if not os.path.exists(dir):
            os.makedirs(dir)  # Создание директории, если необходимо

        with open(full_path, 'w') as file:
            json.dump(self.known_peers, file, indent=4)

    def load_from_disk(self, filename='peers.json'):
        dir = self.dir.replace(":", "_")
        full_path = os.path.join(dir, filename)

        if os.path.exists(full_path):
            with open(full_path, 'r') as file:
                try:
                    self.known_peers = json.load(file)
                except:
                    self.known_peers = []
        else:
            print(f"No data file found at {full_path}. Starting with an empty list of peers.")

    def ping_all_peers(self):
        for peer in list(self.known_peers):
            self.ping_peer(peer)

    def active_peers(self):
        return [peer for peer in self.peers]

    def _ping_all_peers_and_save(self):
        self.ping_all_peers()
        self.save_to_disk()
        print(self.active_peers())

    def check_peers(self):
        """ Проверка доступных нод, выбор ближайших соседей """

        t = time.time() - 11
        while self.running:
            # with self.lock:
            if len(self.list_need_broadcast_peers) > 0:
                for peer in self.list_need_broadcast_peers:
                    self.broadcast_new_peer(peer)

            if time.time() - t > 10:
                self._ping_all_peers_and_save()

                t = time.time()

            time.sleep(0.1)  # Пауза перед следующей проверкой

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
            print(f"Ошибка клиента {address}")
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

                return True

            print(f"Error send: {response}")
            del self.peers[address]
            return False

        else:
            print(f"Failed to connect to {address}")
            del self.peers[address]
            return False

        return True
        #
        # except Exception as e:
        #     print(f"Failed to connect to {address}: {str(e)}")
        #     del self.peers[address]

    def stop(self):
        self.running = False
        self.background_thread.join()  # Дожидаемся завершения фонового потока

    def send_message(self, message):
        """ Рассылка сообщениц в ноды """

        # тут должна быть добавлена логика отсылки не всем подряд, а только части.

        # потом разбить на мультипоток
        for peer in self.get_active_peers():
            self._send_message_to_peer(peer, message)

    def _send_message_to_peer(self, peer, message):
        """ отправка сообщения конкретной ноде """

    def broadcast_new_peer(self, peer_to_broadcast):
        """ передать всем клиентам информацию о новом пире """

        # сами себе не бродкастим
        if self.server.address == peer_to_broadcast:
            return False

        print(f"Broadcast to {peer_to_broadcast}")
        for client in self.peers.values():
            # if peer != new_peer and self.server.address != peer:  # Avoid notifying the new peer about itself
            if client.is_connected:
                answer = client.send_request({'command': 'newpeer', 'peer': peer_to_broadcast})
                if answer.get('status') == 'success':
                    if peer_to_broadcast in self.list_need_broadcast_peers:
                        self.list_need_broadcast_peers.remove(peer_to_broadcast)
