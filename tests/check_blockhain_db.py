from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from tools.config_loader import ConfigLoader

import pprint

if __name__ == '__main__':
    """ """
    config_loader = ConfigLoader('../config/','node_config.yaml')
    # config_loader = ConfigLoader('../config/','node_config_off.yaml')
    config = config_loader.load_config()

    chain = Chain(config)
    chain2 = Chain()

    # print(chain.last_block().to_json())

    print("Все балансы:", chain.transaction_storage.get_all_balances())


    for b in chain.transaction_storage.get_addresses_sorted_by_balance():
        print(b[0], b[1]/100000000)

    all_ratio = 0
    list_time =[]
    for i, block in enumerate(chain.blocks):

        if block is None:
            print("!!!!!!!")
        if not chain2.validate_block(block):
            print("Блок не валидный")
        chain2.add_block_candidate(block)
        chain2.close_block()

        is_key = Protocol.is_key_block(block.hash_block())
        # if is_key:
        #     print(i)

        t = Protocol.find_longest_common_substring(block.signer.lower(), Protocol.sequence(block.previousHash))
        ratio =t[0]

        if ratio>4:
            print("RATIO!!!", ratio)

        h = Protocol.address_height(block.signer)

        all_ratio += ratio*h

        if i>0:
            b0 : Block = chain.blocks[i-1]
            b1 : Block= chain.blocks[i]

            t = b1.timestamp_seconds_before_validation - b0.timestamp_seconds_before_validation
            list_time.append(t)

            print(i, block.datetime(), block.signer, block.mining_reward()/10000000, block.signer, chain2.next_address_nonce(block.signer))
            # print(b0.hash, b1.previousHash, t)

    print(list_time)

    print(len(chain.blocks))
    print(len(chain2.blocks))

    print(chain2.transaction_storage.nonces)
    print("all_ratio", all_ratio)
