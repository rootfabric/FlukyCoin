from storage.chain import Chain
from core.protocol import Protocol
from core.block import Block

if __name__ == '__main__':
    """ """

    chain = Chain()

    chain.load_from_disk(dir = "test_db")

    print(chain.last_block().to_json())

    print("Все балансы:", chain.transaction_storage.get_all_balances())


    for b in chain.transaction_storage.get_addresses_sorted_by_balance():
        print(b[0], b[1]/100000000)


    list_time =[]
    for i, block in enumerate(chain.blocks):
        is_key = Protocol.is_key_block(block.hash_block())
        if is_key:
            print(i)

        if i>0:
            b0 : Block = chain.blocks[i-1]
            b1 : Block= chain.blocks[i]

            t = b1.time - b0.time
            list_time.append(t)

            # print(b0.hash, b1.previousHash, t)

    print(list_time)
