from tools.logger import Log
import socket
import json
import struct
import time
class Client:
    def __init__(self, host="localhost", port=5555, timeout=10.0, log=Log()):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(timeout)
        self.log = log

        self.last_time_info = 0
        self.last_broadcast_block = None
        self.info = {}

        self.sequence_id = 0  # Инициализация идентификатора последовательности

        self._connect()

    def _connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            self.is_connected = True
        except socket.error as e:
            self.is_connected = False

    def address(self):
        return f"{self.host}:{self.port}"

    def node_candidate(self):
        """ Блок кандидат в заголовке ноды """
        if self.info is None:
            return "None"
        return str(self.info.get('block_candidate'))


    def get_info(self, ignore_timer=False):
        """Опрос сервера с учетом частоты запросов."""
        if time.time() - self.last_time_info > 1 or ignore_timer:
            # self.log.info("get_info", self.address())
            self.info = self.send_request({'command': 'getinfo'})
            # print("get_info", datetime.datetime.now(), self.info)
            self.last_time_info = time.time()

        return self.info

    def send_request(self, request):
        response = b''


        request['sequence_id'] = self.sequence_id  # Добавление идентификатора последовательности к запросу
        self.sequence_id += 1  # Инкремент идентификатора
        # Остальной код метода остаётся без изменений

        try:
            # Encode the request into JSON and then bytes
            request_data = json.dumps(request).encode('utf-8')
            # Pack the length of the request_data before sending
            self.client_socket.sendall(struct.pack('>I', len(request_data)) + request_data)
            # Wait for response
            response = self.recvall()
            if response is None:
                return None
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            self.log.error(f"{self.host}:{self.port}, response: {response}")
            self.log.error("Error sending request: {}".format(e))

            self._connect()

            return {'error': str(e)}

    def recvall(self):
        try:
            raw_msglen = self.client_socket.recv(4)
            if not raw_msglen:
                self.log.error("Failed to receive message length")
                return None
            msglen = struct.unpack('>I', raw_msglen)[0]

            # Полное получение сообщения
            data = bytearray()
            while len(data) < msglen:
                packet = self.client_socket.recv(msglen - len(data))
                if not packet:
                    self.log.error("Connection closed prematurely when expecting {} bytes".format(msglen - len(data)))
                    return None
                data.extend(packet)
            return data
        except Exception as e:
            self.log.error("Failed during recvall: {}".format(str(e)))

            self._connect()

            return None

    def close(self):
        self.client_socket.close()
        self.log.info("Client has been disconnected")
