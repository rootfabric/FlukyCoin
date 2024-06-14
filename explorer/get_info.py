import grpc
from protos import network_pb2, network_pb2_grpc


def get_info(server="192.168.0.26:9334"):
    """ Информация с ноды """
    # Создание канала связи с сервером
    channel = grpc.insecure_channel(server)
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    # Запрос на получение информации о сети
    net_info_request = network_pb2.Empty()

    try:
        # Отправка запроса и получение ответа
        response = stub.GetNetInfo(net_info_request)

        # Обработка и вывод информации
        print(f"Synced: {response.synced}")
        print(f"Blocks: {response.blocks}")
        print(f"Last Block Time: {response.last_block_time}")
        print(f"Last Block Hash: {response.last_block_hash}")
        print(f"Difficulty: {response.difficulty}")

        for peer in response.peers_info:
            print(f"Peer Network Info: {peer.network_info}")
            print(f"Peer Synced: {peer.synced}")
            print(f"Peer Blocks: {peer.blocks}")
            print(f"Peer Latest Block: {peer.latest_block}")
            print(f"Peer Uptime: {peer.uptime}")
            print(f"Peer Difficulty: {peer.difficulty}")

        return response

    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {str(e)}")


if __name__ == '__main__':
    info = get_info()
    print(info)
