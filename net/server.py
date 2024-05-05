import threading
import zmq
import json

class Server:
    def __init__(self, handle_request, port=5555, host='localhost'):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(f"tcp://{host}:{port}")
        self.handle_request = handle_request
        self.address = f"{host}:{port}"
        self.is_work = True
        print(f"Server is listening on {self.address} ")

        self.clients = {}

        # Создание потока для асинхронного прослушивания
        self.server_thread = threading.Thread(target=self.listen)
        self.server_thread.daemon = True  # Установка потока как демона для автоматического завершения при закрытии основного потока
        self.server_thread.start()

    def listen(self):
        while self.is_work:
            client_id, message = self.socket.recv_multipart()
            request = json.loads(message.decode('utf-8'))
            response = self.handle_request(request, client_id)
            self.socket.send_multipart([client_id, json.dumps(response).encode('utf-8')])

    def close(self):
        self.is_work = False
        self.socket.close()
        self.context.term()
        self.server_thread.join()  # Дожидаемся завершения серверного потока
        print("Server has been stopped")


