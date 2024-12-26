import time

from core.Transactions import TransferTransaction
from core.Block import Block
from core.protocol import Protocol

from crypto.xmss import XMSS


import random
if __name__ == '__main__':
    """ """

    xmss = XMSS.create()
    print(xmss.address)


    t = TransferTransaction("aaaaa", ['bbbbb'], ["100000000"], "1000")
    t.nonce = 1
    t.make_hash()

    print(t.to_json())





