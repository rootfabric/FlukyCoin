import json
import os
import pickle
from core.Transactions import Transaction

class Mempool:
    def __init__(self, dir="", filepath='mempool.json'):
        self.dir = dir
        self.transactions = {}
        self.filepath = filepath
        # self.load_transactions()

    def get_hashes(self):
        return list(self.transactions.keys())

    def chech_hash_transaction(self, hash_transaction):
        return True if hash_transaction in self.transactions else False


    def add_transaction(self, transaction):
        """Добавить транзакцию в mempool и сохранить изменения."""
        if transaction.hash in self.transactions:
            return False

        self.transactions[transaction.hash] = transaction
        # self.save_transactions()
        return True


    def save_transactions(self, dir="", filename='mempool.db'):
        # Нормализация имени директории и формирование пути
        base_dir = self.dir.replace(":", "_")

        dir_path = os.path.join(base_dir, dir)

        # Создание пути, если необходимо
        # if not os.path.exists(dir_path):
        #     os.makedirs(dir_path)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        # Сохранение данных
        with open(full_path, 'wb') as file:
            pickle.dump(self.transactions, file)

        # print(f"Blockchain saved to disk at {full_path}.")

    def load_transactions(self, dir="", filename='mempool.db'):
        # Нормализация имени директории и формирование пути
        dir_path = self.dir.replace(":", "_")
        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        try:
            with open(full_path, 'rb') as file:
                self.transactions = pickle.load(file)
            print(f"Mempool loaded from disk. Count {len(self.transactions)}")
        except FileNotFoundError:
            print("No Mempool file found.")
        except Exception as e:
            print(f"Failed to load Mempool: {e}")

    def get_transactions(self):
        """Вернуть список всех транзакций в mempool."""
        return self.transactions

    def size(self):
        return len(self.transactions)
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
