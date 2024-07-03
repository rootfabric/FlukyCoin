import datetime
import os
import pickle
from crypto.xmss import XMSS, keypair_from_json, keypair_to_json, XMSSPublicKey
from tools.logger import Log
from core.protocol import Protocol


class MinerStorage:
    def __init__(self, config, start_generate = True):
        """ """
        self.config = config
        self.dir = str(f'{self.config.get("host", "localhost")}:{self.config.get("port", "5555")}')
        self.log = Log()
        self.keys: {str: XMSS} = {}
        self.old_keys: {str: XMSS} = {}

        self.load_from_disk(dir=self.dir)

        if len(self.keys) == 0 and start_generate:

            # по дефолту если нет значения в конфиге, берем небольшие значения
            miners_storage_size = self.config.get('miners_storage_size', 10)
            miners_storage_height = self.config.get('miners_storage_height', Protocol.MAX_HEIGHT_SIGN_KEY)

            self.generate_keys(miners_storage_size, height=miners_storage_height)
            self.save_storage_to_disk(dir=self.dir)

    def generate_keys(self, size=10, height=Protocol.MAX_HEIGHT_SIGN_KEY):
        """ Генерация заданного количества ключей для майнинга"""
        self.log.info("Генерация ключей")
        start_time = datetime.datetime.now()
        count_sign = 0
        # ограничение на высоту ключа
        height = min(height, Protocol.MAX_HEIGHT_SIGN_KEY)
        for i in range(size):
            xmss = XMSS.create(height)
            count_sign += xmss.keyPair.PK.max_height()
            self.keys[xmss.address] = xmss
            self.log.info(f"[{i + 1}/{size}]  {xmss.address} signs:{xmss.keyPair.PK.max_height()}")

        self.log.info(f"Ключей создано: {size}, подписей:  {count_sign}  время{datetime.datetime.now()-start_time}")
        self.save_storage_to_disk(dir=self.dir)

    def close_key(self, key: XMSS):
        """ Переносим в израсходованные """
        key = self.keys.pop(key)
        self.old_keys[key.address] = key

    def save_storage_to_disk(self, dir="", filename='miners_storage.db'):
        # Нормализация имени директории и формирование пути
        dir = self.dir if self.dir != "" else dir
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
            pickle.dump((
                [key.to_json() for key in self.keys.values()],
                [key2.to_json() for key2 in self.old_keys.values()]
            ), file)

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
                keys_json , old_keys_json= pickle.load(file)
                for key_json in keys_json:
                    xmss = XMSS.from_json(key_json)
                    count_sign += xmss.keyPair.PK.max_height()
                    self.keys[xmss.address] = xmss

                for key_json in old_keys_json:
                    xmss = XMSS.from_json(key_json)
                    count_sign += xmss.keyPair.PK.max_height()
                    self.old_keys[xmss.address] = xmss

            self.log.info(f"Miner storage loaded from disk. {len(self.keys)} signs:{count_sign}")

        except FileNotFoundError:
            self.log.error("No Miner storage file found.")
        except Exception as e:
            self.log.error(f"Failed to load Miner storage: {e}")


if __name__ == '__main__':
    """ """
    mining_storage = MinerStorage({}, start_generate=False)

    mining_storage.generate_keys(1, 14)
    mining_storage.save_storage_to_disk()

    # mining_storage.load_from_disk()

    # for k in mining_storage.keys.keys():
    #     print(k, XMSSPublicKey().is_valid_address(k))
    # print(mining_storage.keys)
    # mining_storage.generate_keys(size=20, height=7)
    # mining_storage.save_storage_to_disk()
