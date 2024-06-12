import grpc
from protos import network_pb2, network_pb2_grpc
from crypto.xmss import XMSS
from core.protocol import Protocol
from core.Transactions import Transaction, TransferTransaction
from crypto.file_crypto import FileEncryptor


class Wallet:
    def __init__(self, server='192.168.0.26:9334', filename = "keys.dat"):
        """ """
        self.filename = filename
        self.server = server = '95.154.71.53:9333'
        self.keys: {str: XMSS} = dict()



    def load_from_file(self, password):
        """ Сохранение файла кошелька """
        # Расшифровка данных из файла
        file_encryptor = FileEncryptor(password)
        decrypted_data = file_encryptor.decrypt_file(self.filename)

        for json_key in decrypted_data:
            key = XMSS.from_json(json_key)
            self.keys[key.address] = key


    def save_to_file(self, password):
        """ Загрузка кошелька из файла """

        file_encryptor = FileEncryptor(password)

        data = [k.to_json() for k in  self.keys.values()]

        # Шифрование данных в файл
        file_encryptor.encrypt_data_to_file(data, self.filename)


    def info(self, address):
        """ Информация по адресу кошелька из ноды """

        # Создание канала связи с сервером
        channel = grpc.insecure_channel(self.server)
        stub = network_pb2_grpc.NetworkServiceStub(channel)

        # Запрос на получение информации по адресу
        # address_request = network_pb2.AddressRequest(address="bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm")
        address_request = network_pb2.AddressRequest(address=address)

        try:
            # Отправка запроса и получение ответа
            response = stub.GetAddressInfo(address_request)
            return response

        except grpc.RpcError as e:
            print(f"Ошибка gRPC: {str(e)}")

    def info_text(self, address):
        response = self.info(address)
        print("Баланс адреса:", response.balance / 10000000)
        print("Nonce адреса:", response.nonce)
        print("Транзакции:")
        for transaction in response.transactions:
            print(transaction.json_data)

    def make_transaction(self, xmss, address_to, ammount, fee=0, message=""):
        """ создание транзакции """
        transaction = TransferTransaction(xmss.address, [address_to], [ammount], fee=fee,
                                 message_data=[message])

        transaction.nonce = self.info(xmss.address).nonce
        transaction.make_hash()
        transaction.make_sign(xmss)
        # json_transaction = tt.to_json()

        self.send_transaction(transaction)

    def send_transaction(self, transaction: Transaction):
        # Создание gRPC канала
        channel = grpc.insecure_channel(self.server)
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

    @staticmethod
    def create_wallet():
        """"""

    def add_key(self, height=5, hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE, key=None, seed_phrase=None):
        """  Добавление ключа в кошелек """
        xmss_keys = XMSS.create(height=height, hash_function_code=hash_function_code, key=key, seed_phrase=seed_phrase)
        self.keys[xmss_keys.address] = xmss_keys

    def keys_address(self):
        return [key.address for key in self.keys.values()]


if __name__ == '__main__':

    wallet = Wallet(filename ="keys.dat")

    password = input("пароль:")
    wallet.load_from_file(password)

    # print(wallet.keys_address())

    # wallet.add_key(seed_phrase=input("сид:"))
    wallet.add_key(key=input("ключ:"))

    #
    wallet.save_to_file(password)

    # info = wallet.info("YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA")
    wallet.info_text("YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA")
    wallet.info_text("bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm")



    # wallet.create_transaction()
