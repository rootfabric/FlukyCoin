import datetime
import hashlib
import time

from core.transaction import Transaction
import os, json
import random
from storage.transaction_storage import TransactionStorage, TransactionGenerator
import base64
# from crypto.xmss import *


class Block:

    def __init__(self, previousHash=None):
        self.index = 0
        self.time = time.time()
        self.previousHash = "0000000000000000000000000000000000000000000000000000000000000000" if previousHash is None else previousHash
        # self.previousHash = "3b6c2c7aa4d45aa89fcad9568208270fb73dd954a0c62b33d5e47355d4157ff1" if previousHash is None else previousHash
        self.transactions = []
        self.hash = None
        # self.new_nodes = {}

        # публичны ключ того кто сделал блок.
        self.signer = None

        self.sign = None

        # параметр возникновения ключевого блока
        self.diff_key_block = 11

        # технические параметры, для симулятора, ускоряющие работу

        # уровень победителя и его адрес
        self.winer_ratio = 0
        self.winer_address = None

    def to_json_for_sign(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        block_dict = {
            'index': self.index,
            'previousHash': self.previousHash,
            'time': self.time,
            'transactions': [tr.to_json() for tr in self.transactions],
            'hash': self.hash,
            'diff_key_block': self.diff_key_block,
            'signer': self.signer
        }
        return json.dumps(block_dict)

    def to_json(self):
        # Преобразование объекта Block в словарь для последующей сериализации в JSON
        block_dict = {
            'index': self.index,
            'previousHash': self.previousHash,
            'time': self.time,
            'transactions': [tr.to_json() for tr in self.transactions],
            'hash': self.hash,
            'diff_key_block': self.diff_key_block,
            'signer': self.signer,
            'sign': self.sign,
            'winer_ratio': self.winer_ratio,
            'winer_address': self.winer_address
        }
        return json.dumps(block_dict)

    @classmethod
    def from_json(cls, json_str):
        # Десериализация строки JSON обратно в объект Block
        block_dict = json.loads(json_str)
        block = cls(block_dict['previousHash'])
        block.index = block_dict['index']
        block.time = block_dict['time']
        block.transactions = [Transaction.from_json(t) for t in block_dict['transactions']]
        block.hash = block_dict['hash']
        block.diff_key_block = block_dict['diff_key_block']
        block.signer = block_dict['signer']
        block.sign = block_dict['sign']
        block.winer_ratio = block_dict['winer_ratio']
        block.winer_address = block_dict['winer_address']
        return block

    # def as_dict(self):
    #     info = {}
    #     info['index'] = str(self.index)
    #     info['previousHash'] = str(self.previousHash)
    #     info['transactions'] = self.transactions
    #     info['new_nodes'] = self.new_nodes
    #     info['hash'] = str(self.hash)
    #     return info

    def hash_block(self):
        """ Формирование блока"""
        self.hash = self.calculate_hash()

    def add_new_node(self, node, node_parrent):
        # формирование транзекций новой ноды
        # if node in self.nodes:
        #     return
        if node not in self.new_nodes:
            self.new_nodes[node] = node_parrent
            return

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def calculate_hash(self):

        text_transaction = " ".join([t.to_json() for t in self.transactions])

        data = str(self.previousHash) + str(text_transaction)
        data += str(self.signer) + str(self.winer_address)

        result = hashlib.sha256(data.encode())
        return result.hexdigest()

    def count_initial_zeros(self):

        # Шаг 2 и 3: Подсчёт начальных нулей в шестнадцатеричной строке
        count = 0
        for char in self.hash:
            if char == '0':
                count += 1
            else:
                break

        return count

    def block(self):
        self.hash = self.calculate_hash()

    def datetime(self):
        return datetime.datetime.fromtimestamp(self.time)
    def __equal__(self, other):
        return (self.index == other.blocks_count and
                self.timeStamp == other.timestamp and
                self.previousHash == other.previousHash and
                self.hash == other.hash and
                self.transactions == other.transaction and
                self.nonce == other.nonce
                )

    def get_seed_from_hash(self, hash_sum):
        """
        Преобразует хеш-сумму блока в сид для генератора случайных чисел.

        :param hash_sum: Строковое представление хеш-суммы.
        :return: Целочисленный сид.
        """
        return int(hash_sum, 16)

    def find_winner_in_new_nodes(self):
        """ """
        # победитель может быть в нодах, в стаках и в новых нодах.

        new_nodes_raiting = {node: 0 for node in self.new_nodes.keys()}
        return self.find_winner_adress(new_nodes_raiting)

    def find_winner_in_nodes(self, nodes: dict):
        """ """
        return self.find_winner_adress(nodes)

    def max_matching_characters(self, str1, str2):
        # Подсчитываем количество каждого символа в обеих строках
        count_str1 = {}
        count_str2 = {}
        for char in str1:
            count_str1[char] = count_str1.get(char, 0) + 1
        for char in str2:
            count_str2[char] = count_str2.get(char, 0) + 1

        # Считаем максимальное количество совпадающих символов
        matching_count = 0
        for char, count in count_str1.items():
            if char in count_str2:
                matching_count += min(count, count_str2[char])

        return matching_count

    # def find_longest_common_substring(self, s1, s2):
    #     if len(s1) == 0 or len(s2) == 0:
    #         return 0, ""
    #
    #     matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    #     longest = 0
    #     lcs = ""
    #
    #     for i in range(len(s1)):
    #         for j in range(len(s2)):
    #             if s1[i] == s2[j]:
    #                 c = matrix[i][j] + 1
    #                 matrix[i + 1][j + 1] = c
    #                 if c > longest:
    #                     longest = c
    #                     lcs = s1[i - c + 1:i + 1]
    #             else:
    #                 matrix[i + 1][j + 1] = 0
    #
    #     return longest, lcs

    def find_longest_common_substring(self, s1, s2):
        if len(s1) == 0 or len(s2) == 0:
            return 0, ""

        # Использование только двух строк вместо полной матрицы
        previous_row = [0] * (len(s2) + 1)
        current_row = [0] * (len(s2) + 1)
        longest = 0
        lcs_end = 0  # Храним позицию окончания LCS для уменьшения числа операций с строками

        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                if s1[i - 1] == s2[j - 1]:
                    current_row[j] = previous_row[j - 1] + 1
                    if current_row[j] > longest:
                        longest = current_row[j]
                        lcs_end = i  # Обновляем позицию окончания LCS
                else:
                    current_row[j] = 0
            # Обновляем строки для следующей итерации
            previous_row, current_row = current_row, [0] * (len(s2) + 1)

        lcs = s1[lcs_end - longest: lcs_end]  # Получаем LCS из строки s1
        return longest, lcs

    # def find_winner_adress(self, nodes: dict):
    #     r = random.Random(self.previousHash)
    #     max_reward = 100  # Максимальное вознаграждение
    #
    #     # sorted_nodes = sorted(nodes.items())
    #     sorted_data = sorted(nodes, key=lambda x: (x[1], x[0]))
    #
    #     count = 1
    #     for _ in range(32):
    #
    #         # sequence = r.getrandbits(128).to_bytes(16, byteorder='big').hex()  # Получаем 128-битную последовательность
    #         sequence = r.getrandbits(128).to_bytes(16, byteorder='big')
    #         # original_length = len(sequence)
    #
    #         sequence = base58.b58encode(sequence).decode('utf-8')
    #         # print(f'Ищем последовательность: {sequence}')
    #         while sequence:
    #             for address in sorted_data:
    #                 # рэйтинг адреса должен влиять на награду. при низком большую не выбить
    #                 if len(sequence) <= nodes[address] + 1:
    #                     # обрезаем OUT
    #                     if sequence in address[3:]:
    #                         reward = max_reward * len(sequence) / count
    #                         # Учитываем рейтинг для резкого уменьшения награды
    #                         # reward = max_reward -(max_reward * (2 ** (-1 * (32 - len(sequence)) / 32))) * (2 ** (-rating))
    #
    #                         # if reward>10:
    #                         if len(sequence)>4:
    #                             print(f'Победитель: {address}, Вознаграждение: {reward}', len(sequence))
    #                         # self.winner_node = address
    #                         # self.winner_node_amount = reward
    #
    #                         return {'address': address, 'reward': reward}
    #             sequence = sequence[:-1]  # Убираем последний символ
    #             count += 1
    #
    #         # print('Победитель не найден')
    #         max_reward /= 2
    def find_winner_adress(self, nodes: dict):
        # r = random.Random(self.previousHash)
        max_reward = 100  # Максимальное вознаграждение

        # sorted_nodes = sorted(nodes.items())
        sorted_data = sorted(nodes, key=lambda x: (x[1], x[0]))

        # sequence = r.getrandbits(128).to_bytes(16, byteorder='big').hex()  # Получаем 128-битную последовательность
        # sequence = r.getrandbits(128).to_bytes(16, byteorder='big')
        # original_length = len(sequence)

        sequence = base58.b58encode(self.previousHash).decode('utf-8').lower()
        # print(f'Ищем последовательность: {sequence}')
        res = {}

        for address in sorted_data:

            longest_length, lcs = self.find_longest_common_substring(sequence, address[3:].lower())
            res[address] = longest_length

            if longest_length >= 5:
                print(longest_length, lcs)

            return {'address': address, 'reward': longest_length}

    def get_sign_address(self):
        """ """
        return XMSSPublicKey.from_bytes(base64.b64decode(self.signer)).generate_address()

    def check_sign(self):
        """ проверка подписи """
        # Верификация подписи
        sign = SigXMSS.from_bytes(base64.b64decode(self.sign))
        PK_signer = XMSSPublicKey.from_bytes(base64.b64decode(self.signer))
        verification_result = XMSS_verify(sign, self.to_json_for_sign().encode(), PK_signer)
        # print("Подпись:",  verification_result)
        return verification_result


if __name__ == '__main__':
    """ """
    # r = random.Random(1)
    # bits = 128
    # sequence = r.getrandbits(bits).to_bytes(bits // 8, byteorder='big').hex()
    # print(sequence)
    # exit(0)

    # transaction_storage = TransactionStorage()
    #
    # # Использование генератора транзакций
    # generator = TransactionGenerator(address_count=2, transaction_count=100)
    # transactions = generator.generate_transactions_from_genesis()
    # for transaction in transactions:
    #     transaction_storage.add_transaction(transaction)
    #
    # generator = TransactionGenerator(address_count=2, transaction_count=100)
    # transactions = generator.generate_transactions()
    # for transaction in transactions:
    #     transaction_storage.add_transaction(transaction)
    #
    # # tr = [Transaction('0', 'a1', 10), Transaction("a1", "a2", 1)]
    # block = Block(timeStamp=datetime.datetime.now(), previousHash="123",
    #               transactions=transaction_storage)
    #
    # block.addresses = [a[0] for a in transaction_storage.get_addresses_sorted_by_balance()]
    #
    # for i in range(10000):
    #     sequence = random.getrandbits(128).to_bytes(128 // 8, byteorder='big').hex()
    #     block.addresses.append(sequence)
    #
    # block.find_winner()
    # # block.save()
    # print(block.nonce, block.hash)
