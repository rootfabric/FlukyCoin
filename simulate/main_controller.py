import time

from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from core.Transactions import TransferTransaction, NodeRegistrationTransaction, ValidationTransaction
from storage.chain import Chain
from crypto.xmss import XMSS
from storage.mempool import Mempool
from pprint import pprint


class NodeSimulate():
    """ """

    def __init__(self, key, ip="192.168.0.26", port="9334"):
        """ """
        self.ip = ip
        self.port = port

        self.transaction  = []

        self.xmss = XMSS.create(key=key)
        self.chain = Chain(node_dir_base=self.xmss.address)



    def create_genesis_block(self, time):
        """ Первая нода делает блок генезиса """

        # сам создает блок
        block_genesis = Block.create(self.chain.blocks_count(), self.chain.last_block_hash(), time, self.transaction, address_miner=self.xmss.address,
                                address_reward=self.xmss.address)
        block_genesis.make_sign_before_validation(self.xmss)


        # сам валидирует
        vadidation_transaction = ValidationTransaction(self.xmss.address, block_genesis.hash_before_validation)
        vadidation_transaction.make_hash()
        vadidation_transaction.make_sign(self.xmss)

        block_genesis.add_validator_signature(vadidation_transaction)

        block_genesis.calculate_hash_with_signatures(time)

        block_genesis.make_sign_final(self.xmss)

        self.chain.add_block_candidate(block_genesis)
        self.chain.close_block()

        return block_genesis

    def adress(self):
        # print(self.xmss.address)
        return self.xmss.address

    def create_registration_transaction(self):
        """  Регистрируемся в блокчейне """
        transaction1 = NodeRegistrationTransaction(self.xmss.address,
                                                   {"address": self.xmss.address, "ip": self.ip, "port": self.port, })
        transaction1.make_hash()
        transaction1.make_sign(self.xmss)

        # isValid = transaction1.validate_sign()
        self.transaction.append(transaction1)

    def get_list_candidate(self):
        """ кто может быть лидером и валидатором """
        return self.chain.transaction_storage.miners


    def work(self, current_time):
        """ Работа ноды """

        # из расчета текущего времени и предыдущего блока делаем действие

        # смотрим кто сейчас лидер а кто валидатор

        list_candidats = self.get_list_candidate()

        block  = self.chain.last_block()

        liders_and_validators = Protocol.lider_and_validators(list_candidats, block.previousHash, block.timestamp_seconds, current_time)
        print(liders_and_validators)


class MainController:
    """ """

    def __init__(self, start_time=0):
        self.start_time = start_time
        self.time = start_time

        self.nodes = []

        self.blocks = []
        self.transactions = []




    def step(self):
        """ """

        for node in self.nodes:
            node.work(self.time)


def simulate1():
    """"""


if __name__ == "__main__":
    m = MainController()

    node1 = NodeSimulate('45be862faf6e0dd0ec3d4b9da8f8e12b3e4e130f8ba5c7ce67d8b1894b80c1a7e4d9c29d')
    print("node1", node1.adress())
    node2 = NodeSimulate('45f82094df93616c349d2cbb587bea590e8396a44e457f99ce11324bc11d5e190c9bb9e9')
    print("node2", node2.adress())
    node3 = NodeSimulate('43bc879a2219e29793f8487782c1ef408dd9d72aee50570a2ac11260cb5588b66e3b7ce4')
    print("noda3", node3.adress())

    #
    m.nodes.append(node1)

    # добавляем транзакцию регестрирущую ноду
    node1.create_registration_transaction()

    # создание блока генезиса
    block_genesis = node1.create_genesis_block(m.time)
    m.blocks.append(block_genesis)
    m.step()
