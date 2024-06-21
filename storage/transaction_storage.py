from core.Transactions import Transaction
import json
import dbm
import os
import zlib
import datetime


class TransactionStorage:
    def __init__(self, db_name='transactions', dir=""):
        self.dir = dir
        self.db_name = db_name
        self.miners = self._load_miners()

    def _open_db(self, mode='c'):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        db_path = os.path.join(dir_path, 'transactions.db')

        if mode == 'r' and not os.path.exists(db_path):
            with dbm.open(db_path, 'c'):
                pass

        return dbm.open(db_path, mode)

    def _load_miners(self):
        with self._open_db() as db:
            if b'miners' in db:
                return set(json.loads(zlib.decompress(db[b'miners']).decode()))
            return set()

    def _save_miners(self):
        with self._open_db() as db:
            db[b'miners'] = zlib.compress(json.dumps(list(self.miners)).encode())

    def get_transaction(self, hash):
        with self._open_db() as db:
            if hash in db:
                return Transaction.from_json(zlib.decompress(db[hash]).decode())
        return None

    def clear(self):
        with self._open_db() as db:
            db.clear()
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

        t = datetime.datetime.now()

        if transaction.tx_type != "coinbase" and self.get_balance(from_address) < amounts + fee:
            return False

        with self._open_db() as db:
            db[transaction.txhash] = zlib.compress(transaction.to_json().encode())

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
        with self._open_db() as db:
            balance_key = f"balance_{address}".encode()
            value = db.get(balance_key, None)
            if value is None:
                return 0
            return int(float(zlib.decompress(value).decode()))

    def _update_balance(self, address, new_balance):
        with self._open_db() as db:
            balance_key = f"balance_{address}".encode()
            db[balance_key] = zlib.compress(str(new_balance).encode())

    def get_nonce(self, address):
        with self._open_db() as db:
            nonce_key = f"nonce_{address}".encode()
            value = db.get(nonce_key, None)
            if value is None:
                return 0
            return int(zlib.decompress(value).decode())

    def _update_nonce(self, address, new_nonce):
        with self._open_db() as db:
            nonce_key = f"nonce_{address}".encode()
            db[nonce_key] = zlib.compress(str(new_nonce).encode())

    def get_all_balances(self):
        balances = {}
        with self._open_db() as db:
            for key in db.keys():
                if key.startswith(b'balance_'):
                    address = key.decode()[8:]
                    balances[address] = int(float(zlib.decompress(db[key]).decode()))
        return balances

    def get_addresses_sorted_by_balance(self):
        return sorted(self.get_all_balances().items(), key=lambda x: x[1], reverse=True)

    def to_json(self):
        with self._open_db() as db:
            transactions = {k.decode(): zlib.decompress(v).decode() for k, v in db.items() if not k.startswith(b'nonce_') and not k.startswith(b'balance_') and not k.startswith(b'miners')}
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
        with storage._open_db() as db:
            for k, v in data['transactions'].items():
                db[k.encode()] = zlib.compress(v.encode())
            for address, balance in data['balances'].items():
                db[f"balance_{address}".encode()] = zlib.compress(str(balance).encode())
            for address, nonce in data['nonces'].items():
                db[f"nonce_{address}".encode()] = zlib.compress(str(nonce).encode())
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

        with self._open_db() as db:
            if transaction.txhash in db:
                del db[transaction.txhash]

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
        with self._open_db() as db:
            for key in db.keys():
                if not key.startswith(b'nonce_') and not key.startswith(b'balance_') and not key.startswith(b'miners'):
                    transaction = Transaction.from_json(zlib.decompress(db[key]).decode())
                    if transaction.fromAddress == address or address in transaction.toAddress:
                        filtered_transactions.append(transaction)
        return filtered_transactions[transactions_start:transactions_end]
