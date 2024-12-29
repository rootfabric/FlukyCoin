import datetime
import hashlib
import time

from core.Transactions import Transaction, CoinbaseTransaction, TransferTransaction, SlaveTransaction, \
    ValidationTransaction
from core.protocol import Protocol
from core.BlockHeader import BlockHeader
import os, json
import random
from storage.transaction_storage import TransactionStorage
import base64
from crypto.xmss import XMSS, XMSSPublicKey, SigXMSS, XMSS_verify
from crypto.mercle import merkle_tx_hash, MerkleTools
from tools.logger import Log


# from crypto.xmss import *


class Block:

    def __init__(self, previousHash=None):

        self.version = Protocol.VERSION
        self.timestamp_seconds_before_validation = None
        self.timestamp_seconds = None

        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000" if previousHash is None else previousHash
        self.merkle_root = None
        self.merkle_root_validators = ""

        self.hash_before_validation = None
        self.hash = ""

        self.sign_before_validation = None

        self.sign = None
        self.signer_pk = None

        # избыточные параметры

        self.block_number = 0
        # адрес публичного ключ того кто сделал блок.
        self.signer = None

        self.transactions: [Transaction] = []

        # Подписи валидаторов
        self.validator_signatures: {str: Transaction} = {}

    def mining_reward(self):
        for tx in self.transactions:
            if tx.tx_type == "coinbase":
                return tx.all_amounts()

    @staticmethod
    def create(
            block_number: int,
            previousHash: bytes,
            timestamp_seconds: int,
            transactions: list,
            address_miner,
            address_reward
    ):

        block = Block()
        block.block_number = block_number
        block.previousHash = Protocol.prev_hash_genesis_block.hex() if previousHash is None else previousHash
        block.timestamp_seconds_before_validation = int(timestamp_seconds)
        block.signer = address_miner

        # Process transactions
        hashedtransactions = []
        fee_reward = 0

        for tx in transactions:
            fee_reward += tx.fee

        # Prepare coinbase tx
        # total_reward_amount = BlockHeader.block_reward_calc(block_number, dev_config) + fee_reward

        # block_reward, ratio, lcs = Protocol.reward(block.signer, sec, block_number=block_number)
        block_reward = Protocol.reward(block_number=block_number)

        total_reward_amount = block_reward + fee_reward

        # coinbase_tx = CoinBase.create(dev_config, total_reward_amount, miner_address, block_number)

        coinbase_nonce = block_number + 1

        coinbase_tx = CoinbaseTransaction(toAddress=[address_reward], amounts=[block_reward], nonce=coinbase_nonce)
        # количество выплат с генезис адреса
        coinbase_tx.nonce = coinbase_nonce

        h = coinbase_tx.txhash
        hashedtransactions.append(h)
        block.transactions.append(coinbase_tx)
        # Block._copy_tx_pbdata_into_block(block, coinbase_tx)  # copy memory rather than sym link
        #
        for tx in transactions:
            hashedtransactions.append(tx.txhash)
            block.transactions.append(tx)
        #     Block._copy_tx_pbdata_into_block(block, tx)  # copy memory rather than sym link
        #
        block.merkle_root = merkle_tx_hash(hashedtransactions)

        #
        # tmp_blockheader = BlockHeader.create(dev_config=dev_config,
        #                                      blocknumber=block_number,
        #                                      prev_headerhash=prev_headerhash,
        #                                      prev_timestamp=prev_timestamp,
        #                                      hashedtransactions=txs_hash,
        #                                      fee_reward=fee_reward,
        #                                      seed_height=seed_height,
        #                                      seed_hash=seed_hash)
        #
        # block.blockheader = tmp_blockheader
        #
        # block._data.header.MergeFrom(tmp_blockheader.pbdata)
        #
        # block.set_nonces(dev_config, 0, 0)

        block.hash_block_before_validation()

        return block

    def make_sign_before_validation(self, xmss: XMSS) -> bytes:
        """ Подпись блока """
        signature = xmss.sign(bytes.fromhex(self.hash_before_validation))

        self.sign_before_validation = signature.to_base64()
        self.signer_pk = xmss.keyPair.PK.to_hex()
        # print(f"Подпись размер: {len(self.sign)} ")

    def make_sign_final(self, xmss: XMSS) -> bytes:
        """ Подпись блока """
        signature = xmss.sign(bytes.fromhex(self.hash))

        self.sign = signature.to_base64()
        self.signer_pk = xmss.keyPair.PK.to_hex()
        # print(f"Подпись размер: {len(self.sign)} ")

    def to_dict(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        block_dict = {
            'hash': self.hash,
            'hash_before_validation': self.hash_before_validation,
            'index': self.block_number,
            'version': self.version,
            'previousHash': self.previousHash,
            'time_before_validation': self.timestamp_seconds_before_validation,
            'time': self.timestamp_seconds,
            'transactions': [tr.to_dict() for tr in self.transactions],
            'validators': [tr.to_dict() for tr in self.validator_signatures.values()],
            'signer': self.signer,
            'merkle_root': self.merkle_root,
            'merkle_root_validators': self.merkle_root_validators,
            'sign_before_validation': self.sign_before_validation,

            'sign': self.sign,
            'signer_pk': self.signer_pk
        }
        return block_dict

    def to_json(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        # Десериализация строки JSON обратно в объект Block
        block_dict = json.loads(json_str)
        block = cls(block_dict['previousHash'])
        block.block_number = block_dict['index']
        block.version = block_dict['version']
        block.timestamp_seconds_before_validation = block_dict['time_before_validation']
        block.timestamp_seconds = block_dict['time']
        block.merkle_root = block_dict['merkle_root']
        block.transactions = [Transaction.from_json(t) for t in block_dict['transactions']]
        block.hash_before_validation = block_dict['hash_before_validation']
        block.hash = block_dict['hash']
        block.signer = block_dict['signer']
        block.sign_before_validation = block_dict['sign_before_validation']
        block.sign = block_dict['sign']
        block.signer_pk = block_dict['signer_pk']
        block.validator_signatures = {Transaction.from_json(t).fromAddress:Transaction.from_json(t) for t in block_dict['validators']}
        block.merkle_root_validators = block_dict['merkle_root_validators']
        return block

    def hash_block_before_validation(self):
        """ Формирование блока"""
        if self.hash_before_validation is None:
            self.hash_before_validation = self.calculate_hash()
        return self.hash_before_validation

    def hash_block_final(self):
        """ Формирование блока"""
        if self.hash is None or self.hash == "":
            self.hash = self.calculate_hash()
        return self.hash

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_block_bytes(self):
        version_bytes = self.version.encode()
        previous_hash_bytes = self.previousHash.encode()
        merkle_root_bytes = self.merkle_root.encode()
        merkle_root_validators_bytes = self.merkle_root_validators.encode()

        # Используем 8 байтов для представления временной метки
        timestamp_bytes_before_validation = self.timestamp_seconds_before_validation.to_bytes(8, byteorder='big')
        timestamp_bytes = self.timestamp_seconds_before_validation.to_bytes(8,
                                                                            byteorder='big') if self.timestamp_seconds_before_validation is not None else b""
        signer_bytes = self.signer.encode()
        return version_bytes + previous_hash_bytes + merkle_root_bytes + merkle_root_validators_bytes + timestamp_bytes_before_validation + timestamp_bytes + signer_bytes

    def calculate_hash(self):
        result = hashlib.sha256(self.get_block_bytes())
        return result.hexdigest()

    def datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp_seconds_before_validation)

    def __equal__(self, other):
        return (self.block_number == other.blocks_count and
                self.timeStamp == other.timestamp and
                self.previousHash == other._previousHash and
                self.hash_before_validation == other.hash_before_validation and
                self.transactions == other.transaction and
                self.nonce == other.nonce
                )

    def XMSSPublicKey(self):
        """ публичный ключ """
        return XMSSPublicKey.from_hex(self.signer_pk)

    def validate_before_validate(self):
        """ Проверка блока """

        old_hash = self.hash_before_validation
        new_hash = self.calculate_hash()

        if old_hash != new_hash:
            print("Ошибка валидации блока. не совпадает хеш")
            return False

        PK2 = self.XMSSPublicKey()
        if self.signer != PK2.generate_address():
            print("Ошибка валидации блока. не совпадает майнер")
            return False

        signature = SigXMSS.from_base64(self.sign_before_validation)

        # Верификация подписи
        verf = XMSS_verify(signature, bytes.fromhex(new_hash), PK2)
        if not verf:
            print("Ошибка валидации блока. не совпадает подпись")
            return False

        """
        дополнительно нужна валидация дерева меркле
        """

        mt = MerkleTools(hash_type="SHA256")

        for transaction in self.transactions:
            mt.add_leaf(transaction.txhash)
        mt.make_tree()
        if not mt.is_ready:
            print("Ошибка валидации MerkleTools. is_ready False")
            return False

        if mt.get_merkle_root() != self.merkle_root:
            print("Ошибка валидации MerkleTools. Не верный merkle_root")
            return False

        return True

    ###########################
    ### Функции валидации финального блока

    def validate_final(self):
        """ Проверка блока """

        old_hash = self.hash
        new_hash = self.calculate_hash()

        if old_hash != new_hash:
            print("Ошибка валидации блока. не совпадает хеш")
            return False

        PK2 = self.XMSSPublicKey()
        if self.signer != PK2.generate_address():
            print("Ошибка валидации блока. не совпадает майнер")
            return False

        signature = SigXMSS.from_base64(self.sign)

        # Верификация подписи
        verf = XMSS_verify(signature, bytes.fromhex(new_hash), PK2)
        if not verf:
            print("Ошибка валидации блока. не совпадает подпись")
            return False

        """
        дополнительно нужна валидация дерева меркле
        """

        mt = MerkleTools(hash_type="SHA256")

        for transaction in self.transactions:
            mt.add_leaf(transaction.txhash)
        mt.make_tree()
        if not mt.is_ready:
            print("Ошибка валидации MerkleTools. is_ready False")
            return False

        if mt.get_merkle_root() != self.merkle_root:
            print("Ошибка валидации MerkleTools. Не верный merkle_root")
            return False

        return True

    def add_validator_signature(self, validator_transaction: ValidationTransaction):
        """
        Добавить подпись от валидатора.
        """
        if validator_transaction.fromAddress in self.validator_signatures:
            print(f"Валидатор {validator_transaction.fromAddress} уже подписал блок.")
            return False
        self.validator_signatures[validator_transaction.fromAddress] = validator_transaction
        return True

    def is_finalized(self, required_signatures_count=1):
        """
        Проверить, можно ли считать блок финализированным.
        """
        return len(self.validator_signatures) >= required_signatures_count

    def finalize_block(self, xmss):
        """
        Финализировать блок, подписав его повторно.
        """
        if not self.is_finalized(len(self.validator_signatures)):
            print("Недостаточно подписей для финализации блока.")
            return False

        # Обновить хеш с учетом подписей валидаторов
        self.hash_before_validation = self.calculate_hash_with_signatures()
        # Повторная подпись блока
        self.make_sign_before_validation(xmss)
        return True

    def calculate_hash_with_signatures(self, time_calculate):
        """ добавляются транзакции валидаторов и делается финальный hash """

        hashedtransactions_validator = []
        for tx_validator in self.validator_signatures.values():
            hashedtransactions_validator.append(tx_validator.txhash)

        self.merkle_root_validators = merkle_tx_hash(hashedtransactions_validator)

        # финальное время подписи
        self.timestamp_seconds = time_calculate
        self.hash_block_final()


if __name__ == '__main__':
    """ """
