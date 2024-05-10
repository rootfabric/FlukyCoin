
from crypto.mercle import MerkleTools


if __name__ == '__main__':
    mt = MerkleTools(hash_type="SHA256")  # default is sha256
    # valid hashTypes include all crypto hash algorithms
    # such as 'MD5', 'SHA1', 'SHA224', 'SHA256', 'SHA384', 'SHA512'
    # as well as the SHA3 family of algorithms
    # including 'SHA3-224', 'SHA3-256', 'SHA3-384', and 'SHA3-512'

    hex_data = '7b3dab1fa45fde417c6431c714392d3842c4f53f0c42c08f5c0a152b4e1aafb3'
    hex_data2 = '3564ed0691dac7b73b78a320d71fcde904a0f62e2746ae6fce26cee9d1f91f2c'
    # list_data = ['Some text data', 'perhaps']

    mt.add_leaf(hex_data)
    mt.add_leaf(hex_data2)
    # mt.add_leaf(list_data, True)

    leaf_count =  mt.get_leaf_count();
    print("leaf_count", leaf_count)

    leaf_value =  mt.get_leaf(1)
    print(leaf_value)

    mt.make_tree()

    print(mt.is_ready )

    root_value = mt.get_merkle_root();
    print(root_value)