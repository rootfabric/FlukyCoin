import difflib
import random
import hashlib
import base58
import base64
import math
import uuid


class Protocol:
    VERSION = "0.1"
    # ожидание подсоединения активных пиров
    WAIT_ACTIVE_PEERS_BEFORE_START = 30
    # WAIT_ACTIVE_PEERS_BEFORE_START = 10

    # BLOCK_TIME_INTERVAL =  30
    BLOCK_TIME_SECONDS = 30

    BLOCK_TIME_INTERVAL_LOG = 1

    # количество секунд. после смены блока, перед проверками
    BLOCK_START_CHECK_PAUSE = 2

    # после закрытия блока, пауза перед созданием нового.
    # все ноды должны закрыть блок чтобы принять новый кандидат
    BLOCK_TIME_PAUSE_AFTER_CLOSE = 1

    # количество секунд перед закрытием, когда прекращаем синхронизации и проверки
    BLOCK_END_CHECK_PAUSE = 1

    # 11 2-4 в день
    KEY_BLOCK_POROG = 11

    # HALVING_INTERVAL = 1500000
    INITIAL_HALVING_INTERVAL = 1500000
    INITIAL_REWARD = 100000000
    HALVING_FACTOR = 3

    # сколько вермени ищем новые ноды перед тем как начать свою цепь если первые
    TIME_WAIN_CONNECT_TO_NODES_START = 10

    # если появилось подозрение на рассинхрон, сколько проаерять, прежде чем терять рассинхрон
    TIME_CONFIRM_LOST_SYNC = 60

    coinbase_address = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    prev_hash_genesis_block = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    # принудительно берем ноды у всех пирово
    TIME_PAUSE_GET_PEERS = 10

    TIME_PAUSE_PING_PEERS_SYNCED = 1
    TIME_PAUSE_PING_PEERS_NOT_SYNCED = 3

    hash_functions = {
        0: hashlib.sha256(),
        1: lambda: hashlib.shake_128(),  # Функция возвращает объект хеша
        2: lambda: hashlib.shake_256()  # Функция возвращает объект хеша
    }

    # по умолчанию функция хехирования
    DEFAULT_HASH_FUNCTION_CODE = 1
    DEFAULT_HEIGHT = 10

    MAX_MESSAGE_SIZE = 128

    DEFAULT_PORT = 9333

    @staticmethod
    def find_longest_common_substring(s1, s2, convert_to_sha256=False):

        if convert_to_sha256:
            s1 = hashlib.sha256(s1.encode()).hexdigest()
            s2 = hashlib.sha256(s2.encode()).hexdigest()

        match = difflib.SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
        if match.size > 0:
            return match.size, s1[match.a: match.a + match.size]
        return 0, ""

    # @staticmethod
    # def find_longest_common_substring(str1, str2, convert_to_sha256=False):
    #
    #     if convert_to_sha256:
    #         str1 = hashlib.sha256(str1.encode()).hexdigest()
    #         str2 = hashlib.sha256(str2.encode()).hexdigest()
    #
    #     len1, len2 = len(str1), len(str2)
    #     longest, start1, start2 = 0, 0, 0
    #
    #     # Таблица для хранения длин общих подстрок
    #     table = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    #
    #     # Заполнение таблицы
    #     for i in range(1, len1 + 1):
    #         for j in range(1, len2 + 1):
    #             if str1[i - 1] == str2[j - 1]:
    #                 table[i][j] = table[i - 1][j - 1] + 1
    #                 if table[i][j] > longest:
    #                     longest = table[i][j]
    #                     start1, start2 = i - longest, j - longest
    #
    #     return longest, str1[start1:start1 + longest]

    @staticmethod
    def hash_to_uuid(address):
        hash_object = hashlib.sha256(address.encode())
        hash_digest = hash_object.digest()
        short_hash = hash_digest[:16]
        return uuid.UUID(bytes=short_hash)

    @staticmethod
    def is_key_block(previousHash):  # 11 2-4 в день
        """ Определяет, является ли блок ключевым """

        count_zerro = previousHash.count("0")

        if count_zerro >= Protocol.KEY_BLOCK_POROG:
            return True

        return False

    def reward_matrix(self):
        for i in range(1, 12):
            print(i, 2 ** i)

    # @staticmethod
    # def is_reverse(str1):
    #     # Взять ASCII-код первого символа
    #     num_one = ord(str1[0])
    #     # Вернуть True, если число четное, и False, если нечетное
    #     return num_one % 2 == 0
    @staticmethod
    def is_reverse(str1):
        # Получаем SHA-256 хэш строки
        hash_bytes = hashlib.sha256(str1.encode('utf-8')).digest()
        # Суммируем все байты хэша
        total = sum(hash_bytes)
        # Возвращаем True, если сумма чётная, и False, если нечётная
        return total % 2 == 0

    def random_addres(self):
        h = hashlib.sha256(str(random.random()).encode('utf-8')).digest()
        a = base58.b58encode(h).decode('utf-8')
        return a

    @staticmethod
    def calculate_halving_factor(halvings_passed):
        """Функция для динамического уменьшения HALVING_FACTOR"""
        initial_factor = 3.0  # начальное значение фактора
        reduction_rate = 0.95  # скорость уменьшения фактора
        return initial_factor * (reduction_rate ** halvings_passed)

    @staticmethod
    def calculate_halving_interval(halvings_passed):
        """Функция для динамического увеличения интервала халвинга"""
        initial_interval = Protocol.INITIAL_HALVING_INTERVAL
        interval_growth_rate = 1.5  # скорость увеличения интервала
        return int(initial_interval * (interval_growth_rate ** halvings_passed))

    @staticmethod
    def reward(block_number, initial_reward=INITIAL_REWARD):
        halvings_passed = 0
        halving_interval = Protocol.INITIAL_HALVING_INTERVAL
        while block_number >= halving_interval:
            halvings_passed += 1
            block_number -= halving_interval
            halving_interval = Protocol.calculate_halving_interval(halvings_passed)

        halving_factor = Protocol.calculate_halving_factor(halvings_passed)
        current_reward = initial_reward / (halving_factor ** halvings_passed)
        return current_reward

    @staticmethod
    def winner(addresses, hash):
        """ Алгоритм проверки победителя адреса в хеше """
        best_address = None
        best_score = -1

        for address in addresses:

            hash_sha256 = hashlib.sha256(hash.encode()).hexdigest()
            address_sha256 = hashlib.sha256(address.encode()).hexdigest()
            ratio, lcs = Protocol.find_longest_common_substring(hash_sha256, address_sha256)
            signs = Protocol.address_max_sign(address)
            score = ratio * signs

            if score > best_score:
                best_address = address
                # best_ratio = ratio
                best_score = score
                continue

            if score == best_score:
                rev = Protocol.is_reverse(hash)
                sorted_list = sorted([best_address, address], reverse=rev)
                best_address = sorted_list[0]

        return best_address

    @staticmethod
    def address_info(address):

        try:
            # Декодирование адреса из Base58 и удаление префикса
            decoded_address = base58.b58decode(address)

            # Извлечение параметров и контрольной суммы
            key_hash = decoded_address[:-6]
            params = decoded_address[-6:-4]
            checksum = decoded_address[-4:]

            # Извлечение значений из параметров
            hash_function_code = params[0] >> 4
            tree_height = params[0] & 0x0F

            extracted_info = {
                "hash_function_code": hash_function_code,
                "tree_height": tree_height,
                "key_hash": key_hash,
                "params": params,
                "checksum": checksum
            }

            return extracted_info
        except:
            print(""" Не верный адрес """)

    @staticmethod
    def address_height(address):
        return Protocol.address_info(address)['tree_height']

    @staticmethod
    def address_max_sign(address):
        return 2 ** Protocol.address_height(address)

    @staticmethod
    def generate_random_hash():
        import os
        secret_key = os.urandom(35)
        return secret_key.hex()


