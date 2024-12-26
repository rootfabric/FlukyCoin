import json
import hashlib
from core.protocol import Protocol
from crypto.xmss import XMSS, XMSSPublicKey, SigXMSS, XMSS_verify
from tools.logger import Log


class Transaction:

    def __init__(self, tx_type, fromAddress, toAddress, amounts, fee=0, nonce=None):
        self.tx_type = tx_type
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.amounts = amounts
        self.nonce = nonce
        self.fee = fee
        self.message_data = None
        self.txhash = None
        self.public_key = None
        self.signature = None
        self.log = Log()
        self.PK = None

    def as_dict(self):
        # Возвращает представление объекта в виде словаря
        data = {
            'tx_type': self.tx_type,
            'nonce': self.nonce,
            'txhash': self.txhash,
            'fromAddress': self.fromAddress,
            'toAddress': self.toAddress,
            'amounts': self.amounts,
            'fee': self.fee,
            'public_key': self.public_key,
            'signature': self.signature
        }
        if self.message_data is not None:
            data['message_data'] = self.message_data[:Protocol.MAX_MESSAGE_SIZE]
        return data

    def to_dict(self, for_sign=False):

        d = self.as_dict()
        if for_sign:
            # данные для подписи. Убираем поля которых не должно быть
            d['public_key'] = None
            d['signature'] = None
            d['txhash'] = None
        return d

    def to_json(self, for_sign=False):
        # Сериализует объект в строку JSON
        return json.dumps(self.to_dict(for_sign))

    @classmethod
    def from_json(cls, json_data):
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
        elif tx_type == 'node_registration':
            return NodeRegistrationTransaction.from_dict(data)
        elif tx_type == 'reputation_token':
            return ReputationTokenTransaction.from_dict(data)
        else:
            raise ValueError(f"Unknown transaction type: {tx_type}")

    def get_data_hash(self) -> bytes:
        """
        This method returns the hashes of the transaction data.
        """
        return hashlib.sha256(self.to_json(for_sign=True).encode())

    def make_hash(self):
        """ Идентификатор транзакции """
        self.txhash = self.get_data_hash().hexdigest()

    def make_sign(self, xmss: XMSS) -> bytes:
        """ Подпись блока """
        signature = xmss.sign(bytes.fromhex(self.txhash))

        self.signature = signature.to_base64()
        self.public_key = xmss.keyPair.PK.to_hex()
        # print(f"Подпись размер: {len(self.signature)} ")

    def all_amounts(self):
        """ вся сумма транзакции """
        return sum(self.amounts)

    def make_XMSSPublicKey(self):
        """Воссоздание публичного ключа по строке """
        self.PK = XMSSPublicKey.from_hex(self.public_key)
        return self.PK

    def validate_sign(self):
        """ проверка подписи транзакции """

        old_hash = self.txhash

        self.make_hash()
        if old_hash != self.txhash:
            self.log.error("Ошибка валидации транзакции. не совпадает хеш")
            return False

        # self.PK = XMSSPublicKey.from_hex(self.public_key)
        self.PK = self.make_XMSSPublicKey()

        if self.fromAddress != self.PK.generate_address():
            self.log.error("Ошибка валидации транзакции. не совпадает отправитель")
            return False

        signature = SigXMSS.from_base64(self.signature)

        # Верификация подписи
        verf = XMSS_verify(signature, bytes.fromhex(self.txhash), self.PK)
        if not verf:
            self.log.error("Ошибка валидации транзакции. не совпадает подпись")
            return False

        """ 
        Валидация по цепи
        """

        return True


class TransferTransaction(Transaction):
    def __init__(self, fromAddress, toAddress, amounts, fee=0, message_data=None):
        super().__init__('transfer', fromAddress, toAddress, amounts, fee)
        if message_data:
            self.message_data = message_data[:Protocol.MAX_MESSAGE_SIZE]  # Преобразование message_data в Uint8Array

    @classmethod
    def from_dict(cls, data):
        fromAddress = data['fromAddress']
        toAddress = data['toAddress']
        amounts = data['amounts']
        fee = data['fee']
        message_data = data.get('message_data')
        tx = cls(fromAddress, toAddress, amounts, fee, message_data)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        tx.public_key = data.get('public_key')
        tx.signature = data.get('signature')
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
        del data['amounts']
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
        tx.public_key = data.get('public_key')
        tx.signature = data.get('signature')

        return tx


