import grpc
from protos import network_pb2, network_pb2_grpc


def run_client(server_address, address):

    # Создание канала связи с сервером
    channel = grpc.insecure_channel(server_address)
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    # Запрос на получение информации по адресу
    # address_request = network_pb2.AddressRequest(address="bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm")
    address_request = network_pb2.AddressRequest(address=address)

    try:
        # Отправка запроса и получение ответа
        response = stub.GetAddressInfo(address_request)
        print("Баланс адреса:", response.balance/10000000)
        print("Nonce адреса:", response.nonce)
        print("Транзакции:")
        for transaction in response.transactions:
            print(transaction.json_data)
    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {str(e)}")

import requests

def get_address_info(server_address, address):
    url = f"http://{server_address}/address-info/{address}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Поднимет исключение для HTTP ошибок
        data = response.json()  # Получение данных ответа в формате JSON
        print("Полученные данные:")
        print(f"Баланс: {data['balance']}")
        print(f"Nonce: {data['nonce']}")
        print("Транзакции:")
        for transaction in data['transactions']:
            print(transaction['json_data'])  # Предполагается, что данные транзакций в JSON формате
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ошибка: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")

if __name__ == '__main__':
    server_address = '192.168.0.26:9333'  # Адрес сервера
    address = "YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA"  # Пример Bitcoin адреса
    get_address_info(server_address, address)


    # run_client(server_address, address)
