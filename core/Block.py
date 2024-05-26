import datetime
import hashlib
import time

from core.transaction import Transaction
from core.protocol import Protocol
from core.BlockHeader import BlockHeader
import os, json
import random
from storage.transaction_storage import TransactionStorage, TransactionGenerator
import base64
from crypto.xmss import XMSS
from crypto.mercle import merkle_tx_hash


# from crypto.xmss import *


class Block:

    def __init__(self, previousHash=None):

        # self.bh = BlockHeader()
        self.version = Protocol.VERSION
        self.timestamp_seconds = None
        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000" if previousHash is None else previousHash
        self.merkle_root = None

        self.sign = None
        self.Hash = None

        # избыточные параметры

        self.block_number = 0
        # адрес публичного ключ того кто сделал блок.
        self.signer = None

        self.transactions = []

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
        block.previousHash = Protocol.prev_hash_genesis_block if previousHash is None else previousHash
        block.timestamp_seconds = int(timestamp_seconds)
        block.signer = address_miner
        # Process transactions
        hashedtransactions = []
        fee_reward = 0

        for tx in transactions:
            fee_reward += tx.fee

        # Prepare coinbase tx
        # total_reward_amount = BlockHeader.block_reward_calc(block_number, dev_config) + fee_reward
        sec = Protocol.sequence(block.previousHash)
        block_reward, ratio, lcs = Protocol.reward(block.signer, sec)

        total_reward_amount = block_reward + fee_reward

        # coinbase_tx = CoinBase.create(dev_config, total_reward_amount, miner_address, block_number)

        coinbase_tx = Transaction(tx_type="coinbase", fromAddress=Protocol.coinbase_address.hex(),
                                  toAddress=address_reward, amount=block_reward)

        h = coinbase_tx.txhash.hexdigest()
        hashedtransactions.append(h)
        # Block._copy_tx_pbdata_into_block(block, coinbase_tx)  # copy memory rather than sym link
        #
        for tx in transactions:
            hashedtransactions.append(tx.txhash)
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

        block.hash_block()

        return block

    def make_sign(self, xmss: XMSS) -> bytes:
        """ Подпись блока """
        signature = xmss.sign(bytes.fromhex(self.Hash))
        print(f"Подпись: {signature}, размер: {len(signature.to_bytes())} байт")
        self.sign =signature.to_bytes()
        self.pk_signer = xmss.keyPair.PK.to_str()
        return self.sign

    def to_json(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        block_dict = {
            'index': self.block_number,
            'previousHash': self.previousHash,
            'time': self.timestamp_seconds,
            'transactions': [tr.to_json() for tr in self.transactions],
            'hash': self.Hash,
            # 'diff_key_block': self.diff_key_block,
            'signer': self.signer,
            'sign': self.sign,
            # 'winer_ratio': self.winer_ratio,
            # 'winer_address': self.winer_address
        }
        return json.dumps(block_dict)

    @classmethod
    def from_json(cls, json_str):
        # Десериализация строки JSON обратно в объект Block
        block_dict = json.loads(json_str)
        block = cls(block_dict['previousHash'])
        block.block_number = block_dict['index']
        block.timestamp_seconds = block_dict['time']
        block.transactions = [Transaction.from_json(t) for t in block_dict['transactions']]
        block.Hash = block_dict['hash']
        # block.diff_key_block = block_dict['diff_key_block']
        block.signer = block_dict['signer']
        block.sign = block_dict['sign']
        # block.winer_ratio = block_dict['winer_ratio']
        # block.winer_address = block_dict['winer_address']
        return block

    def hash_block(self):
        """ Формирование блока"""
        if self.Hash is None:
            self.Hash = self.calculate_hash()
        return self.Hash

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def get_block_bytes(self):
        version_bytes = self.version.encode()
        previous_hash_bytes = self.previousHash
        merkle_root_bytes = self.merkle_root.encode()

        # Используем 8 байтов для представления временной метки
        timestamp_bytes = self.timestamp_seconds.to_bytes(8, byteorder='big')
        signer_bytes = self.signer.encode()
        return version_bytes + previous_hash_bytes + merkle_root_bytes + timestamp_bytes + signer_bytes

    def calculate_hash(self):
        result = hashlib.sha256(self.get_block_bytes())
        return result.hexdigest()

    def datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp_seconds)

    def __equal__(self, other):
        return (self.block_number == other.blocks_count and
                self.timeStamp == other.timestamp and
                self.previousHash == other.previousHash and
                self.Hash == other.Hash and
                self.transactions == other.transaction and
                self.nonce == other.nonce
                )


if __name__ == '__main__':
    """ """
    # r = random.Random(1)
    # bits = 128
    # sequence = r.getrandbits(bits).to_bytes(bits // 8, byteorder='big').hex()
    # print(sequence)
    # exit(0)

    # transaction_storage = TransactionStorage()
    #
    # # Использование генератора транзакций
    # generator = TransactionGenerator(address_count=2, transaction_count=100)
    # transactions = generator.generate_transactions_from_genesis()
    # for transaction in transactions:
    #     transaction_storage.add_transaction(transaction)
    #
    # generator = TransactionGenerator(address_count=2, transaction_count=100)
    # transactions = generator.generate_transactions()
    # for transaction in transactions:
    #     transaction_storage.add_transaction(transaction)
    #
    # # tr = [Transaction('0', 'a1', 10), Transaction("a1", "a2", 1)]
    # block = Block(timeStamp=datetime.datetime.now(), previousHash="123",
    #               transactions=transaction_storage)
    #
    # block.addresses = [a[0] for a in transaction_storage.get_addresses_sorted_by_balance()]
    #
    # for i in range(10000):
    #     sequence = random.getrandbits(128).to_bytes(128 // 8, byteorder='big').hex()
    #     block.addresses.append(sequence)
    #
    # block.find_winner()
    # # block.save()
    # print(block.nonce, block.hash)
