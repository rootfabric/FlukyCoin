import datetime

from core.Block import Block
import base64
# from crypto.xmss import *
# # Пример использования класса
from storage.transaction_storage import TransactionStorage
from core.protocol import Protocol
from core.transaction import Transaction
from storage.mempool import Mempool
import copy
import time
from tools.time_sync import NTPTimeSynchronizer
import os
import pickle
from tools.logger import Log


class Chain():
    def __init__(self, config=None, time_ntpt=None, mempool=None, log=Log()):
        self.blocks: Block = []
        self.transaction_storage = TransactionStorage()
        self.mempool: Mempool = mempool
        self.protocol = Protocol()
        self.log = log

        self.block_candidate: Block = None

        self.time_ntpt = NTPTimeSynchronizer(log=self.log) if time_ntpt is None else time_ntpt

        self.miners = set()

        if config is not None:
            host = config.get("host", "localhost")
            port = config.get("port", "5555")
            dir = f"{host}_{port}"
            self.load_from_disk(dir=dir)

        self.history_hash = {}

        self._previousHash = Protocol.prev_hash_genesis_block.hex()

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

    def save_chain_to_disk(self, dir="", filename='blockchain.db'):
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

            # pickle.dump([[b.to_json() for b in self.blocks], self.transaction_storage, None if self.block_candidate is None else self.block_candidate.to_json()], file)
            pickle.dump([[b.to_json() for b in self.blocks], self.transaction_storage.to_json(), None if self.block_candidate is None else self.block_candidate.to_json()], file)


            # pickle.dump([[b.to_json() for b in self.blocks],  None if self.block_candidate is None else self.block_candidate.to_json()], file)


        # print(f"Blockchain saved to disk at {full_path}.")

    def load_from_disk(self, dir="", filename='blockchain.db'):
        # Нормализация имени директории и формирование пути
        dir = dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        try:
            with open(full_path, 'rb') as file:
                blocks_json, transaction_storage_json, block_candidate_json = pickle.load(file)
                if block_candidate_json is not None:
                    self.block_candidate.from_json(block_candidate_json)

                self.transaction_storage = TransactionStorage.from_json(transaction_storage_json)

                self.blocks = [Block.from_json(j) for j in blocks_json]

            for block in self.blocks:
                self.miners.add(block.signer)

            self.log.info(f"Blockchain loaded from disk. {self.blocks_count()} miners: {len(self.miners)}")
        except FileNotFoundError:
            self.log.error("No blockchain file found.")
        except Exception as e:
            self.log.error(f"Failed to load blockchain: {e}")

    def validate_block_hash(self, block: Block):
        if block.previousHash != self.last_block_hash():
            self.log.warning("validateblock.previousHash != self.last_block_hash()")
            return False
        return True

    def validate_block_time(self, block: Block):
        if self.last_block() is None:
            return True

        if block.timestamp_seconds <= self.last_block().timestamp_seconds:
            self.log.warning("Блок не проходит валидацию по времени")
            return False
        return True

    def validate_block_number(self, block: Block):

        if block.block_number != self.blocks_count():
            self.log.warning("Блок не проходит валидацию по номеру")
            return False
        return True

    def next_address_nonce(self, address):
        """ сколько раз использовался адрес в цепи """
        return self.transaction_storage.get_nonce(address) + 1

    def address_ballance(self, address):
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

            if self.address_ballance(transaction.fromAddress) < transaction.all_amounts() + transaction.fee:
                self.log.warning(
                    f"Транзакция не валидна. Остаток: {self.address_ballance(transaction.fromAddress)} < amounts:{transaction.all_amounts()} + fee {transaction.fee}")
                return False

        return True

    def validate_block(self, block):
        """ Проверка блока в цепи """

        if not block.validate():
            return False

        if not self.validate_block_hash(block):
            return False

        if not self.validate_block_time(block):
            return False

        if not self.validate_block_number(block):
            return False

        count_coinbase = 0
        for transaction in block.transactions:
            if transaction.tx_type=="coinbase":
                count_coinbase+=1
            if not self.validate_transaction(transaction):
                self.log.warning(f"Транзакция {transaction.txhash} не валидна")
                return False

        if count_coinbase!=1:
            self.log.warning(f"Неверно количество coinbase транзакций: {count_coinbase} шт")
            return False

        return True

    def validate_and_add_block(self, block):

        if block is None:
            self.log.warning("validate block is None")
            return False

        if not self.validate_block(block):
            return False

        self.add_block(block)
        return True

    def add_block(self, block:Block):
        """  """
        self.blocks.append(block)

        # for new_node in block.new_nodes:
        #     self.nodes_rating[new_node] = 0
        address_reward = None
        for transaction in block.transactions:
            if transaction.tx_type == "coinbase":
                address_reward = transaction.toAddress[0]
                break




        for transaction in block.transactions:
            self.transaction_storage.add_transaction(transaction, address_reward)

            # # при любом вознаграждении повышаем рейтинг
            # if transaction.fromAddress == '0000000000000000000000000000000000':
            #     self.nodes_rating[transaction.toAddress] = self.nodes_rating.get(transaction.toAddress, 0)+1

        self.miners.add(block.signer)

        self.history_hash[block.hash_block()] = block
        # self.save_to_disk()

    def blocks_count(self):
        return len(self.blocks)

    def get_nodes(self):
        # for block in self.blocks:
        #     for new_node in block.new_nodes:
        #         self.nodes_rating[new_node] = 0

        return self.nodes_rating

    def last_block_hash(self) -> Block:
        return self.blocks[-1].hash_block() if len(
            self.blocks) > 0 else Protocol.prev_hash_genesis_block.hex()

    def last_block(self) -> Block:

        return self.blocks[-1] if len(self.blocks) > 0 else None

    # def select_winer_block(self, block1: Block, block2: Block):
    #     """ при разных блоках надо выбрать правильный"""
    #
    #     if block1.previousHash != block2.previousHash:
    #         print(" Блоки разного уровня. сравнение не корректно")
    #         raise
    #
    #     # signer = base64.b64decode(block1.signer)
    #     # PK = XMSSPublicKey.from_bytes(signer)
    #     # print(PK.generate_address())
    #
    #     merge_block = Block(block1.previousHash)
    #
    #     for new_node, parrent in block1.new_nodes.items():
    #         merge_block.add_new_node(new_node, parrent)
    #
    #     for new_node, parrent in block2.new_nodes.items():
    #         merge_block.add_new_node(new_node, parrent)
    #
    #     winner = merge_block.find_winner_in_new_nodes()
    #
    #     print(winner)
    #
    #     if XMSSPublicKey.from_bytes(base64.b64decode(block1.signer)).generate_address() == winner['address']:
    #         return block1
    #     if XMSSPublicKey.from_bytes(base64.b64decode(block2.signer)).generate_address() == winner['address']:
    #         return block2
    def check_miners(self, addr):
        return addr in self.miners

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

        is_key_block = self.protocol.is_key_block(self._previousHash)
        # print(f"Key block: {is_key_block}")

        # при ключевом блоке проверяем, не является ли адрем новым
        if not is_key_block:

            if self.check_miners(self.block_candidate.signer) and not self.check_miners(block.signer):
                """ кандидат не в списках майнеров """
                # print(f"Текущий майнер {self.block_candidate.signer}, кандидат не в списках майнеров", block.signer, self.miners)
                return False

            if not self.check_miners(self.block_candidate.signer) and self.check_miners(block.signer):
                """ кандидат в списках майнеров, а текущий нет """
                # print(f"Кандидат майнер {self.block_candidate.signer}, пербивает кандидата", block.signer, self.miners)
                # self.block_candidate = copy.deepcopy(block)
                self.block_candidate = Block.from_json(block.to_json())
                # print("New candidat", self.block_candidate.hash, self.block_candidate.signer)
                self.log.info("New candidate", self.block_candidate.hash, self.block_candidate.signer)
                return True

        win_address = self.protocol.winner(self.block_candidate.signer, block.signer,
                                           self.protocol.sequence(self._previousHash))
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

        is_key_block = self.protocol.is_key_block(self._previousHash)
        # print(f"Key block: {is_key_block}")

        # при ключевом блоке проверяем, не является ли адрем новым
        if not is_key_block:

            if self.check_miners(candidate_signer) and not self.check_miners(address_candidate):
                """ кандидат не в списках майнеров """
                # print(f"Текущий майнер {self.block_candidate.signer}, кандидат не в списках майнеров", block.signer, self.miners)
                return False

            if not self.check_miners(candidate_signer) and self.check_miners(address_candidate):
                """ кандидат в списках майнеров, а текущий нет """
                return True

        win_address = self.protocol.winner(candidate_signer, address_candidate,
                                           self.protocol.sequence(self._previousHash))

        if win_address == candidate_signer:
            return False

        return True

    def close_block(self):
        """ Берем блок кандидата как верный """

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

        if self.block_candidate.timestamp_seconds > self.time_ntpt.get_corrected_time():
            return False

        return True
        # last_block = self.last_block()
        #
        # if last_block is None:
        #     print("Блоков нет")
        #     return True
        #
        # delta = time.time() - last_block.time
        # print(f"{datetime.datetime.now()} delta", delta, last_block.hash)
        #
        # if delta > 60:
        #     return True
        #
        # return False


if __name__ == '__main__':
    """ """
