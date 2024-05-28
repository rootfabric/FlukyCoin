import time

from core.transaction import TransferTransaction
from core.Block import Block
from core.protocol import Protocol

from crypto.xmss import XMSS

from net.client import Client
import random
if __name__ == '__main__':
    """ """

    xmss = XMSS.create()
    print(xmss.wallet_address)


    t = TransferTransaction("aaaaa", ['bbbbb'], ["100000000"], "1000")
    t.nonce = 1
    t.make_hash()

    print(t.to_json())





