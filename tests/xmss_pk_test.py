import base64

from crypto.xmss import *

if __name__ == '__main__':
    # Пример использования
    keys = XMSS.create(6)

    PK = keys.keyPair.PK

    print(PK.generate_address())
    print(PK.max_height())

    pk_hex = PK.to_hex()

    # pk_str = PK.to_str()
    # print("pk_str", pk_str)
    # pk_bytes = PK.to_bytes()
    # pk_hex =pk_bytes.hex()
    #
    #
    # pk_bytes = bytes.fromhex(pk_hex)
    #
    # # распаковываем подписи
    # PK2 = XMSSPublicKey.from_bytes(pk_bytes)

    PK2 = XMSSPublicKey.from_hex(pk_hex)

    print(PK2.generate_address())

    print(keys.sign_before_validation(b"1"))
    print(keys.count_sign())
    print(keys.sign_before_validation(b"2"))
    print(keys.count_sign())
    print(keys.sign_before_validation(b"3"))
    print(keys.count_sign())
    print(keys.sign_before_validation(b"4").to_hex())
    print(keys.count_sign())
    print(keys.sign_before_validation(b"4"))
    print(keys.count_sign())
