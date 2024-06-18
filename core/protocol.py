import difflib
import random
import hashlib
import base58
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
    def find_longest_common_substring(s1, s2):
        match = difflib.SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
        if match.size > 0:
            return match.size, s1[match.a: match.a + match.size]
        return 0, ""

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
    @staticmethod
    def sequence(prevHash):
        return base58.b58encode(prevHash).decode('utf-8').lower()

    # def reward(self, addrr, sequence):
    #     ratio1, lcs = self.find_longest_common_substring(sequence, addrr.lower())
    #
    #     return ratio1 * ratio1 * 10, ratio1, lcs

    # @staticmethod
    # def reward(addrr, sequence, block_number=0, initial_reward=3000000, halving_interval=1500000):
    #     ratio1, lcs = Protocol.find_longest_common_substring(sequence, addrr.lower())
    #
    #     # Определение количества прошедших халфингов
    #     halvings_passed = block_number // halving_interval
    #
    #     # Учёт уменьшения награды из-за халфингов
    #     current_reward = initial_reward / (2 ** halvings_passed)
    #
    #     # Умножаем текущую награду на коэффициент, полученный из ratio1
    #     # reward = (ratio1 ** 3) * current_reward
    #     # reward = (current_reward ** ratio1)/100000000
    #
    #     # reward = int(current_reward * ratio1 ** 3)
    #
    #     # # Применяем функцию с дополнительной нелинейностью для более сильного различия в наградах
    #     adjusted_ratio = (ratio1 ** 2) * math.log(1 + ratio1 * 100)
    #     #
    #     # # Умножаем текущую награду на скорректированный коэффициент
    #     reward = int(current_reward * adjusted_ratio)
    #
    #     # Округление награды до миллиона
    #     reward = round(reward, -6)
    #
    #     return reward, ratio1, lcs
    #
    # def winner(self, a1, a2, sequence):
    #     """ Проверка выигрышного адреса """
    #     sequence = sequence.lower()
    #     ratio1, lcs = self.find_longest_common_substring(sequence, a1.lower())
    #     ratio2, lcs = self.find_longest_common_substring(sequence, a2.lower())
    #
    #     if ratio1 > ratio2:
    #         # print("win",a1, "loose", a2, "sec", sequence)
    #         return a1
    #
    #     if ratio1 < ratio2:
    #         # print("win", a2, "loose", a1, "sec", sequence)
    #         return a2
    #
    #     rev = self.is_reverse(sequence)
    #
    #     sorted_list = sorted([a1, a2], reverse=rev)
    #     winer = sorted_list[0]
    #     # print("win", winer, "loose", sorted_list[1], "sec", sequence)
    #     return winer

    def random_addres(self):
        h = hashlib.sha256(str(random.random()).encode('utf-8')).digest()
        a = base58.b58encode(h).decode('utf-8')
        return a

    @staticmethod
    # def reward(block_number, initial_reward=100000000, halving_interval=5000000):
    #     halvings_passed = block_number // halving_interval
    #     current_reward = initial_reward / (2 ** halvings_passed)
    #     return current_reward

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
    # def winner(self, addresses, sequence):
    #     sequence = sequence.lower()
    #     best_address = None
    #     best_ratio = -1
    #     best_signs = -1
    #
    #     for address in addresses:
    #         ratio, lcs = self.find_longest_common_substring(sequence, address.lower())
    #         signs = self.address_max_sign(address)
    #
    #         if ratio > best_ratio or (ratio == best_ratio and signs > best_signs):
    #             best_address = address
    #             best_ratio = ratio
    #             best_signs = signs
    #             continue
    #
    #         if ratio==best_ratio and signs==best_signs:
    #             # при одинаковых данных выбираем первого по сортировке
    #             rev = self.is_reverse(sequence)
    #             sorted_list = sorted([best_address, address], reverse=rev)
    #             best_address = sorted_list[0]
    #
    #
    #     if best_address:
    #         return best_address
    #
    #
    #
    #     sorted_list = sorted(addresses, reverse=rev)
    #     winer = sorted_list[0]
    #     return winer

    def winner(self, addresses, sequence):
        sequence = sequence.lower()
        best_address = None
        best_ratio = -1
        best_score = -1

        # Добавление детального логирования
        detailed_scores = {}

        for address in addresses:
            ratio, lcs = self.find_longest_common_substring(sequence, address.lower())
            signs = self.address_max_sign(address)
            score = ratio * signs  # Комбинированный скор с учетом подписей

            # Логирование результатов для каждого адреса
            detailed_scores[address] = {'ratio': ratio, 'lcs': lcs, 'score': score}

            if score > best_score:
                best_address = address
                best_ratio = ratio
                best_score = score
                continue

            if score == best_score:
                rev = self.is_reverse(sequence)
                sorted_list = sorted([best_address, address], reverse=rev)
                best_address = sorted_list[0]

        # Вывод логирования для анализа
        print("Detailed scores for each address:")
        for addr, details in detailed_scores.items():
            print(f"Address: {addr}, Score: {details['score']}, Ratio: {details['ratio']}, LCS: {details['lcs']}")

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
    def generate_random_hash():
        random_data = secrets.token_hex(32)
        current_time = str(time.time())
        extra_random_data = secrets.token_hex(32)
        combined_data = random_data + current_time + extra_random_data
        return hashlib.sha256(combined_data.encode('utf-8')).hexdigest()


    # Инициализация протокола и адресов
    protocol = Protocol()

    addresses = [
        "bosGxTY8XcWKvR54PM8DVGzu5kz1fTSfEZPxXHybugmjZrNYjAWm",
        "Runsb7FX8Qzr3SBxzWmBpNJD3sG2HCSxLHgbXEfiUTPiGLEfbQsZ",
        "YGPieNA3cqvCKSKm8NkR2oE6gCLf4pkNaie3g1Kmc2Siiprh3cjA",
        "URRisTVxmH5wwkexcZChHHEaCSrNLJ4bXk2r87ZuYRwVgssfLnQJ",
        "V1Pp6Hd4uUs8iwT7LWEEzFFUEiGfLwBXZUKuAP4a8MP78axPTVsK",
        "AKMxvU7oJPWraHpaMxiYebN6eZn92DJNSqmQEGxzkB7m2b25okMh"
    ]

    # Инициализация предыдущего хэша и счётчиков очков для адресов
    previous_hash = generate_random_hash()
    scores = {address: 0 for address in addresses}
    match_lengths = {address: [] for address in addresses}
    substring_freq = {address: {i: 0 for i in range(1, 11)} for address in
                      addresses}  # Частоты длин совпадающих подстрок

    # Количество тестов
    num_tests = 10000

    # Выполнение тестов
    for _ in range(num_tests):

        random.shuffle(addresses)

        sequence = protocol.sequence(previous_hash)
        winner_address = protocol.winner(addresses, sequence)
        scores[winner_address] += 1
        previous_hash = generate_random_hash()  # обновляем предыдущий хэш для следующего цикла

        # Запись длины совпадающей подстроки
        for address in addresses:
            ratio, lcs = protocol.find_longest_common_substring(sequence, address.lower())
            match_lengths[address].append(ratio)
            substring_freq[address][ratio] += 1

    # Вывод результатов
    print("Результаты тестирования:")
    for address, score in scores.items():
        print(f"Адрес: {address}, Очки: {score}")

    # Анализ длины совпадающих подстрок
    print("\nДлина совпадающих подстрок:")
    for address, lengths in match_lengths.items():
        avg_length = sum(lengths) / len(lengths)
        print(f"Адрес: {address}, Средняя длина совпадающей подстроки: {avg_length:.2f}")

    # Вывод информации о каждом адресе
    print("\nИнформация о каждом адресе:")
    for address in addresses:
        info = protocol.address_info(address)
        if info:
            print(f"Адрес: {address}, Информация: {info}")

    # Вывод частот длин совпадающих подстрок
    print("\nЧастоты длин совпадающих подстрок:")
    for address, freqs in substring_freq.items():
        print(f"\nАдрес: {address}")
        for length, count in freqs.items():
            print(f"Длина: {length}, Частота: {count}")