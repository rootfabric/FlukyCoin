import sqlite3
import json
import os
import zlib
from core.Transactions import Transaction
import threading

class TransactionStorage:
    def __init__(self, db_name='transactions', dir=""):
        self.dir = dir
        self.db_name = db_name
        self.local = threading.local()  # Используем локальные данные потока
        self._init_db()
        self.miners = self._load_miners()

    def _init_db(self):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        self.db_path = os.path.join(dir_path, 'transactions.db')

    def _get_conn(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self._create_tables(self.local.conn)
        return self.local.conn

    def _create_tables(self, conn):
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS kv_store
                            (key TEXT PRIMARY KEY, value BLOB)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS miners
                            (address TEXT PRIMARY KEY)''')

    def _load_miners(self):
        miners = set()
        with self._get_conn() as conn:
            for row in conn.execute('SELECT address FROM miners'):
                miners.add(row[0])
        return miners

    def _save_miners(self):
        with self._get_conn() as conn:
            conn.execute('DELETE FROM miners')
            conn.executemany('INSERT INTO miners (address) VALUES (?)', [(miner,) for miner in self.miners])

    def get_transaction(self, hash):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key=?', (hash,))
            row = cursor.fetchone()
            if row:
                return Transaction.from_json(zlib.decompress(row[0]).decode())
        return None

    def clear(self):
        with self._get_conn() as conn:
            conn.execute('DELETE FROM kv_store')
        self._save_miners()

    def add_block(self, block):
        address_reward = None

        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                address_reward = transaction.toAddress[0]
                break

        for transaction in block.transactions:
            self.add_transaction(transaction, address_reward)

        self.miners.add(block.signer)
        self.add_nonce_to_address(block.signer)
        self._save_miners()

    def add_transaction(self, transaction: Transaction, address_reward: str):
        from_address = transaction.fromAddress
        amounts = transaction.all_amounts()
        fee = transaction.fee
        to_address = transaction.toAddress

        if transaction.tx_type != "coinbase" and self.get_balance(from_address) < amounts + fee:
            return False

        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                         (transaction.txhash, zlib.compress(transaction.to_json().encode())))

        self._update_balance(from_address, self.get_balance(from_address) - amounts - fee)
        self._update_balance(address_reward, self.get_balance(address_reward) + fee)

        for i, address in enumerate(to_address):
            self._update_balance(address, self.get_balance(address) + transaction.amounts[i])

        self.add_nonce_to_address(from_address)

        return True

    def add_nonce_to_address(self, address):
        self._update_nonce(address, self.get_nonce(address) + 1)

    def pop_nonce_to_address(self, address):
        self._update_nonce(address, max(0, self.get_nonce(address) - 1))

    def get_balance(self, address):
        balance_key = f"balance_{address}"
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key=?', (balance_key,))
            row = cursor.fetchone()
            if row:
                return int(float(zlib.decompress(row[0]).decode()))
        return 0

    def _update_balance(self, address, new_balance):
        balance_key = f"balance_{address}"
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                         (balance_key, zlib.compress(str(new_balance).encode())))

    def get_nonce(self, address):
        nonce_key = f"nonce_{address}"
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT value FROM kv_store WHERE key=?', (nonce_key,))
            row = cursor.fetchone()
            if row:
                return int(zlib.decompress(row[0]).decode())
        return 0

    def _update_nonce(self, address, new_nonce):
        nonce_key = f"nonce_{address}"
        with self._get_conn() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                         (nonce_key, zlib.compress(str(new_nonce).encode())))

    def get_all_balances(self):
        balances = {}
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT key, value FROM kv_store WHERE key LIKE "balance_%"')
            for row in cursor:
                address = row[0][8:]
                balances[address] = int(float(zlib.decompress(row[1]).decode()))
        return balances

    def get_addresses_sorted_by_balance(self):
        return sorted(self.get_all_balances().items(), key=lambda x: x[1], reverse=True)

    def to_json(self):
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT key, value FROM kv_store WHERE key NOT LIKE "nonce_%" AND key NOT LIKE "balance_%" AND key NOT LIKE "miners"')
            transactions = {row[0]: zlib.decompress(row[1]).decode() for row in cursor}
        return json.dumps({
            'balances': self.get_all_balances(),
            'nonces': {k: self.get_nonce(k) for k in self.get_all_balances().keys()},
            'transactions': transactions,
            'miners': list(self.miners)
        })

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        storage = cls()
        with storage._get_conn() as conn:
            for k, v in data['transactions'].items():
                conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                             (k, zlib.compress(v.encode())))
            for address, balance in data['balances'].items():
                conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                             (f"balance_{address}", zlib.compress(str(balance).encode())))
            for address, nonce in data['nonces'].items():
                conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)',
                             (f"nonce_{address}", zlib.compress(str(nonce).encode())))
        storage.miners = set(data['miners'])
        storage._save_miners()
        return storage

    def rollback_block(self, block):
        address_reward = None
        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                address_reward = transaction.toAddress[0]
                break

        for transaction in reversed(block.transactions):
            self.rollback_transaction(transaction, address_reward)

        if block.signer in self.miners:
            self.miners.remove(block.signer)
        self.pop_nonce_to_address(block.signer)
        self._save_miners()

    def rollback_transaction(self, transaction: Transaction, address_reward):
        from_address = transaction.fromAddress
        amounts = transaction.all_amounts()
        fee = transaction.fee
        to_address = transaction.toAddress

        with self._get_conn() as conn:
            conn.execute('DELETE FROM kv_store WHERE key=?', (transaction.txhash,))

        if transaction.tx_type == 'coinbase':
            for i, address in enumerate(to_address):
                self._update_balance(address, self.get_balance(address) - transaction.amounts[i])
        else:
            self._update_balance(from_address, self.get_balance(from_address) + amounts + fee)
            self._update_balance(address_reward, self.get_balance(address_reward) - fee)
            for i, address in enumerate(to_address):
                self._update_balance(address, self.get_balance(address) - transaction.amounts[i])

        self.pop_nonce_to_address(from_address)

    def get_transactions_by_address(self, address, transactions_start=0, transactions_end=0):
        filtered_transactions = []
        with self._get_conn() as conn:
            cursor = conn.execute('SELECT key, value FROM kv_store WHERE key NOT LIKE "nonce_%" AND key NOT LIKE "balance_%" AND key NOT LIKE "miners"')
            for row in cursor:
                transaction = Transaction.from_json(zlib.decompress(row[1]).decode())
                if transaction.fromAddress == address or address in transaction.toAddress:
                    filtered_transactions.append(transaction)
        return filtered_transactions[transactions_start:transactions_end]
