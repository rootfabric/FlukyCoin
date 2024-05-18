# import threading
# import zmq
# import json
#
# class Server:
#     def __init__(self, handle_request, port=5555, host='localhost'):
#         self.context = zmq.Context()
#         self.socket = self.context.socket(zmq.ROUTER)
#         self.socket.bind(f"tcp://{host}:{port}")
#         self.handle_request = handle_request
#         self.address = f"{host}:{port}"
#         self.is_work = True
#         print(f"Server is listening on {self.address} ")
#
#         self.clients = {}
#
#         # Создание потока для асинхронного прослушивания
#         self.server_thread = threading.Thread(target=self.listen)
#         self.server_thread.daemon = True  # Установка потока как демона для автоматического завершения при закрытии основного потока
#         self.server_thread.start()
#
#     def listen(self):
#         while self.is_work:
#             try:
#                 client_id, message = self.socket.recv_multipart()
#                 request = json.loads(message.decode('utf-8'))
#                 response = self.handle_request(request, client_id)
#                 self.socket.send_multipart([client_id, json.dumps(response).encode('utf-8')])
#             except Exception as e:
#                 print("Error Server listen", e)
#     def close(self):
#         self.is_work = False
#         self.socket.close()
#         self.context.term()
#         self.server_thread.join()  # Дожидаемся завершения серверного потока
#         print("Server has been stopped")
#
#

import socket
import threading
import json

class Server:
    def __init__(self, handle_request, port=5555, host='localhost'):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.handle_request = handle_request
        self.address = f"{host}:{port}"
        self.is_work = True
        print(f"Server is listening on {self.address}")

        # Создание потока для асинхронного прослушивания
        self.server_thread = threading.Thread(target=self.listen)
        self.server_thread.daemon = True
        self.server_thread.start()

    def listen(self):
        while self.is_work:
            try:
                client_socket, addr = self.server_socket.accept()
                # print(f"Connected by {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except Exception as e:
                print("Error Server listen", e)

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                request = json.loads(data.decode('utf-8'))
                response = self.handle_request(request)
                client_socket.sendall(json.dumps(response).encode('utf-8'))
        finally:
            client_socket.close()

    def close(self):
        self.is_work = False
        self.server_socket.close()
        # self.server_thread.join()  # Дожидаемся завершения серверного потока
        print("Server has been stopped")


if __name__ == '__main__':
    # server = Server(handle_request, 5555, 'localhost')
    """"""
