from net.server import Server
from net.client import Client
import os
import pickle
import threading
import json
import time

"""

Связь с нодами, организация gossip protocol

"""


class PeerManager:
    def __init__(self, initial_peers, dir=''):
        self.known_peers = {peer: {'active': False} for peer in initial_peers}

        self.dir = dir
        # self.lock = threading.Lock()

        self.load_from_disk()

        self.is_work = True
        self.ping_all_peers()

    def run(self):
        # Запуск фонового потока для периодической проверки узлов
        self.background_thread = threading.Thread(target=self.check_peers)
        self.background_thread.start()

    def save_to_disk(self, filename='peers.json'):
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
                self.known_peers = json.load(file)
        else:
            print(f"No data file found at {full_path}. Starting with an empty list of peers.")

    def get_active_peers(self):
        # Возвращает список активных узлов
        # with self.lock:
        active_peers = [peer for peer, details in self.known_peers.items() if details['active']]
        return active_peers

    def ping_all_peers(self):
        for peer in list(self.known_peers):
            self.ping_peer(peer)

    def check_peers(self):
        """ Проверка доступных нод, выбор ближайших соседей """

        t = time.time()
        while self.is_work:
            # with self.lock:
            if time.time() - t > 30:
                self.ping_all_peers()
                self.save_to_disk()
                t = time.time()

            time.sleep(0.1)  # Пауза перед следующей проверкой

    def ping_peer(self, peer):
        client = Client(peer.split(":")[0], int(peer.split(":")[1]))
        try:
            response = client.send_request({'command': 'getinfo'})
            if response:

                if peer not in self.known_peers:
                    self.known_peers[peer] = {'active': False}
                self.known_peers[peer]['active'] = True if "error" not in response else False
                # Обновляем список известных узлов с новыми узлами, полученными от текущего узла
                new_peers = response.get('peers', [])
                for new_peer in new_peers:
                    if new_peer not in self.known_peers:
                        self.known_peers[new_peer] = {'active': False}
        except Exception as e:
            # print(f"Failed to connect to {peer}: {str(e)}")
            self.known_peers[peer]['active'] = False
        # finally:
        #     client.close()

    def stop(self):
        self.is_work = False
        self.background_thread.join()  # Дожидаемся завершения фонового потока

    def send_message(self, message):
        """ Рассылка сообщениц в ноды """

        # тут должна быть добавлена логика отсылки не всем подряд, а только части.

        # потом разбить на мультипоток
        for peer in self.get_active_peers():
            self._send_message_to_peer(peer, message)

    def _send_message_to_peer(self, peer, message):
        """ отправка сообщения конкретной ноде """