def load_data():
    # Считываем список из файла
    with open('d.txt', 'r') as file:
        return [line.strip() for line in file]


def calculate_total_supply(initial_reward=50, halving_interval=210000, block_time=10, halvings_limit=None):
    """
    Рассчитывает суммарное количество монет, выплаченное в награду за блоки,
    количество halving и приблизительное количество лет до достижения этого момента.

    :param initial_reward: Начальная награда за блок (в биткоинах).
    :param halving_interval: Количество блоков между halving.
    :param block_time: Среднее время генерации одного блока (в минутах).
    :param halvings_limit: Ограничение на количество halving (если None, рассчитывается до ближайшего halving с наградой < 1 сатоши).
    :return: Словарь с суммарным количеством биткоинов, количеством halving и количеством лет до достижения этого момента.
    """
    total_supply = 0
    current_reward = initial_reward
    halvings = 0
    blocks_per_year = (365.25 * 24 * 60) / block_time  # Переводим время в года

    while current_reward >= 0.00000001:
        # Добавляем награду за текущий период
        total_supply += halving_interval * current_reward
        # Уменьшаем награду вдвое
        current_reward /= 2
        halvings += 1
        if halvings_limit and halvings >= halvings_limit:
            break

    years_until_limit = (halving_interval * halvings) / blocks_per_year

    return {

        "total_supply_int": int(total_supply) + 1,
        "total_supply": total_supply,
        "halvings": halvings,
        "years_until_limit": years_until_limit,
        "blocks": blocks_per_year * years_until_limit
    }