class CoinbaseTransaction(Transaction):
    def __init__(self, toAddress, amounts, nonce):
        super().__init__('coinbase', Protocol.coinbase_address.hex(), toAddress, amounts, fee=0, nonce=nonce)
        self.make_hash()

    @classmethod
    def from_dict(cls, data):
        toAddress = data['toAddress']
        amounts = data['amounts']
        nonce = data.get('nonce')
        tx = cls(toAddress, amounts, nonce)
        # tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        return tx


class NodeRegistrationTransaction(Transaction):
    def __init__(self, fromAddress, registration_details):
        super().__init__('node_registration', fromAddress, [], [0], fee=0)

        self.registration_details = registration_details  # Поле для фиксации действия (начисление/штраф)

    def as_dict(self):
        data = super().as_dict()
        data.update({'registration_details': self.registration_details})
        return data

    @classmethod
    def from_dict(cls, data):
        fromAddress = data['fromAddress']

        registration_details = data.get('registration_details', {})
        fee = data['fee']
        tx = cls(fromAddress, registration_details)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        tx.public_key = data.get('public_key')
        tx.signature = data.get('signature')
        return tx

class ReputationTokenTransaction(Transaction):
    def __init__(self, fromAddress, toAddress, amounts, action_details, fee=0):
        super().__init__('reputation_token', fromAddress, toAddress, amounts, fee)
        self.action_details = action_details  # Поле для фиксации действия (начисление/штраф)

    def as_dict(self):
        data = super().as_dict()
        data.update({'action_details': self.action_details})
        return data

    @classmethod
    def from_dict(cls, data):
        fromAddress = data['fromAddress']
        toAddress = data['toAddress']
        amounts = data['amounts']
        action_details = data.get('action_details', {})
        fee = data['fee']
        tx = cls(fromAddress, toAddress, amounts, action_details, fee)
        tx.nonce = data.get('nonce')
        tx.txhash = data.get('txhash')
        tx.public_key = data.get('public_key')
        tx.signature = data.get('signature')
        return tx


class ValidationTransaction(Transaction):
    def __init__(self, fromAddress, block_hash, signature=None, public_key=None, fee=0):
        super().__init__('validation', fromAddress, [], [], fee)
        self.block_hash = block_hash
        self.signature = signature
        self.public_key = public_key

    def as_dict(self):
        data = super().as_dict()
        data.update({
            'block_hash': self.block_hash,
            'signature': self.signature,
            'public_key': self.public_key,
        })
        return data

    @classmethod
    def from_dict(cls, data):
        tx = cls(
            fromAddress=data['fromAddress'],
            block_hash=data['block_hash'],
            signature=data.get('signature'),
            public_key=data.get('public_key'),
            fee=data.get('fee', 0),
        )
        tx.txhash = data['txhash']
        return tx

    def validate_transaction(self):
        """Проверка подписи и связности транзакции."""
        if not XMSS_verify(SigXMSS.from_base64(self.signature), bytes.fromhex(self.block_hash), XMSSPublicKey.from_hex(self.public_key)):
            raise ValueError("Подпись транзакции недействительна.")
        return True



if __name__ == '__main__':
    # t = CoinbaseTransaction("2", 100)
    # t.nonce = 1
    # t.make_hash()
    # print(t.to_json())

    xmss = XMSS.create()
    print(xmss.address)

    tt = TransferTransaction(xmss.address, ["2"], [100], message_data=["test message"])
    tt.nonce = 1
    tt.make_hash()
    tt.make_sign(xmss)
    json_transaction = tt.to_json()
    print(json_transaction)
    tt.validate_sign()

    tt = TransferTransaction("1", ["2", "3", "4"], [100, 100, 100])
    tt.nonce = 1
    tt.make_hash()
    tt.make_sign(xmss)
    print(tt.to_json())
    #
    # st = SlaveTransaction("1", ["slaveAddress123"], ["TRANSFER", "MINING"], 0.01)
    # st.nonce = 1
    # st.make_hash()
    # st.make_sign(xmss)
    # print(st.to_json())

    tt2 = Transaction.from_json(json_transaction)
    print(tt2.to_json())
    if tt2.validate_sign():
        print("Валидация успешна")
