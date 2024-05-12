import datetime
import time

import zmq
import json


class Client:
    def __init__(self, host="localhost", port=5555, timeout=1000):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(f"tcp://{host}:{port}")
        # Установка таймаута для операций с сокетом
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, timeout)
        self.socket.setsockopt(zmq.LINGER, 0)  # Устанавливаем LINGER на 0
        # print(f"Connected to node at {host}:{port}")
        self.host = host
        self.port = port
        self.is_connected = False
        self.server_address = ""
        self.last_broadcast_block = None
        self.info = {}

        self.last_time_info = 0
    def address(self):
        return f"{self.host}:{self.port}"

    def get_info(self):
        """Опрос клиента, но не спам """
        if time.time() - self.last_time_info>1:
            self.info = self.send_request({'command': 'getinfo'})
            # print(datetime.datetime.now(), self.info)
            self.last_time_info = time.time()
        return self.info


    def send_request(self, request):
        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv()
            self.is_connected = True
            return json.loads(response.decode('utf-8'))
        except zmq.error.Again:
            # print(f"Timeout occurred when connecting to {self.host}:{self.port}")
            self.is_connected = False
            return {'error': 'Timeout occurred'}
        except Exception as e:
            print(f"An error occurred: {e}")
            self.is_connected = False
            return {'error': str(e)}

    def close(self):
        """ """
        # if self.is_connected:
        #     self.context.term()
        #     self.socket.close()
        # print("Client has been disconnected")


