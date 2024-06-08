from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from core.Transactions import TransferTransaction
from storage.chain import Chain
from crypto.xmss import XMSS
from storage.mempool import Mempool
from pprint import pprint

if __name__ == '__main__':
    """ Тестирование максимальной подписи и валидации"""

    """ создание цепи """
    c1 = Chain()
    c2 = Chain()

    # xmss1 = XMSS.create(2)
    xmss1 = XMSS.create(key='429b17ebcb160473674f828098278cde896779742fe881a2c9d1d25c6dcd7c07e8c00e70')
    print('private_key', xmss1.private_key.hex())
    print('xmss1 address', xmss1.address)
    # пользователи создают блоки
    t = 1716710000
    xmss1_b0 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b0.make_sign(xmss1)

    """ Добавление блоков """
    c1.add_block_candidate(xmss1_b0)

    c1.close_block()


    print(c1.last_block_hash())

    pprint(c1.transaction_storage.get_all_balances())
    print("count_sign", xmss1.count_sign())

    """ Создание транзакции и валидация в цепи """

    tt = TransferTransaction("Kx4cWtri8AuF46MfXhn74F5Yj2R9VgjvyRVDYLssDu5rFpxUnytX",
                             ["1111111111111111111111111111111111111111111111111111"],
                             [100],
                             fee=10
                             )
    tt.nonce = c1.next_address_nonce(tt.fromAddress)
    tt.make_hash()
    tt.make_sign(xmss1)
    print("transaction hash",  tt.txhash)
    print("count_sign", xmss1.count_sign())

    # tt2 = TransferTransaction("Kx4cWtri8AuF46MfXhn74F5Yj2R9VgjvyRVDYLssDu5rFpxUnytX",
    #                          ["1111111111111111111111111111111111111111111111111111"],
    #                          [100],
    #                          fee=10
    #                          )
    # tt2.nonce = c1.next_address_nonce(tt.fromAddress)
    # tt2.make_hash()
    # tt2.make_sign(xmss1)
    # print("transaction hash",  tt2.txhash)
    # print("count_sign", xmss1.count_sign())
    # c1.validate_transaction(tt2)

    """ Создание блока с транзакциями и валидация в цепи """
    # пользователи создают блоки
    t = 1716720000
    xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [tt], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b1.make_sign(xmss1)

    """ Добавление блоков """
    c1.add_block_candidate(xmss1_b1)



    c1.close_block()


    print(c1.last_block_hash())

    pprint(c1.transaction_storage.get_all_balances())

    print("count_sign", xmss1.count_sign())




    """ Создание блока с транзакциями и валидация в цепи """
    # пользователи создают блоки
    t = 1716730000
    xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b1.make_sign(xmss1)

    """ Добавление блоков """
    c1.add_block_candidate(xmss1_b1)



    c1.close_block()
    print("count_sign", xmss1.count_sign())

    xmss1.set_idx(2)
    """ Создание блока с транзакциями и валидация в цепи """
    # пользователи создают блоки
    t = 1716740000
    xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b1.make_sign(xmss1)

    """ Добавление блоков """
    c1.add_block_candidate(xmss1_b1)



    c1.close_block()
    print("count_sign", xmss1.count_sign())
