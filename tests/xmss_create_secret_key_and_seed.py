import base64

from crypto.xmss import *

if __name__ == '__main__':
    # Пример использования
    # Создание объекта XMSSPrivateKey для теста

    # height = 6  # Высота дерева
    # n = 10  # Размер хэша в байтах
    # w = 16  # Параметр Winternitz
    #
    # Пример использования:
    # secret_key = os.urandom(36)
    #
    # # Преобразование байт в целое число
    # secret_key_number = int.from_bytes(secret_key, 'big')
    #
    # print("Сгенерированный ключ в виде байт:", secret_key)
    # # print("Ключ преобразованный в число:", secret_key_number)
    # # print("Ключ преобразованный в текст:", len(str(secret_key_number)))
    #
    # print("Сгенерированный ключ в строке", base58.b58encode(secret_key).decode())
    # seed_phrase = key_to_seed_phrase(secret_key)
    # print(f"Seed Phrase: {seed_phrase}")
    #
    # restored_key = seed_phrase_to_key(seed_phrase)
    # # print("Restored Secret Key:", restored_key)
    # print("Restored Secret Key преобразованный в текст:", base58.b58encode(restored_key).decode())
    # if restored_key == secret_key:
    #     print("Ключи верны")


    # Тестирование
    height, n, w = 6, 10, 16
    extended_key = create_extended_secret_key(height)
    print(extended_key)
    print("Extended Secret Key:", extended_key.hex())

    seed_phrase = key_to_seed_phrase(extended_key)
    print("Seed Phrase:", seed_phrase)

    restored_extended_key = seed_phrase_to_key(seed_phrase)
    restored_height, restored_secret_key = extract_parameters_from_key(restored_extended_key)
    print(restored_secret_key)
    print("Restored Parameters:", restored_height)
    print("Restored Secret Key:", restored_secret_key.hex())
    print("Keys are the same:", extended_key == restored_secret_key)