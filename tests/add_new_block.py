from core.transaction import Transaction
from core.Block import Block
from core.protocol import Protocol

from net.client import Client
import random
if __name__ == '__main__':
    """ """

    t = Transaction("coinbase", random.randint(0,100000), "2", "100")
    t.make_hash()
    # print(t.get_data_hash().hexdigest())
    print(t.txhash)
    block = Block()
    block.add_transaction(t)

    client = Client(host = "127.0.0.1", port = 9333)

    response = client.send_request(
        {'command': 'version', 'ver': Protocol.version, 'address':"127.0.0.1:888"})
    print(response)
    response = client.send_request(
        {'command': 'newblock', 'block_data': block.to_json()})
    print(response)