def calculate_mined_coins(period_in_years, initial_reward=100, halving_interval=210000, block_time=10, porog=9):
    blocks_per_year = (365.25 * 24 * 60) / block_time
    total_blocks = int(blocks_per_year * period_in_years)

    # Предполагаем минимальное и максимальное значения ratio1 для расчета
    min_ratio, max_ratio = 0.1, 1.0  # Примерные пределы для ratio1

    min_coins, max_coins = 0, 0
    for block_number in range(1, total_blocks + 1):
        halvings_passed = block_number // halving_interval
        current_reward = initial_reward / (2 ** halvings_passed)

        # Минимальная и максимальная возможная награда за блок
        min_reward = (current_reward ** min_ratio)
        max_reward = (current_reward ** max_ratio)

        min_coins += min_reward
        max_coins += max_reward

    return min_coins, max_coins


def calculate_rewards(protocol, max_blocks):
    rewards = []
    times = []
    current_reward = protocol.INITIAL_REWARD
    block_number = 0
    while current_reward >= 1 and block_number <= max_blocks:
        current_reward = protocol.reward(block_number)
        rewards.append(current_reward / 10000000)  # переводим в монеты
        times.append(block_number * protocol.BLOCK_TIME_SECONDS / 60 / 60 / 24 / 365.25)  # переводим в годы
        block_number += 1
    return rewards, times


def plot_rewards(times, rewards):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 6))
    plt.plot(times, rewards, label="Block Reward")
    plt.xlabel("Time (years)")
    plt.ylabel("Reward (coins)")
    plt.title("Block Reward Over Time")
    plt.yscale('log')
    plt.grid(True)
    plt.legend()
    plt.show()


def calculate_total_supply_and_duration(protocol):
    total_supply = 0
    current_reward = protocol.INITIAL_REWARD
    block_number = 0
    while current_reward >= 1:
        current_reward = protocol.reward(block_number)
        total_supply += current_reward
        block_number += 1

    total_supply_coins = total_supply / 10000000  # переводим в монеты
    total_time_years = block_number * protocol.BLOCK_TIME_SECONDS / 60 / 60 / 24 / 365.25  # переводим в годы

    return total_supply_coins, total_time_years


