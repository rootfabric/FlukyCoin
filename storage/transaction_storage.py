from core.transaction import Transaction

class TransactionStorage:
    def __init__(self):
        # Словарь для хранения балансов адресов. Ключ - адрес, значение - баланс.
        self.balances = {}
        # Список для хранения всех транзакций
        self.transactions = []

    def add_transaction(self, transaction: Transaction):
        """
        Добавляет транзакцию и обновляет балансы адресов, если у отправителя достаточно средств.

        :param transaction: словарь с данными транзакции
        """
        from_address = transaction.fromAddress
        amount = transaction.amount
        to_address = transaction.toAddress
        # Проверка наличия средств
        if (transaction.tx_type !="coinbase"
                and self.get_balance(from_address) < amount):
            # print(f"Ошибка: недостаточно средств на адресе {from_address}")
            return False

        # Добавление транзакции в список транзакций
        self.transactions.append(transaction)

        # Вычитание суммы из баланса отправителя
        self.balances[from_address] = self.balances.get(from_address, 0) - amount

        # Добавление суммы к балансу получателя
        self.balances[to_address] = self.balances.get(to_address, 0) + amount
        return True

    def get_balance(self, address):
        """
        Возвращает текущий баланс по указанному адресу.

        :param address: адрес для получения баланса
        :return: баланс адреса
        """
        return self.balances.get(address, 0)

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
        return sorted(self.balances.items(), key=lambda x: x[1]/100000000, reverse=True)

# # Пример использования класса
transaction_storage = TransactionStorage()

import random

class TransactionGenerator:
    def __init__(self, address_count=100, transaction_count=1000):
        self.addresses = [f"Адрес{i}" for i in range(1, address_count + 1)]
        self.transaction_count = transaction_count

    def generate_transactions(self):
        transactions = []
        for _ in range(self.transaction_count):
            from_address = random.choice(self.addresses)
            to_address = random.choice([addr for addr in self.addresses if addr != from_address])
            amount = random.uniform (0, 1)
            # transactions.append({'from': from_address, 'to': to_address, 'amount': amount})
            transactions.append(Transaction(fromAddress=from_address, toAddress=to_address, amount=amount))
        return transactions

    def generate_transactions_from_genesis(self):
        transactions = []
        for _ in range(self.transaction_count):
            from_address = "0"
            to_address = random.choice([addr for addr in self.addresses if addr != from_address])
            amount = 10
            # transactions.append({'from': from_address, 'to': to_address, 'amount': amount})
            transactions.append(Transaction(fromAddress=from_address, toAddress=to_address, amount=amount))
        return transactions
if __name__ == '__main__':
    # Использование генератора транзакций
    generator = TransactionGenerator(address_count=2, transaction_count=100)
    transactions = generator.generate_transactions_from_genesis()
    for transaction in transactions:
        transaction_storage.add_transaction(transaction)


    generator = TransactionGenerator(address_count=2, transaction_count=1000000)
    transactions = generator.generate_transactions()
    for transaction in transactions:
        transaction_storage.add_transaction(transaction)


    # print("Баланс Адрес1:", transaction_storage.get_balance("Адрес1"))
    # print("Баланс Адрес2:", transaction_storage.get_balance("Адрес2"))
    # print("Баланс Адрес3:", transaction_storage.get_balance("Адрес3"))
    print("Все балансы:", transaction_storage.get_all_balances())
    print(transaction_storage.get_addresses_sorted_by_balance())