import json
import hashlib
from core.protocol import Protocol
from crypto.xmss import XMSS

class Transaction:

    def __init__(self, tx_type, fromAddress, toAddress, amount, fee=0):
        self.tx_type = tx_type
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.amount = amount
        self.nonce = None
        self.fee = fee
        self.message_data = None
        self.txhash = None
        self.public_key = None
        self.signature = None

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        data = {
            'tx_type': self.tx_type,
            'nonce': self.nonce,
            'txhash': self.txhash,
            'fromAddress': self.fromAddress,
            'toAddress': self.toAddress,
            'amount': self.amount,
            'fee': self.fee,
            'public_key': self.public_key,
            'signature': self.signature
        }
        if self.message_data is not None:
            data['message_data'] = self.message_data[:Protocol.MAX_MESSAGE_SIZE]
        return data

    def to_json(self):
        # Сериализует объект в строку JSON
        d = self.as_dict()
        return json.dumps(d)

    @classmethod
    def from_json(cls, json_data):
        # Создает и возвращает экземпляр класса из строки JSON или словаря
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        tx_type = data.get('tx_type')
        if tx_type == 'transfer':
            return TransferTransaction.from_dict(data)
        elif tx_type == 'slave':
            return SlaveTransaction.from_dict(data)
        elif tx_type == 'coinbase':
            return CoinbaseTransaction.from_dict(data)
        else:
            raise ValueError(f"Unknown transaction type: {tx_type}")

    def get_data_hash(self) -> bytes:
        """
        This method returns the hashes of the transaction data.
        """
        return hashlib.sha256(self.to_json().encode())

    def make_hash(self):
        """ Идентификатор транзакции """
        self.txhash = self.get_data_hash().hexdigest()

    def make_sign(self, xmss: XMSS) -> bytes:
            """ Подпись блока """
            signature = xmss.sign(bytes.fromhex(self.txhash))

            self.signature = signature.to_base64()
            self.public_key = xmss.keyPair.PK.to_hex()
            print(f"Подпись размер: {len(self.signature)} ")

class TransferTransaction(Transaction):
    def __init__(self, fromAddress, toAddress, amount, fee=0, message_data=None):
        super().__init__('transfer', fromAddress, toAddress, amount, fee)
        if message_data:
            self.message_data = message_data[:Protocol.MAX_MESSAGE_SIZE]  # Преобразование message_data в Uint8Array

    @classmethod
    def from_dict(cls, data):
        fromAddress = data['fromAddress']
        toAddress = data['toAddress']
        amount = data['amount']
        fee = data['fee']
        message_data = data.get('message_data')
        tx = cls(fromAddress, toAddress, amount, fee, message_data)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        return tx


class SlaveTransaction(Transaction):
    def __init__(self, fromAddress, slaveAddress, slaveTypes, fee=0):
        super().__init__('slave', fromAddress, slaveAddress, 0, fee)
        self.slaveAddress = slaveAddress
        self.slaveTypes = slaveTypes

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        data = super().as_dict()
        del data['toAddress']
        del data['amount']
        data.update({
            'slaveAddress': self.slaveAddress,
            'slaveTypes': self.slaveTypes
        })
        return data

    @classmethod
    def from_dict(cls, data):
        fromAddress = data['fromAddress']
        slaveAddress = data['slaveAddress']
        slaveTypes = data['slaveTypes']
        fee = data['fee']
        tx = cls(fromAddress, slaveAddress, slaveTypes, fee)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        return tx


class CoinbaseTransaction(Transaction):
    def __init__(self, toAddress, amount):
        super().__init__('coinbase', Protocol.coinbase_address.hex(), toAddress, amount, 0)
        self.make_hash()

    @classmethod
    def from_dict(cls, data):
        toAddress = data['toAddress']
        amount = data['amount']
        tx = cls(toAddress, amount)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        return tx


if __name__ == '__main__':
    t = CoinbaseTransaction("2", 100)
    t.nonce = 1
    t.make_hash()
    print(t.to_json())


    xmss = XMSS.create()
    print(xmss.address)

    tt = TransferTransaction("1", ["2"], [100], message_data=["test message"])
    tt.nonce = 1
    tt.make_hash()
    tt.make_sign(xmss)
    print(tt.to_json())

    tt = TransferTransaction("1", ["2", "3", "4"], [100, 100, 100])
    tt.nonce = 1
    tt.make_hash()
    tt.make_sign(xmss)
    print(tt.to_json())

    st = SlaveTransaction("1", ["slaveAddress123"], ["TRANSFER", "MINING"], 0.01)
    st.nonce = 1
    st.make_hash()
    st.make_sign(xmss)
    print(st.to_json())