if __name__ == '__main__':
    # protocol = Protocol()
    # max_blocks = 10000000  # ограничение на количество блоков для расчетов и графика
    # rewards, times = calculate_rewards(protocol, max_blocks)
    # print(sum(rewards))
    # plot_rewards(times, rewards)
    #
    # total_supply, total_time_years = calculate_total_supply_and_duration(protocol)
    # print(f"Total supply of coins: {total_supply}")
    # print(f"Total time to distribute all rewards: {total_time_years} years")

    # Инициализация протокола и адресов
    import secrets
    import time

    # Функция для генерации случайного previous_hash с большей энтропией
    # def generate_random_hash():
    #     random_data = secrets.token_hex(32)
    #     current_time = str(time.time())
    #     extra_random_data = secrets.token_hex(32)
    #     combined_data = random_data + current_time + extra_random_data
    #     return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()
    # def generate_random_hash():
    #     # Генерация случайных данных с использованием более высокой энтропии
    #     random_data = secrets.token_hex(32)
    #
    #     # Получение текущего времени в миллисекундах для увеличения чувствительности к времени
    #     current_time = str(int(time.time() * 1000))
    #
    #     # Дополнительная случайная порция данных
    #     extra_random_data = secrets.token_hex(32)
    #
    #     # Включение других изменяющихся во времени параметров, таких как показания процессорного времени
    #     cpu_time = str(time.process_time())
    #
    #     # Комбинирование всех данных в одну строку
    #     combined_data = random_data + current_time + extra_random_data + cpu_time
    #
    #     # Генерация хеша с использованием SHA-256
    #     return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()
    import hashlib
    import secrets
    import time

    # def generate_random_hash():
    #     random_data = secrets.token_hex(32)
    #     current_time = str(int(time.time() * 1000))
    #     extra_random_data = secrets.token_hex(32)
    #     cpu_time = str(time.process_time())
    #
    #     combined_data = random_data + current_time + extra_random_data + cpu_time
    #
    #     # Использование BLAKE2b вместо SHA-256
    #     hash_object = hashlib.blake2b()
    #     hash_object.update(combined_data.encode('utf-8'))
    #     return hash_object.hexdigest()

    # # Проверка распределения длин подстрок
    # d = {}
    # import os
    #
    # # a = hashlib.sha256("bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm".encode()).hexdigest()
    # # a = hashlib.sha256(os.urandom(35)).hexdigest()
    # random_data = os.urandom(35)
    # a = random_data.hex()
    #
    # for i in range(100000):
    #     random_data = os.urandom(35)
    #     sequence = random_data.hex()
    #     # sequence = hashlib.sha256(random_data).hexdigest()
    #     # print(sequence, a)
    #
    #     r = Protocol.find_longest_common_substring(sequence, a)
    #     d[r[0]] = d.get(r[0], 0) + 1
    #
    # print(d)

    # Инициализация протокола и адресов
    protocol = Protocol()


    def load_addresses_from_file(file_path):
        addresses = []
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split('::')
                if len(parts) > 5:
                    address = parts[5]
                    addresses.append(address)
        return addresses


    addresses = [
        # "bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm",
        # "Runsb7FX8Qzr3SBxzWmBpNJD3sG2HCSxLHgbXEfiUTPiGLEfbQsZ",
        # "YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA",
        # "URRisTVxmH5wwkexcZChHHEaCSrNLJ4bXk2r87ZuYRwVgssfLnQJ",
        # "V1Pp6Hd4uUs8iwT7LWEEzFFUEiGfLwBXZUKuAP4a8MP78axPTVsK",
        # "AKMxvU7oJPWraHpaMxiYebN6eZn92DJNSqmQEGxzkB7m2b25okMh"
        "eY2CA5THMANYswNykf1bfr1K4Jp5XeTq84c7LzWnFadD7VBmLAtG",
        "2A1XVJgNT53C9c7JKUfHjbZtEQDk89fWd2cL3Ro3BNX2QG7crX2b",
        "aJPVhagraL3uUwWyACkFzhHkPPDTGWyDJ7MUJKxQwfZqEkQXqvUW",
        # "3ebP9Wnm6RykLYoxJe57m2mGccGx9KWc2AZMHEmauWp8iFWBf5DG",

        # "e8bicWZaUzBGFPQkK3upJ7ARnf588fT2Ku4e3frpv7r65mywwshg",
        # "3AohH1miXFM9hNwy22p3ZB6AFieTEM2WCfFsDXjPxJ29yinmDeD6",
        # "N4Gx2KqPiSjRJF8hYFCLYu7magw8qNULyMn31PPaZawc7EPgkkZQ",
        # "Kche7UTznvL5xX1pav9kVUG4Tac5zzP2H2tibWozWjDKSGgqgP37",
    ]

    addresses = load_addresses_from_file(r"C:\FlukyCoin\tests\logs\KEYS_2024-06-19.log")

    # addresses = addresses[:100]
    # Инициализация предыдущего хэша и счётчиков очков для адресов

    scores = {address: 0 for address in addresses}
    match_lengths = {address: [] for address in addresses}
    substring_freq = {address: {i: 0 for i in range(1, 11)} for address in
                      addresses}  # Частоты длин совпадающих подстрок

    # Количество тестов
    num_tests = 100

    # previous_hash = Protocol.generate_random_hash()  # обновляем предыдущий хэш для следующего цикла

    # Выполнение тестов
    for _ in range(num_tests):
        previous_hash = Protocol.generate_random_hash()  # обновляем предыдущий хэш для следующего цикла
        random.shuffle(addresses)
        # addresses = [hashlib.sha256(a.encode()).hexdigest() for a in addresses]

        winner_address = protocol.winner(addresses, previous_hash)
        scores[winner_address] += 1

        # Запись длины совпадающей подстроки
        for address in addresses:
            ratio, lcs = protocol.find_longest_common_substring(previous_hash, address.lower())
            # ratio, lcs = protocol.find_longest_common_substring(sequence, address.lower())
            match_lengths[address].append(ratio)
            substring_freq[address][ratio] += 1

    # Вывод результатов по убыванию
    print("Результаты тестирования:")
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for address, score in sorted_scores:
        print(f"Адрес: {address}, Очки: {score}", ''.join(sorted(address)))

    # Анализ длины совпадающих подстрок
    print("\nДлина совпадающих подстрок:")
    for address, lengths in match_lengths.items():
        avg_length = sum(lengths) / len(lengths)
        print(f"Адрес: {address}, Средняя длина совпадающей подстроки: {avg_length:.2f}")

    # Вывод информации о каждом адресе
    # print("\nИнформация о каждом адресе:")
    # for address in addresses:
    #     info = protocol.address_info(address)
    #     if info:
    #         print(f"Адрес: {address}, Информация: {info}")

    # # Вывод частот длин совпадающих подстрок
    # print("\nЧастоты длин совпадающих подстрок:")
    # for address, freqs in substring_freq.items():
    #     print(f"\nАдрес: {address}")
    #     for length, count in freqs.items():
    #         print(f"Длина: {length}, Частота: {count}")
