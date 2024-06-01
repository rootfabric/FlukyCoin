from tools.logger import Log
import socket
import threading
import json
import struct


class Server:
    def __init__(self, handle_request, port=5555, host='localhost', log=Log()):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.handle_request = handle_request
        self.address = f"{host}:{port}"
        self.is_work = True
        self.log = log
        self.is_work = True
        self.log.info("Server is listening on {}:{}".format(host, port))

        self.server_thread = threading.Thread(target=self.listen)
        self.server_thread.daemon = True
        self.server_thread.start()

    def listen(self):
        while self.is_work:
            try:
                client_socket, addr = self.server_socket.accept()
                self.log.info("Connected by {}".format(addr))
                threading.Thread(target=self.handle_client, args=(client_socket,addr, )).start()
            except Exception as e:
                self.log.error("Server listen error: {}".format(e))

    def handle_client(self, client_socket, addr):
        try:
            sequence_buffer = {}  # Буфер для хранения запросов с идентификаторами
            last_sequence_id = -1  # Последний обработанный идентификатор последовательности

            while True:
                raw_msglen = self.recvall_exactly(client_socket, 4)
                if not raw_msglen:
                    return
                msglen = struct.unpack('>I', raw_msglen)[0]
                data = self.recvall_exactly(client_socket, msglen)
                if not data:
                    return
                request = json.loads(data.decode('utf-8'))

                sequence_id = request.get('sequence_id')
                if sequence_id is not None:
                    if sequence_id == last_sequence_id + 1:
                        response = self.handle_request(request)
                        self.send_response(client_socket, response)
                        last_sequence_id = sequence_id
                        # Проверка и обработка запросов в буфере
                        while sequence_buffer.get(last_sequence_id + 1) is not None:
                            last_sequence_id += 1
                            response = self.handle_request(sequence_buffer.pop(last_sequence_id))
                            self.send_response(client_socket, response)
                    else:
                        # Сохранение запроса в буфер, если он пришёл не по порядку
                        sequence_buffer[sequence_id] = request
        except Exception as e:
            self.log.error("Client handling error: {}".format(e))
        finally:
            client_socket.close()

    def recvall_exactly(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def send_response(self, client_socket, response):
        response_data = json.dumps(response).encode('utf-8')
        response_length = struct.pack('>I', len(response_data))
        client_socket.sendall(response_length + response_data)

    def close(self):
        self.is_work = False
        self.server_socket.close()
        self.server_thread.join()


if __name__ == '__main__':
    server = Server(handle_request)
