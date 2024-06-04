# from core.Transactions import Transaction
# from net.client import Client
# from core.protocol import Protocol
#
# import random
# if __name__ == '__main__':
#     """ """
#
#     t = Transaction("coinbase", random.randint(0,100000), "2", "100")
#     t.make_hash()
#     # print(t.get_data_hash().hexdigest())
#     print(t.txhash)
#
#     # client = Client(host = "127.0.0.1", port = 9334)
#     client = Client(host = "192.168.0.26", port = 9334)
#
#     response = client.send_request(
#         {'command': 'version', 'ver': Protocol.VERSION, 'address': "127.0.0.1:888"})
#     print(response)
#
#     response = client.send_request(
#         {'command': 'tx', 'tx_data': {'tx_json':t.to_json(), 'tx_sign':t.signature}})
#     print(response)

import time

import json
import hashlib
from core.protocol import Protocol
from crypto.xmss import XMSS, XMSSPublicKey, SigXMSS, XMSS_verify
from tools.logger import Log


import grpc
from protos import network_pb2, network_pb2_grpc

from core.Transactions import Transaction, TransferTransaction

def add_transaction(server_address, transaction:Transaction):
    # Создание gRPC канала
    channel = grpc.insecure_channel(server_address)
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    json_data = transaction.to_json()
    # Создание объекта транзакции
    transaction = network_pb2.Transaction(json_data=json_data)

    # Отправка транзакции на сервер
    try:
        response = stub.AddTransaction(transaction)
        if response.success:
            print("Transaction successfully added.")
        else:
            print("Failed to add transaction.")
    except grpc.RpcError as e:
        print(f"Failed to connect to server: {str(e)}")

if __name__ == "__main__":
    # Пример использования
    server_address = '192.168.0.26:9334'  # Адрес сервера

    xmss = XMSS.create()
    print(xmss.address)

    tt = TransferTransaction(xmss.address, ["2"], [100], message_data=["test message"])
    tt.nonce = 1
    tt.make_hash()
    tt.make_sign(xmss)
    json_transaction = tt.to_json()

    add_transaction(server_address, tt)
