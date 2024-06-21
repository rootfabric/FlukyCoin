import datetime

from core.Block import Block
import base64
# from crypto.xmss import *
# # Пример использования класса
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
import dbm


class Chain():
    def __init__(self, config=None, time_ntpt=None, mempool=None, log=Log(), node_dir_base = None):

        self.config = config if config is not None else {}
        if node_dir_base is None:
            self.dir = str(f'{self.config.get("host", "localhost")}:{self.config.get("port", "5555")}')
        else:
            self.dir = node_dir_base

        self.transaction_storage = TransactionStorage(dir=self.dir)
        self.mempool: Mempool = mempool
        self.protocol = Protocol()
        self.log = log
        self.difficulty = 0

        self.block_candidate: Block = None

        self.time_ntpt = NTPTimeSynchronizer(log=self.log) if time_ntpt is None else time_ntpt

        self.history_hash = {}

        self._previousHash = Protocol.prev_hash_genesis_block.hex()

    def clear_db(self):
        with self._open_db() as db:
            db.clear()

    def _open_db(self, mode='c'):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        db_path = os.path.join(dir_path, 'blocks.db')

        if mode == 'r':
            # Если пытаемся открыть для чтения, но файл не существует
            if not os.path.exists(db_path):
                # Создаем пустую базу данных
                with dbm.open(db_path, 'c'):
                    pass
                # И сразу же открываем ее для чтения
                return dbm.open(db_path, 'r')

        try:
            return dbm.open(db_path, mode)
        except dbm.error as e:
            if 'db file doesn\'t exist' in str(e):
                # Если файл не существует, создаем его
                return dbm.open(db_path, 'c')
            else:
                # Если возникла другая ошибка, пробрасываем ее дальше
                raise

    def block_by_number_from_chain(self, num):
        with self._open_db('r') as db:
            if str(num) in db:
                return Block.from_json(db[str(num)].decode())
        return None

    def blocks_count(self):
        with self._open_db('r') as db:
            return len(db)

    def last_block(self):
        count = self.blocks_count()
        return self.block_by_number_from_chain(count - 1) if count > 0 else None

    def last_block_hash(self):
        last_block = self.last_block()
        return last_block.hash_block() if last_block else Protocol.prev_hash_genesis_block.hex()

    def last_block_time(self):
        last_block = self.last_block()
        return last_block.timestamp_seconds if last_block else 0

    def save_chain_to_disk(self, filename='blockchain.db'):

        return
        # Сохранение данных транзакций
        self.transaction_storage.save_to_disk(self.dir)

        # Сохранение блок-кандидата
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        full_path = os.path.join(dir_path, 'block_candidate.pickle')
        with open(full_path, 'wb') as file:
            pickle.dump(None if self.block_candidate is None else self.block_candidate.to_json(), file)

    def calculate_difficulty(self):
        self.difficulty = 0
        with self._open_db('r') as db:
            for key in db.keys():
                block = Block.from_json(db[key].decode())
                self.difficulty += self.block_difficulty(block)

    def load_from_disk(self, filename='blockchain.db'):
        # Загрузка данных транзакций
        # self.transaction_storage.load_from_disk(self.dir)

        # Загрузка блок-кандидата
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

    def _open_db(self, mode='c'):
        dir = self.dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        db_path = os.path.join(dir_path, 'blocks.db')

        if mode == 'r' and not os.path.exists(db_path):
            # Если файл не существует и мы пытаемся открыть его для чтения,
            # создадим пустую базу данных
            with dbm.open(db_path, 'c'):
                pass

        return dbm.open(db_path, mode)

    def _add_block(self, block: Block):
        with self._open_db('c') as db:
            db[str(block.block_number)] = block.to_json().encode()

        self.transaction_storage.add_block(block)
        self.difficulty += self.block_difficulty(block)
        self.add_history_hash(block)
        if self.mempool is not None:
            self.mempool.remove_transactions_in_block(block)

    def drop_last_block(self):
        last_block = self.last_block()
        if last_block is None:
            return False

        self.transaction_storage.rollback_block(last_block)

        with self._open_db('c') as db:
            del db[str(last_block.block_number)]

        if last_block.hash_block() in self.history_hash:
            self.history_hash.pop(last_block.hash_block())

        self.difficulty -= self.block_difficulty(last_block)
        return True

    def time(self):
        return self.time_ntpt.get_corrected_time()

    @property
    def block_candidate_hash(self):
        return self.block_candidate.hash_block() if self.block_candidate is not None else None

    def reset_block_candidat(self):
        self.block_candidate = None

    def check_hash(self, block_hash):
        """"""
        # TODO нужно смотреть блоки в цепи

        # Все хеши блоков храним, чтобы потом не брать уже полученный
        if block_hash in self.history_hash:
            return self.history_hash[block_hash]
        #
        #
        # if self.block_candidate is not None and block_hash ==self.block_candidate.hash_block():
        #     return True
        return None

    def add_history_hash(self, block):
        self.history_hash[block.hash_block()] = block

    def block_difficulty(self, block: Block):
        """ Сложность блока """

        ratio, _ = Protocol.find_longest_common_substring(block.signer, block.previousHash, convert_to_sha256=True)

        address_height = Protocol.address_height(block.signer)

        return ratio * address_height

    def validate_block_hash(self, block: Block):
        if block.previousHash != self.last_block_hash():
            # self.log.warning("validateblock.previousHash != self.last_block_hash()")
            return False
        return True

    def validate_block_time(self, block: Block):
        if self.last_block() is None:
            return True

        if block.timestamp_seconds <= self.last_block().timestamp_seconds:
            self.log.warning("Блок не проходит валидацию по времени")
            return False

        # # если время последнего блока еще не вышло
        # last_block = self.last_block()
        # if last_block is not None:
        #     if last_block.timestamp_seconds + Protocol.BLOCK_TIME_INTERVAL > self.time_ntpt.get_corrected_time():
        #         # self.log.warning("Блок не проходит валидацию по времени. Сильно мало с последнего блока")
        #         return False

        return True

    def validate_block_number(self, block: Block):

        if block.block_number != self.blocks_count():
            self.log.warning("Блок не проходит валидацию по номеру")
            return False
        return True

    def next_address_nonce(self, address):
        """ сколько раз использовался адрес в цепи """
        return self.transaction_storage.get_nonce(address) + 1

    def address_balance(self, address):
        """ Баланс адреса """
        return self.transaction_storage.get_balance(address)

    def validate_transaction(self, transaction: Transaction):
        """ Проверка транзакции """

        """ Проверка  nonce"""
        address_nonce = self.next_address_nonce(transaction.fromAddress)
        if transaction.nonce != address_nonce:
            self.log.warning(
                f"Транзакция не валидна. nonce цепи: {address_nonce} nonce транзакции:{transaction.nonce}")
            return False

        # coinbase не подписывается
        if transaction.tx_type != "coinbase" and not transaction.validate_sign():
            self.log.warning(f"Транзакция не валидна no подписи")
            return False

        """ Проверка на максимальные подписи"""
        if transaction.tx_type != "coinbase":
            if transaction.PK.max_height() <= address_nonce:
                self.log.warning(f"Транзакция не валидна: превышен порог подписей")
                return False

        """ Проверка  баланса"""
        if transaction.tx_type == "transfer":

            if self.address_balance(transaction.fromAddress) < transaction.all_amounts() + transaction.fee:
                self.log.warning(
                    f"Транзакция не валидна. Остаток: {self.address_balance(transaction.fromAddress)} < amounts:{transaction.all_amounts()} + fee {transaction.fee}")
                return False

        return True

    def validate_nonce_key(self, block: Block):

        PK = block.XMSSPublicKey()
        address = PK.generate_address()

        n = self.next_address_nonce(address)

        if PK.max_height() < self.next_address_nonce(address):
            self.log.warning(
                f"PK.max_height() {PK.max_height()} self.next_address_nonce(PK.generate_address()) {self.next_address_nonce(address)}")
            self.log.warning("Количество подписей больше высоты")
            return False
        return True

    def validate_rewards(self, block: Block):
        """ Проверка вознаграждения за блок """
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

        # sec = Protocol.sequence(block.previousHash)
        block_reward = Protocol.reward(block_number=block_num)
        amount = coinbase_transaction.all_amounts()

        if amount != block_reward:
            self.log.warning(f"Неверное вознаграждение блока {block_reward} нужно: {amount}")
            return False

        return True

    def validate_block(self, block):
        """ Проверка блока в цепи """

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

                # Сразу удаляем из мем пула если не валидна
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

    def get_nodes(self):
        # for block in self.blocks:
        #     for new_node in block.new_nodes:
        #         self.nodes_rating[new_node] = 0

        return self.nodes_rating

    def check_miners(self, addr):
        return addr in self.transaction_storage.miners

    def validate_candidate(self, block: Block):
        """ Является ли блок кандидатом """

        if self.last_block() is None:
            return True

        if block.previousHash != self.last_block().hash_block():
            # print("Chain: ошибка проверки кандидата, хеш не подходит")
            return False

        if block.timestamp_seconds < self.last_block().timestamp_seconds:
            # print("Chain: ошибка проверки кандидата, время меньше предыдущего блока")
            return False

        return True

    def add_block_candidate(self, block: Block):
        """  В цепи лежит блок, который является доминирующим"""

        if block is None:
            return False

        if not self.validate_candidate(block):
            return False

        if not self.validate_block(block):
            return False

        # первый блок
        if self.last_block() is None and self.block_candidate is None:
            # self.block_candidate = copy.deepcopy(block)
            self.block_candidate = Block.from_json(block.to_json())
            self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
            return True

        # print("Исходный block:", block)
        if self.block_candidate is None:
            # self.block_candidate = copy.deepcopy(block)
            self.block_candidate = Block.from_json(block.to_json())
            self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
            return True

        if block.hash_block() == self.block_candidate.hash_block():
            return False

        # валидация в цепи.
        if not self.validate_candidate(block):
            return False

        self._previousHash = Protocol.prev_hash_genesis_block.hex() if self.last_block() is None else self.last_block().hash

        # is_key_block = self.protocol.is_key_block(self._previousHash)
        # # print(f"Key block: {is_key_block}")
        #
        # # при ключевом блоке проверяем, не является ли адрем новым
        # if not is_key_block:
        #
        #     if self.check_miners(self.block_candidate.signer) and not self.check_miners(block.signer):
        #         """ кандидат не в списках майнеров """
        #         # print(f"Текущий майнер {self.block_candidate.signer}, кандидат не в списках майнеров", block.signer, self.miners)
        #         return False
        #
        #     if not self.check_miners(self.block_candidate.signer) and self.check_miners(block.signer):
        #         """ кандидат в списках майнеров, а текущий нет """
        #         # print(f"Кандидат майнер {self.block_candidate.signer}, пербивает кандидата", block.signer, self.miners)
        #         # self.block_candidate = copy.deepcopy(block)
        #         self.block_candidate = Block.from_json(block.to_json())
        #         # print("New candidat", self.block_candidate.hash, self.block_candidate.signer)
        #         self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
        #         return True

        win_address = self.protocol.winner([self.block_candidate.signer, block.signer], self._previousHash)
        # print("---------------------------------------------", self.protocol.sequence(self.previousHash))
        # print(self.block_candidate.signer)
        # print(block.signer)
        # print("win_address", win_address)
        if win_address == self.block_candidate.signer:
            return False
        # новый победитель
        # self.block_candidate = copy.deepcopy(block)
        self.block_candidate = Block.from_json(block.to_json())
        self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)

        return True

    def try_address_candidate(self, address_candidate, candidate_signer):
        """  В цепи лежит блок, который является доминирующим"""

        # первый блок
        # if self.last_block() is None and self.block_candidate is None:
        #     return True
        #
        # # print("Исходный block:", block)
        # if self.block_candidate is None:
        #
        #     return True

        if address_candidate == candidate_signer:
            return False

        # валидация в цепи.

        self._previousHash = Protocol.prev_hash_genesis_block.hex() if self.last_block() is None else self.last_block().hash

        # is_key_block = self.protocol.is_key_block(self._previousHash)
        # # print(f"Key block: {is_key_block}")
        #
        # # при ключевом блоке проверяем, не является ли адрем новым
        # if not is_key_block:
        #
        #     if self.check_miners(candidate_signer) and not self.check_miners(address_candidate):
        #         """ кандидат не в списках майнеров """
        #         # print(f"Текущий майнер {self.block_candidate.signer}, кандидат не в списках майнеров", block.signer, self.miners)
        #         return False
        #
        #     if not self.check_miners(candidate_signer) and self.check_miners(address_candidate):
        #         """ кандидат в списках майнеров, а текущий нет """
        #         return True

        win_address = self.protocol.winner([candidate_signer, address_candidate], self._previousHash)

        if win_address == candidate_signer:
            return False

        return True

    def close_block(self):
        """ Берем блок кандидата как верный """
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
        """ Если со времни появления последнего блока прошло более минуты, можно закреплять блок """

        if self.block_candidate is None:
            return False
        # print(f"Check: {self.blocks_count()} txs[{self.mempool.size()}] delta: {self.block_candidate.time -self.time_ntpt.get_corrected_time():0.2f}  {self.block_candidate.hash_block()[:5]}...{self.block_candidate.hash_block()[-5:]}  singer: ...{self.block_candidate.signer [-5:]}")

        # если время последнего блока еще не вышло
        last_block = self.last_block()
        if last_block is not None:
            if last_block.timestamp_seconds + Protocol.BLOCK_TIME_SECONDS > self.time():
                return False

        if self.block_candidate.timestamp_seconds > self.time():
            return False

        return True


if __name__ == '__main__':
    """ """
