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

    BLOCK_TIME_INTERVAL = 30
    BLOCK_TIME_INTERVAL_LOG = BLOCK_TIME_INTERVAL / 4

    # 11 2-4 в день
    KEY_BLOCK_POROG = 11

    # если появилось подозрение на рассинхрон, сколько проаерять, прежде чем терять рассинхрон
    TIME_CONFIRM_LOST_SYNC = 60

    coinbase_address = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    prev_hash_genesis_block = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    hash_functions = {
        0: hashlib.sha256(),
        1: lambda: hashlib.shake_128(),  # Функция возвращает объект хеша
        2: lambda: hashlib.shake_256()  # Функция возвращает объект хеша
    }

    # по умолчанию функция хехирования
    DEFAULT_HASH_FUNCTION_CODE = 1
    DEFAULT_HEIGHT = 10
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

    @staticmethod
    def is_reverse(str1):
        # Взять ASCII-код первого символа каждой строки и сложить их
        # sum_of_codes = ord(str1[0]) + ord(str2[0])
        sum_of_codes = ord(str1[0])
        # Вернуть True, если сумма четная, и False, если нечетная
        return sum_of_codes % 2 == 0

    @staticmethod
    def sequence(prevHash):
        return base58.b58encode(prevHash).decode('utf-8').lower()

    # def reward(self, addrr, sequence):
    #     ratio1, lcs = self.find_longest_common_substring(sequence, addrr.lower())
    #
    #     return ratio1 * ratio1 * 10, ratio1, lcs

    @staticmethod
    def reward(addrr, sequence, block_number=0, initial_reward=3000000, halving_interval=1500000):
        ratio1, lcs = Protocol.find_longest_common_substring(sequence, addrr.lower())

        # Определение количества прошедших халфингов
        halvings_passed = block_number // halving_interval

        # Учёт уменьшения награды из-за халфингов
        current_reward = initial_reward / (2 ** halvings_passed)

        # Умножаем текущую награду на коэффициент, полученный из ratio1
        # reward = (ratio1 ** 3) * current_reward
        # reward = (current_reward ** ratio1)/100000000

        # reward = int(current_reward * ratio1 ** 3)

        # # Применяем функцию с дополнительной нелинейностью для более сильного различия в наградах
        adjusted_ratio = (ratio1 ** 2) * math.log(1 + ratio1 * 100)
        #
        # # Умножаем текущую награду на скорректированный коэффициент
        reward = int(current_reward * adjusted_ratio)

        # Округление награды до ближайшего миллиона
        reward = round(reward / 1000000) * 1000000

        return reward, ratio1, lcs

    def winner(self, a1, a2, sequence):
        """ Проверка выигрышного адреса """
        sequence = sequence.lower()
        ratio1, lcs = self.find_longest_common_substring(sequence, a1.lower())
        ratio2, lcs = self.find_longest_common_substring(sequence, a2.lower())

        if ratio1 > ratio2:
            # print("win",a1, "loose", a2, "sec", sequence)
            return a1

        if ratio1 < ratio2:
            # print("win", a2, "loose", a1, "sec", sequence)
            return a2

        rev = self.is_reverse(sequence)

        sorted_list = sorted([a1, a2], reverse=rev)
        winer = sorted_list[0]
        # print("win", winer, "loose", sorted_list[1], "sec", sequence)
        return winer

    def random_addres(self):
        h = hashlib.sha256(str(random.random()).encode('utf-8')).digest()
        a = base58.b58encode(h).decode('utf-8')
        return a


# def generate_data():
#
#     for a in range(10000):
#         h = hashlib.sha256(str(a).encode('utf-8')).digest()
#         a = base58.b58encode(h).decode('utf-8')
#         data.append(a)
#
#     # Записываем список в файл
#     with open('d.txt', 'w') as file:
#         for item in data:
#             file.write('%s\n' % item)
#
#     return data

def load_data():
    # Считываем список из файла
    with open('d.txt', 'r') as file:
        return [line.strip() for line in file]


def calculate_total_supply(initial_reward=50, halving_interval=210000, block_time=10, halvings_limit=None):
    """
    Рассчитывает суммарное количество биткоинов, выплаченное в награду за блоки,
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

    while current_reward >= 0.00000001:  # 1 сатоши
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


if __name__ == '__main__':

    # Пример: Расчет за 4 года
    # min_coins, max_coins = calculate_mined_coins(1)
    # print(f"Минимальное количество монет, намайненных: {min_coins}")
    # print(f"Максимальное количество монет, намайненных: {max_coins}")
    #
    # exit()

    r = calculate_total_supply(initial_reward=4, block_time=1, halving_interval=2600000)
    print(r)

    p = Protocol()
    # p.reward_matrix()

    # вероятности ключевого блока
    res = {}
    b = 0
    max_try = 14400
    for i in range(max_try):
        h = hashlib.sha256(str(random.random()).encode('utf-8'))
        sec = h.hexdigest()

        c = sec.count("0")

        if c >= 11:
            b += 1
        res[c] = res.get(c, 0) + 1

    res = sorted(res.items(), key=lambda x: x[1])
    # for x, y in res:
    #     print(x, y)
    print(b / 10, b / max_try)
    # print(res)
