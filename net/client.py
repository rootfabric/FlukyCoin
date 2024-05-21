# import datetime
# import time
#
# import zmq
# import json
#
#
# class Client:
#     def __init__(self, host="localhost", port=5555, timeout=1000):
#         self.context = zmq.Context()
#         self.socket = self.context.socket(zmq.DEALER)
#         self.socket.connect(f"tcp://{host}:{port}")
#         # Установка таймаута для операций с сокетом
#         self.socket.setsockopt(zmq.RCVTIMEO, timeout)
#         self.socket.setsockopt(zmq.SNDTIMEO, timeout)
#         self.socket.setsockopt(zmq.LINGER, 0)  # Устанавливаем LINGER на 0
#         # print(f"Connected to node at {host}:{port}")
#         self.host = host
#         self.port = port
#         self.is_connected = False
#         self.server_address = ""
#         self.last_broadcast_block = None
#         self.info = {}
#
#         self.last_time_info = 0
#     def address(self):
#         return f"{self.host}:{self.port}"
#
#     def get_info(self):
#         """Опрос клиента, но не спам """
#         if time.time() - self.last_time_info>1:
#             self.info = self.send_request({'command': 'getinfo'})
#             # print(datetime.datetime.now(), self.info)
#             self.last_time_info = time.time()
#         return self.info
#
#
#     def send_request(self, request):
#         try:
#             self.socket.send(json.dumps(request).encode('utf-8'))
#             response = self.socket.recv()
#             self.is_connected = True
#             return json.loads(response.decode('utf-8'))
#         except zmq.error.Again:
#             # print(f"Timeout occurred when connecting to {self.host}:{self.port}")
#             self.is_connected = False
#             return {'error': 'Timeout occurred'}
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             self.is_connected = False
#             return {'error': str(e)}
#
#     def close(self):
#         """ """
#         # if self.is_connected:
#         #     self.context.term()
#         #     self.socket.close()
#         # print("Client has been disconnected")
#
#

import socket
import json
import time
import datetime

class Client:
    def __init__(self, host="localhost", port=5555, timeout=5.0):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(timeout)
        try:
            self.client_socket.connect((host, port))
            self.is_connected = True
        except socket.error as e:
            # print(f"Cannot connect to server at {host}:{port}, error: {e}")
            self.is_connected = False

        self.last_time_info = 0
        self.last_broadcast_block = None
        self.info = {}

    def address(self):
        return f"{self.host}:{self.port}"

    def get_info(self):
        """Опрос сервера с учетом частоты запросов."""
        if time.time() - self.last_time_info > 1:
            self.info = self.send_request({'command': 'getinfo'})
            # print("get_info", datetime.datetime.now(), self.info)
            self.last_time_info = time.time()
        return self.info

    def send_request(self, request):
        try:
            self.client_socket.sendall(json.dumps(request).encode('utf-8'))
            response = self.client_socket.recv(1024)
            if response:
                return json.loads(response.decode('utf-8'))
            else:
                # print("No response from server")
                return {'error': 'No response from server'}
        except socket.timeout:
            # print(f"Timeout occurred when connecting to {self.host}:{self.port}")
            return {'error': 'Timeout occurred'}
        except Exception as e:
            # print(f"An error occurred: {e}")
            return {'error': str(e)}

    def close(self):
        if self.is_connected:
            self.client_socket.close()
            print("Client has been disconnected")

if __name__ == '__main__':
    client = Client('localhost', 5555)
    info = client.get_info()
    print("Server info:", info)
    client.close()
