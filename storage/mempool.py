import json
import os
import pickle
from core.Transactions import Transaction

class Mempool:
    def __init__(self, config, node_manager, filepath='mempool.json'):

        self.node_manager = node_manager
        self.config = config
        self.dir = str(f'{self.config.get("host", "localhost")}:{self.config.get("port", "5555")}')
        self.transactions = {}
        self.filepath = filepath

        self.load_mempool()

    def get_hashes(self):
        return list(self.transactions.keys())

    def check_hash_transaction(self, hash_transaction):
        return True if hash_transaction in self.transactions else False


    def add_transaction(self, transaction):
        """Добавить транзакцию в mempool и сохранить изменения."""
        if transaction.txhash in self.transactions:
            return False

        if self.node_manager.chain.transaction_storage.get_transaction(transaction.txhash) is not None:
            """Транзакция уже есть в проведенных """
            return False


        self.transactions[transaction.txhash] = transaction
        # self.save_transactions()
        return True


    def save_mempool(self, dir="", filename='mempool.db'):
        # Нормализация имени директории и формирование пути


        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Создание пути, если необходимо
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        # Сохранение данных


        # Сохранение данных
        with open(full_path, 'wb') as file:
            pickle.dump([t.to_json() for t in self.transactions.values()], file)

        # print(f"Blockchain saved to disk at {full_path}.")

    def load_mempool(self, dir="", filename='mempool.db'):
        # Нормализация имени директории и формирование пути
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        try:
            with open(full_path, 'rb') as file:
                for t in pickle.load(file):
                    transaction = Transaction.from_json(t)
                    self.transactions[transaction.txhash] = transaction
            print(f"Mempool loaded from disk. Count {len(self.transactions)}")
        except FileNotFoundError:
            print("No Mempool file found.")
        except Exception as e:
            print(f"Failed to load Mempool: {e}")

    def get_transactions(self):
        """Вернуть список всех транзакций в mempool."""
        return self.transactions

    def get_transaction(self, hash):
        """Вернуть список всех транзакций в mempool."""
        return self.transactions.get(hash)

    def size(self):
        return len(self.transactions)

    def remove_transaction(self, tx_hash):
        if tx_hash in self.transactions:
            del self.transactions[tx_hash]

    def remove_transactions_in_block(self, block):
        """ Убираем из мемпула транзакции """
        for tx in block.transactions:
            self.remove_transaction(tx.txhash)

if __name__ == '__main__':
    # Пример использования класса Mempool
    mempool = Mempool()

    t = Transaction("coinbase", "1", "2", "100")
    t.make_hash()
    # print(t.get_data_hash().hexdigest())
    print(t.txhash)
    mempool.add_transaction(t)

    # Получение всех транзакций
    print(mempool.get_transactions())
