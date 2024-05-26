import time

from core.transaction import Transaction
from core.Block import Block
from core.protocol import Protocol

from crypto.xmss import XMSS

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
    block = Block().create(0, None, t,[], address_miner='1234567', address_reward="aaaaa")
    # hash_block = block.calculate_hash()
    print(block.Hash)

    sign = block.make_sign(xmss).hex()

    print(sign)



