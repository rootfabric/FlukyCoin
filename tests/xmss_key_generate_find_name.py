import base64

from crypto.xmss import *

if __name__ == '__main__':
    # Пример использования
    log = Log("KEYS_all")
    log2 = Log("KEYS")

    for i in range(1000):
        keys = XMSS.create(3)
        log.info(i, keys.address, keys.private_key.hex())
        log2.info(keys.address)

