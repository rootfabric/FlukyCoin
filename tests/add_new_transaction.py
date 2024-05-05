from core.transaction import Transaction
from net.client import Client
import random
if __name__ == '__main__':
    """ """

    t = Transaction("coinbase", random.randint(0,100000), "2", "100")
    t.make_hash()
    # print(t.get_data_hash().hexdigest())
    print(t.hash)

    client = Client(port = 5557)

    response = client.send_request(
        {'command': 'tx', 'tx_data': {'tx_json':t.to_json(), 'tx_sign':t.sign}})
