import time

from core.Transactions import Transaction
from core.Block import Block
from core.protocol import Protocol

from crypto.xmss import XMSS
from pprint import pprint

from net.client import Client
import random
if __name__ == '__main__':
    """ """

    xmss = XMSS.create()
    print(xmss.address)


    # t = Transaction("coinbase", random.randint(0,100000), "2", "100")
    # t.make_hash()
    # # print(t.get_data_hash().hexdigest())
    # print(t.txhash.hexdigest())

    t = 1716713605.5979075
    block = Block.create(0, None, t, [], address_miner=xmss.address, address_reward="aaaaa")
    print(block.previousHash)
    print(block.hash)
    print(xmss.address)

    block.make_sign(xmss)

    json_block =block.to_json()
    pprint(json_block)


    block2 = Block.from_json(json_block)
    pprint(block2.to_json())

    if not block2.validate():
        print("Ошибка валидации")
    else:
        print("валидация ок")




