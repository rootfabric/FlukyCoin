import base64

from crypto.xmss import *

if __name__ == '__main__':
    # Пример использования
    keys = XMSS.create(5)

    PK = keys.keyPair.PK

    print(PK)