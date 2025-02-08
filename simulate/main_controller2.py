import time
from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from core.Transactions import TransferTransaction, NodeRegistrationTransaction, ValidationTransaction
from storage.chain import Chain
from crypto.xmss import XMSS
from storage.mempool import Mempool
from pprint import pprint
from crypto.vrf_xmss import ValidatorVRF_XMSS  # Подключаем VRF-класс


class NodeSimulate():
    """ Симуляция узла """

    def __init__(self, key, ip="192.168.0.26", port="9334"):
        """ Инициализация узла """
        self.ip = ip
        self.port = port
        self.transaction = []

        self.xmss = XMSS.create(key=key)
        self.chain = Chain(node_dir_base=self.xmss.address)

        # VRF-валидатор
        self.vrf_validator = ValidatorVRF_XMSS(self.xmss)

    def create_genesis_block(self, time):
        """ Первая нода делает блок генезиса """

        # Создание блока
        block_genesis = Block.create(self.chain.blocks_count(), self.chain.last_block_hash(), time, self.transaction,
                                     address_miner=self.xmss.address, address_reward=self.xmss.address)
        block_genesis.make_sign_before_validation(self.xmss)

        # Создание транзакции валидации
        validation_transaction = ValidationTransaction(self.xmss.address, block_genesis.hash_before_validation)
        validation_transaction.make_hash()
        validation_transaction.make_sign(self.xmss)

        block_genesis.add_validator_signature(validation_transaction)

        block_genesis.calculate_hash_with_signatures(time)

        block_genesis.make_sign_final(self.xmss)

        self.chain.add_block_candidate(block_genesis)
        self.chain.close_block()

        return block_genesis

    def adress(self):
        """ Возвращает адрес ноды """
        return self.xmss.address

    def create_registration_transaction(self):
        """ Регистрация в блокчейне """
        transaction1 = NodeRegistrationTransaction(self.xmss.address,
                                                   {"address": self.xmss.address, "ip": self.ip, "port": self.port})
        transaction1.make_hash()
        transaction1.make_sign(self.xmss)

        self.transaction.append(transaction1)

    def get_list_candidate(self):
        """ Получает список возможных лидеров и валидаторов """
        return self.chain.transaction_storage.miners

    def work(self, current_time):
        """ Работа ноды: определение лидера по VRF """

        # Получаем кандидатов
        list_candidates = self.get_list_candidate()
        block = self.chain.last_block()

        # Генерация VRF-значений для всех кандидатов
        candidate_vrfs = {}
        for candidate in list_candidates:
            vrf_data = self.vrf_validator.generate_vrf(block.previousHash)
            candidate_vrfs[candidate] = vrf_data

        # Определение победителя (наименьшее VRF-значение)
        leader = min(candidate_vrfs, key=lambda x: candidate_vrfs[x]['vrf_output'])

        # Проверка, является ли текущий узел лидером
        if self.xmss.address == leader:
            print(f"✅ Узел {self.xmss.address} выиграл лидерство и может создать новый блок!")
            # Здесь можно запустить процесс создания нового блока

        else:
            print(f"⏳ Узел {self.xmss.address} не является лидером. Лидер: {leader}")


class MainController:
    """ Контроллер симуляции """

    def __init__(self, start_time=0):
        self.start_time = start_time
        self.time = start_time
        self.nodes = []
        self.blocks = []
        self.transactions = []

    def step(self):
        """ Шаг симуляции: работа всех узлов """
        for node in self.nodes:
            node.work(self.time)


def simulate1():
    """ Запуск симуляции """


if __name__ == "__main__":
    m = MainController()

    node1 = NodeSimulate('45be862faf6e0dd0ec3d4b9da8f8e12b3e4e130f8ba5c7ce67d8b1894b80c1a7e4d9c29d')
    print("node1", node1.adress())
    node2 = NodeSimulate('45f82094df93616c349d2cbb587bea590e8396a44e457f99ce11324bc11d5e190c9bb9e9')
    print("node2", node2.adress())
    node3 = NodeSimulate('43bc879a2219e29793f8487782c1ef408dd9d72aee50570a2ac11260cb5588b66e3b7ce4')
    print("node3", node3.adress())

    m.nodes.append(node1)
    m.nodes.append(node2)
    m.nodes.append(node3)

    # Регистрация узлов
    node1.create_registration_transaction()
    node2.create_registration_transaction()
    node3.create_registration_transaction()

    # Создание блока генезиса
    block_genesis = node1.create_genesis_block(m.time)
    m.blocks.append(block_genesis)

    # Запуск симуляции
    m.step()
