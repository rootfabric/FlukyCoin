import datetime
import hashlib
import time

from core.Transactions import Transaction, CoinbaseTransaction, TransferTransaction, SlaveTransaction
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
        self.timestamp_seconds = None
        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000" if previousHash is None else previousHash
        self.merkle_root = None

        self.sign = None
        self.hash = None
        self.signer_pk = None

        # избыточные параметры

        self.block_number = 0
        # адрес публичного ключ того кто сделал блок.
        self.signer = None

        self.transactions: [Transaction] = []
        self.validators = []
        # self.log = Log()

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
            address_reward,
            validators=None
    ):

        block = Block()
        block.block_number = block_number
        block.previousHash = Protocol.prev_hash_genesis_block.hex() if previousHash is None else previousHash
        block.timestamp_seconds = int(timestamp_seconds)
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

        if validators is not None:
            if block_number != 0:
                raise ValueError("Validators can be attached only to the genesis block")
            block.validators = Block._normalize_validators(validators)
        else:
            block.validators = []

        block.hash_block()

        return block

    @staticmethod
    def _normalize_validators(validators):
        if validators is None:
            return []

        normalized = []

        for entry in validators:
            if isinstance(entry, dict):
                address = entry.get('address')
                stake = entry.get('stake', 0)
                public_key = entry.get('public_key') if entry.get('public_key') is not None else None
            elif isinstance(entry, (list, tuple)):
                if len(entry) < 2:
                    raise ValueError('Validator entry must contain at least address and stake')
                address, stake = entry[0], entry[1]
                public_key = entry[2] if len(entry) > 2 else None
            else:
                raise TypeError('Validator entry must be a dict, list or tuple')

            if address is None:
                raise ValueError('Validator address is required')

            try:
                stake_value = int(stake)
            except (TypeError, ValueError):
                raise ValueError(f'Invalid stake value for validator {address}')

            validator_data = {
                'address': address,
                'stake': stake_value
            }

            if public_key is not None:
                validator_data['public_key'] = public_key

            normalized.append(validator_data)

        normalized.sort(key=lambda item: item['address'])
        return normalized

    def make_sign(self, xmss: XMSS) -> bytes:
        """ Подпись блока """
        signature = xmss.sign(bytes.fromhex(self.hash))

        self.sign = signature.to_base64()
        self.signer_pk = xmss.keyPair.PK.to_hex()
        # print(f"Подпись размер: {len(self.sign)} ")

    def to_dict(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        block_dict = {
            'index': self.block_number,
            'version': self.version,
            'previousHash': self.previousHash,
            'time': self.timestamp_seconds,
            'transactions': [tr.to_dict() for tr in self.transactions],
            'hash': self.hash,
            'signer': self.signer,
            'merkle_root': self.merkle_root,
            'sign': self.sign,
            'signer_pk': self.signer_pk,
            'validators': self.validators
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
        block.timestamp_seconds = block_dict['time']
        block.merkle_root = block_dict['merkle_root']
        block.transactions = [Transaction.from_json(t) for t in block_dict['transactions']]
        block.hash = block_dict['hash']
        block.signer = block_dict['signer']
        block.sign = block_dict['sign']
        block.signer_pk = block_dict['signer_pk']
        block.validators = Block._normalize_validators(block_dict.get('validators', []))
        return block

    def hash_block(self):
        """ Формирование блока"""
        if self.hash is None:
            self.hash = self.calculate_hash()
        return self.hash

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_block_bytes(self):
        version_bytes = (self.version or "").encode()
        previous_hash_bytes = (self.previousHash or "").encode()
        merkle_root_bytes = (self.merkle_root or "").encode()

        # Используем 8 байтов для представления временной метки
        timestamp = int(self.timestamp_seconds or 0)
        timestamp_bytes = timestamp.to_bytes(8, byteorder='big', signed=False)
        signer_bytes = (self.signer or "").encode()
        validators_bytes = json.dumps(self.validators, sort_keys=True).encode()
        return version_bytes + previous_hash_bytes + merkle_root_bytes + timestamp_bytes + signer_bytes + validators_bytes

    def calculate_hash(self):
        result = hashlib.sha256(self.get_block_bytes())
        return result.hexdigest()

    def datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp_seconds)

    def __equal__(self, other):
        return (self.block_number == other.blocks_count and
                self.timeStamp == other.timestamp and
                self.previousHash == other._previousHash and
                self.hash == other.hash and
                self.transactions == other.transaction and
                self.nonce == other.nonce
                )

    def XMSSPublicKey(self):
        """ публичный ключ """
        return XMSSPublicKey.from_hex(self.signer_pk)

    def validate(self):
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


if __name__ == '__main__':
    """ """
