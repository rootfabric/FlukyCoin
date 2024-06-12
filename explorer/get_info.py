import grpc
from protos import network_pb2, network_pb2_grpc
from crypto.xmss import XMSS
from core.protocol import Protocol
from core.Transactions import Transaction, TransferTransaction
from crypto.file_crypto import FileEncryptor


def get_info(server="192.168.0.26:9334"):
    """ Информация с ноды """
    """ Информация с ноды """
    # Создание канала связи с сервером
    channel = grpc.insecure_channel(server)
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    # Запрос на получение информации о сети
    net_info_request = network_pb2.Empty()

    try:
        # Отправка запроса и получение ответа
        response = stub.GetNetInfo(net_info_request)
        return response

    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {str(e)}")


if __name__ == '__main__':
    info = get_info()
    print(info)