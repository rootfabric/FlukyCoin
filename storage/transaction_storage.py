from core.Transactions import Transaction

import json


class TransactionStorage:
    def __init__(self):
        # Словарь для хранения балансов адресов. Ключ - адрес, значение - баланс.
        self.balances = {}

        # Словарь для хранения nonce адресов. Ключ - адрес, значение - nonce.
        self.nonces = {}

        # Список для хранения всех транзакций
        self.transactions = []

        # список манйнеров
        self.miners = set()

    def clear(self):
        self.balances.clear()
        self.nonces.clear()
        self.transactions.clear()
        self.miners.clear()

    def add_block(self, block):
        """  добавляем все данные по блоку в хранилище"""
        # for new_node in block.new_nodes:
        #     self.nodes_rating[new_node] = 0


        # для зачисления коммисии нужен адрес
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
        self.add_nonses_to_address(block.signer)





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
        if transaction.tx_type != "coinbase" and self.get_balance(from_address) < amounts:
            return False

        # Добавление транзакции в список транзакций
        self.transactions.append(transaction)

        # Обновление баланса отправителя и получателя
        self.balances[from_address] = self.balances.get(from_address, 0) - amounts - fee

        # награда на адрес который указал майнер для получения
        self.balances[address_reward] = self.balances.get(address_reward, 0) + fee

        for i, address in enumerate(to_address):
            self.balances[address] = self.balances.get(address, 0) + transaction.amounts[i]

        # Обновление nonce для адреса отправителя
        self.add_nonses_to_address(from_address)

        return True

    def add_nonses_to_address(self, address):
        # Обновление nonce для адреса отправителя
        if address in self.nonces:
            self.nonces[address] += 1
        else:
            self.nonces[address] = 1

    def pop_nonses_to_address(self, address):
        # Обновление nonce для адреса отправителя
        if address in self.nonces:
            self.nonces[address] -= 1

    def get_balance(self, address):
        """
        Возвращает текущий баланс по указанному адресу.

        :param address: адрес для получения баланса
        :return: баланс адреса
        """
        return self.balances.get(address, 0)

    def get_nonce(self, address):
        """
        Возвращает текущий nonce по указанному адресу. Возвращает None, если адрес не найден.

        :param address: адрес для получения nonce
        :return: nonce адреса или None, если адрес не найден
        """
        return self.nonces.get(address, 0)

    def get_all_balances(self):
        """
        Возвращает балансы всех адресов.

        :return: словарь балансов
        """
        return self.balances

    def get_addresses_sorted_by_balance(self):
        """
        Возвращает список адресов, отсортированный по размеру средств на балансе в порядке убывания.

        :return: список адресов
        """
        return sorted(self.balances.items(), key=lambda x: x[1] / 100000000, reverse=True)

    def to_json(self):
        """
        Сериализует объект TransactionStorage в JSON-строку.
        """
        return json.dumps({
            'balances': self.balances,
            'nonces': self.nonces,
            'transactions': [t.to_json() for t in self.transactions],
            'miners': list(self.miners)
        })

    @classmethod
    def from_json(cls, json_str):
        """
        Десериализует объект TransactionStorage из JSON-строки.
        """
        data = json.loads(json_str)
        storage = cls()
        storage.balances = data['balances']
        storage.nonces = data['nonces']
        storage.transactions = [Transaction.from_json(t) for t in data['transactions']]
        storage.miners = set(data['miners'])
        return storage

    def rollback_block(self, block):
        """ Откат блока в хранилище """
        # Перебираем все транзакции в блоке, начиная с конца, чтобы сначала откатить обычные транзакции, затем coinbase
        for transaction in reversed(block.transactions):
            self.rollback_transaction(transaction)

        # Добавляем майнера
        if block.signer in self.miners:
            self.miners.remove(block.signer)

        # Учитываем подпись ключа блока
        self.pop_nonses_to_address(block.signer)


    def rollback_transaction(self, transaction: Transaction):
        from_address = transaction.fromAddress
        amounts = transaction.all_amounts()
        fee = transaction.fee
        to_address = transaction.toAddress

        # Удаление транзакции из списка транзакций
        if transaction in self.transactions:
            self.transactions.remove(transaction)

        # Если это coinbase-транзакция, просто удаляем ее из списка и откатываем соответствующие изменения
        if transaction.tx_type == 'coinbase':
            # Уменьшаем баланс получателя на сумму coinbase
            for i, address in enumerate(to_address):
                self.balances[address] = self.balances.get(address, 0) - transaction.amounts[i]
        else:
            # Обычная транзакция: возвращаем средства отправителю и уменьшаем у получателей
            self.balances[from_address] = self.balances.get(from_address, 0) + amounts + fee

            # Возврат комиссии майнеру (убираем из баланса адреса награды)
            if transaction.reward_address in self.balances:
                self.balances[transaction.reward_address] = self.balances.get(transaction.reward_address, 0) - fee

            # Вычитание средств у получателей
            for i, address in enumerate(to_address):
                self.balances[address] = self.balances.get(address, 0) - transaction.amounts[i]

        # Откат nonce для адреса отправителя
        if from_address in self.nonces:
            self.nonces[from_address] -= 1

    def get_transactions_by_address(self, address):
        # Возвращаем транзакции, где address является отправителем или получателем
        return [tr for tr in self.transactions if tr.fromAddress == address or address in tr.toAddress]