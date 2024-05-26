import base64

from crypto.xmss import *

if __name__ == '__main__':
    # Пример использования
    keys = XMSS.create(5)

    PK = keys.keyPair.PK

    print(PK.generate_address())

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