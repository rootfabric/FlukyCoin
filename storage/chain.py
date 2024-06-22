import threading
import datetime
from core.Block import Block
import base64
from storage.transaction_storage import TransactionStorage
from core.protocol import Protocol
from core.Transactions import Transaction
from storage.mempool import Mempool
import copy
import time
from tools.time_sync import NTPTimeSynchronizer
import os
import pickle
from tools.logger import Log
import sqlite3
import zlib

class Chain():
    def __init__(self, config=None, time_ntpt=None, mempool=None, log=Log(), node_dir_base=None):
        self.config = config if config is not None else {}
        if node_dir_base is None:
            self.dir = str(f'{self.config.get("host", "localhost")}:{self.config.get("port", "5555")}')
        else:
            self.dir = node_dir_base

        self.transaction_storage = TransactionStorage(dir=self.dir)
        self.mempool: Mempool = mempool
        self.protocol = Protocol()
        self.log = log

        self.local = threading.local()  # Initialize thread-local storage

        self._init_db()  # Initialize the database connection and tables

        self.difficulty = self._load_difficulty()

        self.block_candidate: Block = None

        self.time_ntpt = NTPTimeSynchronizer(log=self.log) if time_ntpt is None else time_ntpt

        self.history_hash = {}

        self._previousHash = Protocol.prev_hash_genesis_block.hex()

    def _init_db(self):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.db_path = os.path.join(dir_path, 'blocks.db')

    def _get_conn(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self._create_tables()
        return self.local.conn

    def _create_tables(self):
        with self._get_conn() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS kv_store
                            (key TEXT PRIMARY KEY, value BLOB)''')

    def clear_db(self):
        with self._get_conn() as conn:
            conn.execute('DELETE FROM kv_store')
        self._save_difficulty(0)

    def block_by_number_from_chain(self, num):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key=?', (f'block_{num}',))
            row = cursor.fetchone()
            if row:
                return Block.from_json(zlib.decompress(row[0]).decode())
        return None

    def blocks_count(self):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM kv_store WHERE key LIKE "block_%"')
            return cursor.fetchone()[0]

    def last_block(self):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT key, value FROM kv_store WHERE key LIKE "block_%" ORDER BY CAST(SUBSTR(key, 7) AS INTEGER) DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                try:
                    return Block.from_json(zlib.decompress(row[1]).decode())
                except zlib.error as e:
                    self.log.error(f"Failed to decompress data for last block: {e}")
        return None

    def last_block_hash(self):
        last_block = self.last_block()
        return last_block.hash_block() if last_block else Protocol.prev_hash_genesis_block.hex()

    def last_block_time(self):
        last_block = self.last_block()
        return last_block.timestamp_seconds if last_block else 0

    def save_chain_to_disk(self, filename='blockchain.db'):
        self.transaction_storage.save_to_disk(self.dir)
        self._save_difficulty(self.difficulty)

        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        full_path = os.path.join(dir_path, 'block_candidate.pickle')
        with open(full_path, 'wb') as file:
            pickle.dump(None if self.block_candidate is None else self.block_candidate.to_json(), file)

    def _load_difficulty(self):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key=?', (b'difficulty',))
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def _save_difficulty(self, difficulty):
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                         (b'difficulty', str(difficulty).encode()))

    def calculate_difficulty(self):
        self.difficulty = 0
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key LIKE "block_%"')
            for row in cursor:
                block = Block.from_json(zlib.decompress(row[0]).decode())
                self.difficulty += self.block_difficulty(block)

    def load_from_disk(self, filename='blockchain.db'):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        full_path = os.path.join(dir_path, 'block_candidate.pickle')
        try:
            with open(full_path, 'rb') as file:
                block_candidate_json = pickle.load(file)
                if block_candidate_json is not None:
                    self.block_candidate = Block.from_json(block_candidate_json)
        except FileNotFoundError:
            self.log.error("No block candidate file found.")
        except Exception as e:
            self.log.error(f"Failed to load block candidate: {e}")

        self.calculate_difficulty()

        self.log.info(
            f"Blockchain loaded from disk. {self.blocks_count()} blocks, miners: {len(self.transaction_storage.miners)} all_ratio: {self.difficulty}")

    def _add_block(self, block: Block):
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                         (f'block_{block.block_number}', zlib.compress(block.to_json().encode())))

        self.transaction_storage.add_block(block)

        self.difficulty += self.block_difficulty(block)

        self._save_difficulty(self.difficulty)

        self.add_history_hash(block)

        if self.mempool is not None:
            self.mempool.remove_transactions_in_block(block)

    def drop_last_block(self):
        last_block = self.last_block()
        if last_block is None:
            return False

        self.transaction_storage.rollback_block(last_block)

        with self._get_conn() as conn:
            conn.execute('DELETE FROM kv_store WHERE key=?', (f'block_{last_block.block_number}',))

        if last_block.hash_block() in self.history_hash:
            self.history_hash.pop(last_block.hash_block())

        self.difficulty -= self.block_difficulty(last_block)
        self._save_difficulty(self.difficulty)
        return True

    def time(self):
        return self.time_ntpt.get_corrected_time()

    @property
    def block_candidate_hash(self):
        return self.block_candidate.hash_block() if self.block_candidate is not None else None

    def reset_block_candidat(self):
        self.block_candidate = None

    def check_hash(self, block_hash):
        if block_hash in self.history_hash:
            return self.history_hash[block_hash]
        return None

    def add_history_hash(self, block):
        self.history_hash[block.hash_block()] = block

    def block_difficulty(self, block: Block):
        ratio, _ = Protocol.find_longest_common_substring(block.signer, block.previousHash, convert_to_sha256=True)
        address_height = Protocol.address_height(block.signer)
        return ratio * address_height

    def validate_block_hash(self, block: Block):
        if block.previousHash != self.last_block_hash():
            return False
        return True

    def validate_block_time(self, block: Block):
        if self.last_block() is None:
            return True

        if block.timestamp_seconds <= self.last_block().timestamp_seconds:
            self.log.warning("Блок не проходит валидацию по времени")
            return False

        return True

    def validate_block_number(self, block: Block):
        if block.block_number != self.blocks_count():
            self.log.warning("Блок не проходит валидацию по номеру")
            return False
        return True

    def next_address_nonce(self, address):
        return self.transaction_storage.get_nonce(address) + 1

    def address_balance(self, address):
        return self.transaction_storage.get_balance(address)

    def validate_transaction(self, transaction: Transaction):
        address_nonce = self.next_address_nonce(transaction.fromAddress)
        if transaction.nonce != address_nonce:
            self.log.warning(f"Транзакция не валидна. nonce цепи: {address_nonce} nonce транзакции:{transaction.nonce}")
            return False

        if transaction.tx_type != "coinbase" and not transaction.validate_sign():
            self.log.warning(f"Транзакция не валидна no подписи")
            return False

        if transaction.tx_type != "coinbase":
            if transaction.PK.max_height() <= address_nonce:
                self.log.warning(f"Транзакция не валидна: превышен порог подписей")
                return False

        if transaction.tx_type == "transfer":
            if self.address_balance(transaction.fromAddress) < transaction.all_amounts() + transaction.fee:
                self.log.warning(f"Транзакция не валидна. Остаток: {self.address_balance(transaction.fromAddress)} < amounts:{transaction.all_amounts()} + fee {transaction.fee}")
                return False

        return True

    def validate_nonce_key(self, block: Block):
        PK = block.XMSSPublicKey()
        address = PK.generate_address()
        n = self.next_address_nonce(address)

        if PK.max_height() < self.next_address_nonce(address):
            self.log.warning(f"PK.max_height() {PK.max_height()} self.next_address_nonce(PK.generate_address()) {self.next_address_nonce(address)}")
            self.log.warning("Количество подписей больше высоты")
            return False
        return True

    def validate_rewards(self, block: Block):
        coinbase_transaction: Transaction = None
        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                coinbase_transaction = transaction
                break

        if coinbase_transaction is None:
            self.log.warning(f"Нету coinbase транзакции")
            return False

        block_num = block.block_number

        if block_num != coinbase_transaction.nonce - 1:
            self.log.warning(f"Неверный nonce coinbase транзакции")
            return False

        block_reward = Protocol.reward(block_number=block_num)
        amount = coinbase_transaction.all_amounts()

        if amount != block_reward:
            self.log.warning(f"Неверное вознаграждение блока {block_reward} нужно: {amount}")
            return False

        return True

    def validate_block(self, block: Block):
        if block is None:
            return False

        if not block.validate():
            return False

        if not self.validate_block_hash(block):
            return False

        if not self.validate_block_time(block):
            return False

        if not self.validate_block_number(block):
            return False

        if not self.validate_nonce_key(block):
            return False

        count_coinbase = 0
        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                count_coinbase += 1

            if not self.validate_transaction(transaction):
                self.log.warning(f"Транзакция {transaction.txhash} не валидна")
                if self.mempool is not None:
                    self.mempool.remove_transaction(transaction.txhash)
                return False

        if not self.validate_rewards(block):
            self.log.warning(f"Неверное вознаграждение за блок")
            return False

        if count_coinbase != 1:
            self.log.warning(f"Неверно количество coinbase транзакций: {count_coinbase} шт")
            return False

        return True

    def validate_and_add_block(self, block):
        if block is None:
            self.log.warning("validate block is None")
            return False

        if not self.validate_block(block):
            return False

        self._add_block(block)

        return True

    def check_miners(self, addr):
        return addr in self.transaction_storage.miners

    def validate_candidate(self, block: Block):
        if self.last_block() is None:
            return True

        if block.previousHash != self.last_block().hash_block():
            return False

        if block.timestamp_seconds < self.last_block().timestamp_seconds:
            return False

        return True

    def add_block_candidate(self, block: Block):
        if block is None:
            return False

        if not self.validate_candidate(block):
            return False

        if not self.validate_block(block):
            return False

        if self.last_block() is None and self.block_candidate is None:
            self.block_candidate = Block.from_json(block.to_json())
            self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
            return True

        if self.block_candidate is None:
            self.block_candidate = Block.from_json(block.to_json())
            self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
            return True

        if block.hash_block() == self.block_candidate.hash_block():
            return False

        if not self.validate_candidate(block):
            return False

        self._previousHash = Protocol.prev_hash_genesis_block.hex() if self.last_block() is None else self.last_block().hash

        win_address = self.protocol.winner([self.block_candidate.signer, block.signer], self._previousHash)
        if win_address == self.block_candidate.signer:
            return False

        self.block_candidate = Block.from_json(block.to_json())
        self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)

        return True

    def try_address_candidate(self, address_candidate, candidate_signer):
        if address_candidate == candidate_signer:
            return False

        self._previousHash = Protocol.prev_hash_genesis_block.hex() if self.last_block() is None else self.last_block().hash

        win_address = self.protocol.winner([candidate_signer, address_candidate], self._previousHash)

        if win_address == candidate_signer:
            return False

        return True

    def close_block(self):
        if self.block_candidate is None:
            self.log.info("Кандидат None. Блок нельзя закрыть")
            return False
        if self.validate_and_add_block(Block.from_json(self.block_candidate.to_json())):
            self.reset_block_candidat()
            return True
        else:
            self.log.info("Не валидный блок для закрытия")
            self.reset_block_candidat()
            return False

    def need_close_block(self):
        if self.block_candidate is None:
            return False

        last_block = self.last_block()
        if last_block is not None:
            if last_block.timestamp_seconds + Protocol.BLOCK_TIME_SECONDS > self.time():
                return False

        if self.block_candidate.timestamp_seconds > self.time():
            return False

        return True
