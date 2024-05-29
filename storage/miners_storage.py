import os
import pickle
from crypto.xmss import XMSS, keypair_from_json, keypair_to_json, XMSSPublicKey
from tools.logger import Log


class MinerStorage:
    def __init__(self, dir=""):
        """ """
        self.dir = dir
        self.log = Log()
        self.keys: {str: XMSS} = {}

        self.load_from_disk(dir=dir)

        if len(self.keys) == 0:
            self.generate_keys(2, height=2)
            self.save_storage_to_disk(dir=dir)

    def generate_keys(self, size=10, height=5):
        """ Генерация заданного количества ключей для майнинга"""
        self.log.info("Генерация ключей")
        count_sign = 0
        for i in range(size):
            xmss = XMSS.create(height)
            count_sign += xmss.keyPair.PK.max_height()
            self.keys[xmss.address] = xmss
            self.log.info(f"[{i + 1}/{size}]  {xmss.address} signs:{xmss.keyPair.PK.max_height()}")

        self.log.info(f"Ключей создано: {size}, подписей:  {count_sign}")

    def save_storage_to_disk(self, dir="", filename='miners_storage.db'):
        # Нормализация имени директории и формирование пути
        dir = dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Создание пути, если необходимо
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        # Сохранение данных
        with open(full_path, 'wb') as file:
            pickle.dump([key.to_json() for key in self.keys.values()], file)

        # print(f"Blockchain saved to disk at {full_path}.")

    def load_from_disk(self, dir="", filename='miners_storage.db'):
        # Нормализация имени директории и формирование пути
        dir = dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        try:
            count_sign = 0
            with open(full_path, 'rb') as file:
                keys_json = pickle.load(file)
                for key_json in keys_json:
                    xmss = XMSS.from_json(key_json)
                    count_sign += xmss.keyPair.PK.max_height()
                    self.keys[xmss.address] = xmss

            self.log.info(f"Miner storage loaded from disk. {len(self.keys)} signs:{count_sign}")

        except FileNotFoundError:
            self.log.error("No Miner storage file found.")
        except Exception as e:
            self.log.error(f"Failed to load Miner storage: {e}")


if __name__ == '__main__':
    """ """
    mining_storage = MinerStorage()

    # mining_storage.generate_keys(100)
    # mining_storage.save_storage_to_disk()

    # mining_storage.load_from_disk()

    for k in mining_storage.keys.keys():
        print(k, XMSSPublicKey().is_valid_address(k))
    # print(mining_storage.keys)
    # mining_storage.generate_keys(size=20, height=7)
    # mining_storage.save_storage_to_disk()
