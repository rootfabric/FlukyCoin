import json
import hashlib
from core.protocol import Protocol


class Transaction:

    def __init__(self, tx_type, fromAddress, toAddress, amount, fee=0):
        self.tx_type = tx_type
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.amount = amount
        self.nonce = None
        self.fee = fee
        self.message_data = None
        self.thash = None
        self.sign = None

    # @property
    # def txhash(self) -> bytes:
    #     return self.get_data_hash()

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        data = {
            'tx_type': self.tx_type,
            'nonce': self.nonce,
            'thash': self.thash,
            'fromAddress': self.fromAddress,
            'toAddress': self.toAddress,
            'amount': self.amount,
            'fee': self.fee
        }
        if self.message_data is not None:
            data['message_data'] = self.message_data[:Protocol.MAX_MESSAGE_SIZE]  # Конвертируем Uint8Array в список для сериализации
        return data

    def to_json(self):
        # Сериализует объект в строку JSON
        d = self.as_dict()
        return json.dumps(d)

    @classmethod
    def from_json(cls, json_str):
        # Создает и возвращает экземпляр класса из строки JSON
        data = json.loads(json_str)
        return cls(**data)

    def get_data_hash(self) -> bytes:
        """
        This method returns the hashes of the transaction data.
        """
        return hashlib.sha256(self.to_json().encode())

    def make_hash(self):
        """ Идентификатор транзакции """
        self.thash = self.get_data_hash().hexdigest()
        # print(self.thash)

    def sign_from_str(self, sign_str):
        """  требуется серилизация """
        self.sign = sign_str


class TransferTransaction(Transaction):
    def __init__(self, fromAddress, toAddress, amount, fee=0, message_data=None):
        super().__init__('transfer', fromAddress, toAddress, amount, fee)
        if message_data:
            self.message_data = message_data  # Преобразование message_data в Uint8Array

class SlaveTransaction(Transaction):
    def __init__(self, fromAddress, slaveAddress, slaveTypes, fee=0):
        super().__init__('slave', fromAddress, slaveAddress, 0, fee)
        self.slaveAddress = slaveAddress
        self.slaveTypes = slaveTypes

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        data = super().as_dict()
        data.update({
            'slaveAddress': self.slaveAddress,
            'slaveTypes': self.slaveTypes
        })
        return data


class CoinbaseTransaction(Transaction):
    def __init__(self, toAddress, amount):
        super().__init__('coinbase', Protocol.coinbase_address.hex(), toAddress, amount, 0)


if __name__ == '__main__':
    t = CoinbaseTransaction("2", 100)
    t.nonce = 1
    t.make_hash()
    print(t.to_json())

    tt = TransferTransaction("1", ["2"], [100], message_data=["test message"])
    tt.nonce = 1
    tt.make_hash()
    print(tt.to_json())

    tt = TransferTransaction("1", ["2", "3", "4"], [100, 100, 100])
    tt.nonce = 1
    tt.make_hash()
    print(tt.to_json())

    st = SlaveTransaction("1", "slaveAddress123", ["TRANSFER", "MINING"], 0.01)
    st.nonce = 1
    st.make_hash()
    print(st.to_json())
