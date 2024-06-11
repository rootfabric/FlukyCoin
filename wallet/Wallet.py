import grpc
from protos import network_pb2, network_pb2_grpc
from crypto.xmss import XMSS
from core.protocol import Protocol
from core.Transactions import Transaction, TransferTransaction
from crypto.file_crypto import FileEncryptor


class Wallet:
    def __init__(self, server='192.168.0.26:8080', filename = "keys.dat"):
        """ """
        self.filename = filename
        self.server = server
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

    def create_transaction(self, xmss, address_to, ammount, fee=0, message=""):
        """ создание транзакции """
        tt = TransferTransaction(xmss.address, [address_to], [ammount], fee=fee,
                                 message_data=[message])

        tt.nonce = self.info(xmss.address).nonce
        tt.make_hash()
        tt.make_sign(xmss)
        # json_transaction = tt.to_json()

        self.send_transaction(tt)

    def send_transaction(self):
        """ Отсылка транзакции в сеть """

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

    wallet = Wallet(filename = "keys.dat")

    wallet.load_from_file(input("пароль:"))

    print(wallet.keys_address())

    # wallet.add_key(seed_phrase=input("сид:"))

    #
    # wallet.save_to_file(input("пароль:"))

    # info = wallet.info("YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA")
    # print(info)

    # wallet.create_transaction()
