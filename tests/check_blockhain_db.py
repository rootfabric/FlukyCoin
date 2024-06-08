from storage.chain import Chain
from core.protocol import Protocol
from core.Block import Block
from tools.config_loader import ConfigLoader


if __name__ == '__main__':
    """ """
    config_loader = ConfigLoader('../config/','node_config.yaml ')
    config = config_loader.load_config()

    chain = Chain(config)
    chain2 = Chain()

    chain.load_from_disk()

    print(chain.last_block().to_json())

    print("Все балансы:", chain.transaction_storage.get_all_balances())


    for b in chain.transaction_storage.get_addresses_sorted_by_balance():
        print(b[0], b[1]/100000000)


    list_time =[]
    for i, block in enumerate(chain.blocks):

        chain2.validate_block(block)
        chain2.add_block_candidate(block)
        chain2.close_block()

        is_key = Protocol.is_key_block(block.hash_block())
        # if is_key:
        #     print(i)

        if i>0:
            b0 : Block = chain.blocks[i-1]
            b1 : Block= chain.blocks[i]

            t = b1.timestamp_seconds - b0.timestamp_seconds
            list_time.append(t)

            print(block.datetime(), b0.hash, block.signer, block.mining_reward()/10000000, block.signer)
            # print(b0.hash, b1.previousHash, t)

    print(list_time)

    print(len(chain.blocks))
    print(len(chain2.blocks))
