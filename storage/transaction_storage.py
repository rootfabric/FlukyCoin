from core.Transactions import Transaction
import json


class TransactionStorage:
    def __init__(self):
        # Словарь для хранения балансов адресов. Ключ - адрес, значение - баланс.
        self.balances = {}

        # Словарь для хранения nonce адресов. Ключ - адрес, значение - nonce.
        self.nonces = {}

        # Словарь для хранения всех транзакций. Ключ - хэш транзакции, значение - объект транзакции.
        self.transactions = {}

        # список майнеров
        self.miners = set()

    def get_transaction(self, hash):
        return self.transactions.get(hash)

    def clear(self):
        self.balances.clear()
        self.nonces.clear()
        self.transactions.clear()
        self.miners.clear()

    def add_block(self, block):
        """Добавляем все данные по блоку в хранилище"""
        address_reward = None
        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                address_reward = transaction.toAddress[0]
                break

        for transaction in block.transactions:
            self.add_transaction(transaction, address_reward)

        # Добавляем майнера
        self.miners.add(block.signer)

        # Учитываем подпись ключа блока
        self.add_nonce_to_address(block.signer)

    def add_transaction(self, transaction: Transaction, address_reward: str):
        """
        Добавляет транзакцию и обновляет балансы адресов, если у отправителя достаточно средств.

        :param transaction: объект транзакции
        """
        from_address = transaction.fromAddress
        amounts = transaction.all_amounts()
        fee = transaction.fee
        to_address = transaction.toAddress

        # Проверка наличия средств
        if transaction.tx_type != "coinbase" and self.get_balance(from_address) < amounts + fee:
            return False

        # Добавление транзакции в словарь транзакций
        self.transactions[transaction.txhash] = transaction

        # Обновление баланса отправителя и получателя
        self.balances[from_address] = self.balances.get(from_address, 0) - amounts - fee

        # Награда на адрес, который указал майнер для получения
        self.balances[address_reward] = self.balances.get(address_reward, 0) + fee

        for i, address in enumerate(to_address):
            self.balances[address] = self.balances.get(address, 0) + transaction.amounts[i]

        # Обновление nonce для адреса отправителя
        self.add_nonce_to_address(from_address)

        return True

    def add_nonce_to_address(self, address):
        if address in self.nonces:
            self.nonces[address] += 1
        else:
            self.nonces[address] = 1

    def pop_nonce_to_address(self, address):
        if address in self.nonces:
            self.nonces[address] -= 1

    def get_balance(self, address):
        return self.balances.get(address, 0)

    def get_nonce(self, address):
        return self.nonces.get(address, 0)

    def get_all_balances(self):
        return self.balances

    def get_addresses_sorted_by_balance(self):
        return sorted(self.balances.items(), key=lambda x: x[1] / 100000000, reverse=True)

    def to_json(self):
        return json.dumps({
            'balances': self.balances,
            'nonces': self.nonces,
            'transactions': {k: t.to_json() for k, t in self.transactions.items()},
            'miners': list(self.miners)
        })

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        storage = cls()
        storage.balances = data['balances']
        storage.nonces = data['nonces']
        storage.transactions = {k: Transaction.from_json(t) for k, t in data['transactions'].items()}
        storage.miners = set(data['miners'])
        return storage

    def rollback_block(self, block):
        """Откат блока в хранилище"""
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

    def rollback_transaction(self, transaction: Transaction, address_reward):
        from_address = transaction.fromAddress
        amounts = transaction.all_amounts()
        fee = transaction.fee
        to_address = transaction.toAddress

        if transaction.txhash in self.transactions:
            del self.transactions[transaction.txhash]

        if transaction.tx_type == 'coinbase':
            for i, address in enumerate(to_address):
                self.balances[address] = self.balances.get(address, 0) - transaction.amounts[i]
        else:
            self.balances[from_address] = self.balances.get(from_address, 0) + amounts + fee

            if address_reward in self.balances:
                self.balances[address_reward] = self.balances.get(address_reward, 0) - fee

            for i, address in enumerate(to_address):
                self.balances[address] = self.balances.get(address, 0) - transaction.amounts[i]

        if from_address in self.nonces:
            self.nonces[from_address] -= 1

    def get_transactions_by_address(self, address, transactions_start=0, transactions_end=0):
        filtered_transactions = [tr for tr in self.transactions.values() if
                                 tr.fromAddress == address or address in tr.toAddress]
        return filtered_transactions[transactions_start:transactions_end]
