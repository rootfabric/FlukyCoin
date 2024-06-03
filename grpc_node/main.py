from GrpcServer import GrpcServer
from ClientHandler import ClientHandler
import time

def main():
    local_address = 'localhost:50051'
    version = "1.0"
    initial_peers = ['localhost:50051'] + [local_address]

    server = GrpcServer(local_address, version)
    client_handler = ClientHandler(server.servicer)

    server.start()
    try:
        if initial_peers:
            client_handler.connect_to_peers(set(initial_peers))

        while True:
            time.sleep(1)
            new_peers = list(server.servicer.peers)
            client_handler.connect_to_peers(new_peers)
    except KeyboardInterrupt:
        server.stop()

if __name__ == '__main__':
    main()
