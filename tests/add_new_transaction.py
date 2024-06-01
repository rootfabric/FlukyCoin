from core.Transactions import Transaction
from net.client import Client
from core.protocol import Protocol

import random
if __name__ == '__main__':
    """ """

    t = Transaction("coinbase", random.randint(0,100000), "2", "100")
    t.make_hash()
    # print(t.get_data_hash().hexdigest())
    print(t.txhash)

    # client = Client(host = "127.0.0.1", port = 9334)
    client = Client(host = "192.168.0.26", port = 9334)

    response = client.send_request(
        {'command': 'version', 'ver': Protocol.VERSION, 'address': "127.0.0.1:888"})
    print(response)

    response = client.send_request(
        {'command': 'tx', 'tx_data': {'tx_json':t.to_json(), 'tx_sign':t.signature}})
    print(response)
