from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from core.Transactions import TransferTransaction
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

    c2 = Chain(node_dir_base="2")
    c2.transaction_storage.clear()
    c2.clear_db()

    xmss1 = XMSS.create(key='45be862faf6e0dd0ec3d4b9da8f8e12b3e4e130f8ba5c7ce67d8b1894b80c1a7e4d9c29d')
    # print('xmss1', xmss1.private_key.hex())
    print('xmss1', xmss1.address)
    xmss2 = XMSS.create(key='45f82094df93616c349d2cbb587bea590e8396a44e457f99ce11324bc11d5e190c9bb9e9')
    # print(xmss2.private_key.hex())
    print('xmss2', xmss2.address)

    # пользователи создают блоки
    t = 1716710000
    с = c1.blocks_count()
    xmss1_b0 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b0.make_sign(xmss1)

    c1.add_block_candidate(xmss1_b0)

    t = 1716710001
    xmss2_b0 = Block.create(c1.blocks_count(), c2.last_block_hash(), t, [], address_miner=xmss2.address, address_reward=xmss2.address)
    xmss2_b0.make_sign(xmss2)
    """ Добавление блоков """

    c1.add_block_candidate(xmss2_b0)

    c2.add_block_candidate(xmss2_b0)
    c2.add_block_candidate(xmss1_b0)

    c1.close_block()
    c2.close_block()

    print(c1.last_block_hash())
    print(c2.last_block_hash())

    pprint(c1.transaction_storage.get_all_balances())
    pprint(c2.transaction_storage.get_all_balances())

    """ Создание транзакции и валидация в цепи """

    tt = TransferTransaction("KziK2EjThDUuXU7W4wjxvQgcfyVWbG8WFZhyCakhrpUvrkUH76zt",
                             ["1111111111111111111111111111111111111111111111111111"],
                             [100],
                             fee=10
                             )
    tt.nonce = c1.next_address_nonce(tt.fromAddress)
    tt.make_hash()
    tt.make_sign(xmss1)
    print("transaction hash",  tt.txhash)

    is_valid = c1.validate_transaction(tt)
    print("transaction is_valid", is_valid)

    """ Создание блока с транзакциями и валидация в цепи """
    # пользователи создают блоки
    t = 1716720000
    xmss1_b1 = Block.create(c1.blocks_count(), c1.last_block_hash(), t, [tt], address_miner=xmss1.address, address_reward=xmss1.address)
    xmss1_b1.make_sign(xmss1)
    t = 1716720001
    xmss2_b1 = Block.create(c1.blocks_count(), c2.last_block_hash(), t, [tt], address_miner=xmss2.address, address_reward="2222222222222222222222222222222222222222222222222222")
    xmss2_b1.make_sign(xmss2)
    """ Добавление блоков """
    # c1.add_block_candidate(xmss1_b1)
    c1.add_block_candidate(xmss2_b1)

    c2.add_block_candidate(xmss2_b1)
    # c2.add_block_candidate(xmss1_b1)

    c1.close_block()
    c2.close_block()

    print(c1.last_block_hash())
    print(c2.last_block_hash())

    pprint(c1.transaction_storage.get_all_balances())
    pprint(c2.transaction_storage.get_all_balances())



