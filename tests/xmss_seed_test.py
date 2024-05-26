import base64

from crypto.xmss import *


if __name__ == '__main__':
    # Пример использования
    # Создание объекта XMSSPrivateKey для теста

    height = 6  # Высота дерева
    n = 10  # Размер хэша в байтах
    w = 16  # Параметр Winternitz

    # print("Количество подписей", 2 ** height)
    # Генерация пары ключей на основе сида
    # keyPair_client1 = XMSS_keyGen(height, n, w)


    # test_secret_key = keyPair_client1.SK
    # test_secret_key.wots_private_keys = [[b'key1', b'key2'], [b'key3', b'key4']]
    # test_secret_key.idx = 1
    # test_secret_key.SK_PRF = 'test_prf'
    # test_secret_key.root_value = bytearray(b'test_root_value')
    # test_secret_key.SEED = 'test_seed'

    # Генерация сид фразы из секретного ключа
    # seed_phrase = generate_seed_from_secret_key(test_secret_key)
    # print(f"Seed Phrase: {seed_phrase}")
    #
    # # Восстановление секретного ключа из сид фразы
    # recovered_secret_key = generate_secret_key_from_seed(seed_phrase)
    # print(f"Recovered Secret Key: {recovered_secret_key.__dict__}")

    # Пример использования:
    secret_key = os.urandom(33)

    # Преобразование байт в целое число
    secret_key_number = int.from_bytes(secret_key, 'big')

    print("Сгенерированный ключ в виде байт:", secret_key)
    print("Ключ преобразованный в число:", secret_key_number)
    print("Ключ преобразованный в число:", len(str(secret_key_number)))

    print(base58.b58encode(secret_key))
    print(len(secret_key))
    seed_phrase = key_to_seed_phrase(secret_key)
    print(f"Seed Phrase: {seed_phrase}")
    restored_key = seed_phrase_to_key(seed_phrase)

    print("Restored Secret Key:", restored_key)

    if restored_key==secret_key:
        print(" Ключи верны")
