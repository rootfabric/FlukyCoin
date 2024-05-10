from storage.chain import Chain

if __name__ == '__main__':
    """ """

    chain = Chain()

    chain.load_from_disk(dir = "test_db")

    print(chain.last_block().to_json())

    print("Все балансы:", chain.transaction_storage.get_all_balances())

    for b in chain.transaction_storage.get_addresses_sorted_by_balance():
        print(b[0], b[1]/100000000)
