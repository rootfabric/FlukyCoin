import datetime

from core.block import Block
import base64
# from crypto.xmss import *
# # Пример использования класса
from storage.transaction_storage import TransactionStorage
from core.protocol import Protocol
import copy
import time
from tools.time_sync import NTPTimeSynchronizer
import os
import pickle
class Chain():
    def __init__(self, time_ntpt = None):
        self.blocks: Block = []
        self.transaction_storage = TransactionStorage()

        self.protocol = Protocol()

        self.block_candidate: Block = None

        self.time_ntpt = NTPTimeSynchronizer() if time_ntpt is None else time_ntpt

    def time(self):
        return self.time_ntpt.get_corrected_time()

    @property
    def block_candidate_hash(self):
        return self.block_candidate.hash_block() if self.block_candidate is not None else None

    def check_hach(self, block_hash):
        """"""
        # TODO нужно смотреть блоки в цепи
        if self.block_candidate is not None and block_hash ==self.block_candidate.hash_block():
            return True
        return False
    def save_to_disk(self, dir="", filename='blockchain.db'):
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
            pickle.dump([self.blocks, self.transaction_storage, self.block_candidate], file)

        print(f"Blockchain saved to disk at {full_path}.")

    def load_from_disk(self, dir="", filename='blockchain.db'):
        # Нормализация имени директории и формирование пути
        dir = dir.replace(":", "_")
        base_dir = "node_data"
        dir_path = os.path.join(base_dir, dir)

        # Полный путь к файлу
        full_path = os.path.join(dir_path, filename)

        try:
            with open(full_path, 'rb') as file:
                self.blocks, self.transaction_storage, self.block_candidate = pickle.load(file)
            print("Blockchain loaded from disk.")
        except FileNotFoundError:
            print("No blockchain file found.")
        except Exception as e:
            print(f"Failed to load blockchain: {e}")

    def validate_block(self, block):

        return True

    def validate_and_add_block(self, block):

        if self.validate_block(block):
            self.add_block(block)
            return True


    def add_block(self, block):
        """  """
        self.blocks.append(block)

        # for new_node in block.new_nodes:
        #     self.nodes_rating[new_node] = 0

        for transaction in block.transactions:
            self.transaction_storage.add_transaction(transaction)

            # # при любом вознаграждении повышаем рейтинг
            # if transaction.fromAddress == '0000000000000000000000000000000000':
            #     self.nodes_rating[transaction.toAddress] = self.nodes_rating.get(transaction.toAddress, 0)+1

    def blocks_count(self):
        return len(self.blocks)

    def get_nodes(self):
        # for block in self.blocks:
        #     for new_node in block.new_nodes:
        #         self.nodes_rating[new_node] = 0

        return self.nodes_rating

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

    def add_block_candidate(self, block: Block):
        """  В цепи лежит блок, который является доминирующим"""

        if block is None:
            return False

        # первый блок
        if self.last_block() is None and self.block_candidate is None:
            self.block_candidate = copy.deepcopy(block)
            print("New candidat", self.block_candidate.hash, self.block_candidate.winer_address)
            return True

        # print("Исходный block:", block)
        if self.block_candidate is None:
            self.block_candidate = copy.deepcopy(block)
            return True


        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000" if self.last_block() is None else self.last_block().hash

        is_key_block = self.protocol.is_key_block(self.previousHash)
        # print(f"Key block: {is_key_block}")

        # при ключевом блоке проверяем, не является ли адрем новым
        if not is_key_block:

            addrs = self.transaction_storage.balances.keys()
            if self.block_candidate.winer_address in addrs and block.winer_address not in addrs:
                """ кандидат не в списках майнеров """
                return False



        win_address = self.protocol.winner(self.block_candidate.winer_address, block.winer_address,
                                           self.protocol.sequence(self.previousHash))

        if win_address == self.block_candidate.winer_address:
            return False
        # новый победитель
        self.block_candidate = copy.deepcopy(block)
        print("New candidat", self.block_candidate.hash, self.block_candidate.winer_address)

        return True

    def close_block(self):
        """ Берем блок кандидата как верный """
        if self.block_candidate is not None:
            self.add_block(copy.deepcopy(self.block_candidate))

        self.block_candidate = None

    def need_close_block(self):
        """ Если со времни появления последнего блока прошло более минуты, можно закреплять блок """


        if self.block_candidate is None:
            return False
        print(f"Check:  block_candidate: {self.block_candidate.datetime()} time:{self.time_ntpt.get_corrected_datetime()} delta: {self.block_candidate.time -self.time_ntpt.get_corrected_time()}  {self.block_candidate.hash_block()}")

        if self.block_candidate.time >self.time_ntpt.get_corrected_time():

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
