import time

from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from core.Transactions import TransferTransaction, NodeRegistrationTransaction, ValidationTransaction
from storage.chain import Chain
from crypto.xmss import XMSS
from storage.mempool import Mempool
from pprint import pprint

if __name__ == '__main__':
    """ Тестирование валидаци цепи"""

    """ создание цепи """
    c1 = Chain(node_dir_base="1")
    c1.transaction_storage.clear()
    c1.clear_db()

    # c2 = Chain(node_dir_base="2")
    # c2.transaction_storage.clear()
    # c2.clear_db()

    xmss1 = XMSS.create(key='45be862faf6e0dd0ec3d4b9da8f8e12b3e4e130f8ba5c7ce67d8b1894b80c1a7e4d9c29d')
    print(xmss1.count_sign())
    # print('xmss1', xmss1.private_key.hex())
    print('xmss1', xmss1.address)
    xmss2 = XMSS.create(key='45f82094df93616c349d2cbb587bea590e8396a44e457f99ce11324bc11d5e190c9bb9e9')
    # print(xmss2.private_key.hex())
    print('xmss2', xmss2.address)

    xmss3 = XMSS.create(key='43bc879a2219e29793f8487782c1ef408dd9d72aee50570a2ac11260cb5588b66e3b7ce4')
    print('xmss3', xmss3.address)

    # первая транзакция, регистрация ноды
    transaction1 = NodeRegistrationTransaction(xmss3.address,
                                               {"address": xmss3.address, "ip": "192.168.0.26", "port": "9334", })
    transaction1.make_hash()
    transaction1.make_sign(xmss3)

    isValid = transaction1.validate_sign()

    print(xmss1.count_sign())

    # создание блока генезиса, первый пользователь в цепи
    t = 1716710000
    # t = time.time()
    с = c1.blocks_count()
    xmss1_b0 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [transaction1], address_miner=xmss3.address,
                            address_reward=xmss3.address)
    xmss1_b0.make_sign_before_validation(xmss3)

    import pprint

    # pprint.pprint(xmss1_b0.to_dict())

    # Валидатор прверяет блок, и делает свою подпись правильности блока
    validate_result = xmss1_b0.validate_before_validate()
    print(f"validate_result {validate_result}")

    list_candidats = [
        # xmss1.address,
        xmss2.address,
        xmss3.address
    ]
    # определяем текущего лидера и валидаторов

    liders_and_validators = Protocol.lider_and_validators(list_candidats, xmss1_b0.previousHash, t, t + 11)
    print(liders_and_validators)

    # Валидаторы получают предворительный блок, проверяют его и валидируют

    # EAcsef7kcVXGW15hqho2o3hvXKDc62xTjaTjxW6PLhL4XhwoNVus
    vadidation_transaction = ValidationTransaction(xmss2.address, xmss1_b0.hash_before_validation)
    vadidation_transaction.make_hash()
    vadidation_transaction.make_sign(xmss2)

    # KziK2EjThDUuXU7W4wjxvQgcfyVWbG8WFZhyCakhrpUvrkUH76zt
    # vadidation_transaction2 = ValidationTransaction(xmss1.address, xmss1_b0.hash_before_validation)
    # vadidation_transaction2.make_hash()
    # vadidation_transaction2.make_sign(xmss1)

    # pprint.pprint(vadidation_transaction.to_dict())
    # pprint.pprint(len(str(vadidation_transaction.to_dict())))
    # print(vadidation_transaction.validate_sign())

    # Лидер собирает подписи валидации и добавляет их в блок

    # xmss1_b0.add_validator_signature(vadidation_transaction2)
    xmss1_b0.add_validator_signature(vadidation_transaction)

    print("Блок с валидной транзакцией:")
    # pprint.pprint(xmss1_b0.to_dict())

    t +=10
    xmss1_b0.calculate_hash_with_signatures(t)

    xmss1_b0.make_sign_final(xmss3)

    # print("Блок с валидной транзакцией финально подписанный:")
    # pprint.pprint(xmss1_b0.to_dict())

    print(xmss1_b0.validate_final())

    c1.add_block_candidate(xmss1_b0)


    # Блок добавлен в цепь
    c1.add_block_candidate(xmss1_b0)


    print("-------------------")
    # print(vadidation_transaction.to_dict()['message_data'])
    # print(xmss1_b0.to_dict()['validators'][0])
    # pprint.pprint(xmss1_b0.to_dict())
    # print(xmss1_b0.to_dict()['validators'][0])
    b = Block.from_json(xmss1_b0.to_json())
    # pprint.pprint(b.to_dict())
    # print(b.to_dict()['validators'][0])
    c1.close_block()

    # print(c1.last_block())


    #################################################################################
    #  Проверка протокола, добавление второго блока

    t = c1.last_block().timestamp_seconds
    print("t", t)

    list_candidats = [
        xmss1.address,
        xmss2.address,
        xmss3.address
    ]

    liders_and_validators = Protocol.lider_and_validators(list_candidats, c1.last_block().hash, t, t + 10)
    print(liders_and_validators)

    print("c1.last_block_hash()", c1.last_block_hash())

    xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [], address_miner=xmss2.address,
                            address_reward=xmss2.address)
    xmss1_b1.make_sign_before_validation(xmss2)

    validate_result = xmss1_b1.validate_before_validate()
    print(f"validate_result {validate_result}")


    t+=10

    # Валидатор делает подпись:

    vadidation_transaction2 = ValidationTransaction(xmss3.address, xmss1_b1.hash_before_validation)
    vadidation_transaction2.make_hash()
    vadidation_transaction2.make_sign(xmss3)

    t += 10
    # Лидер собирает подписи валидации и добавляет их в блок

    xmss1_b1.add_validator_signature(vadidation_transaction2)
    xmss1_b1.calculate_hash_with_signatures(t)
    xmss1_b1.make_sign_final(xmss2)


    print(xmss1_b1.validate_final())
    # Блок добавлен в цепь
    print("add_block_candidate")
    c1.add_block_candidate(xmss1_b1)


    #
    # t = 1716710001
    # xmss2_b0 = Block.create(c1.blocks_count(), c2.last_block_hash(), t, [], address_miner=xmss2.address,
    #                         address_reward=xmss2.address)
    # xmss2_b0.make_sign(xmss2)
    # """ Добавление блоков """
    #
    # c1.add_block_candidate(xmss2_b0)
    #
    # c2.add_block_candidate(xmss2_b0)
    # c2.add_block_candidate(xmss1_b0)
    #
    # c1.close_block()
    # c2.close_block()
    #
    # print(c1.last_block_hash())
    # print(c2.last_block_hash())
    #
    # pprint(c1.transaction_storage.get_all_balances())
    # pprint(c2.transaction_storage.get_all_balances())
    #
    # """ Создание транзакции и валидация в цепи """
    #
    # tt = TransferTransaction("KziK2EjThDUuXU7W4wjxvQgcfyVWbG8WFZhyCakhrpUvrkUH76zt",
    #                          ["1111111111111111111111111111111111111111111111111111"],
    #                          [100],
    #                          fee=10
    #                          )
    # tt.nonce = c1.next_address_nonce(tt.fromAddress)
    # tt.make_hash()
    # tt.make_sign(xmss1)
    # print("transaction hash", tt.txhash)
    #
    # is_valid = c1.validate_transaction(tt)
    # print("transaction is_valid", is_valid)
    #
    # """ Создание блока с транзакциями и валидация в цепи """
    # # пользователи создают блоки
    # t = 1716720000
    # xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [tt], address_miner=xmss1.address,
    #                         address_reward=xmss1.address)
    # xmss1_b1.make_sign(xmss1)
    # t = 1716720001
    # xmss2_b1 = Block.create(c1.blocks_count(), c2.last_block_hash(), t, [tt], address_miner=xmss2.address,
    #                         address_reward="2222222222222222222222222222222222222222222222222222")
    # xmss2_b1.make_sign(xmss2)
    # """ Добавление блоков """
    # # c1.add_block_candidate(xmss1_b1)
    # c1.add_block_candidate(xmss2_b1)
    #
    # c2.add_block_candidate(xmss2_b1)
    # # c2.add_block_candidate(xmss1_b1)
    #
    # c1.close_block()
    # c2.close_block()
    #
    # print(c1.last_block_hash())
    # print(c2.last_block_hash())
    #
    # pprint(c1.transaction_storage.get_all_balances())
    # pprint(c2.transaction_storage.get_all_balances())
