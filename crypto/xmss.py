# from WOTS import *
import datetime
from typing import List
import json
import base58
import base64
import struct
import pickle
import zlib
from random import choice, seed, randint
from string import ascii_letters, digits
from hashlib import sha256
import hashlib
from math import floor, log2, log, ceil
# from WOTS import *
import datetime
from typing import List
import json
import base58
import base64
import struct
import pickle
import zlib
from random import choice, seed, randint
from string import ascii_letters, digits
from hashlib import sha256
from math import floor, log2, log, ceil


class XMSSPrivateKey:

    def __init__(self):
        self.wots_private_keys = None
        self.idx = None
        self.SK_PRF = None
        self.root_value = None
        self.SEED = None

class XMSSPublicKey:

    def __init__(self, OID=None, root_value=None, SEED=None, height = 4, n = 4, w = 32):
        self.OID = OID
        self.root_value = root_value
        self.SEED = SEED

        self.heigh = height
        self.n = n
        self.w = w


    def generate_address(self):
        # Конкатенация строковых представлений ключевых компонентов
        # key_data = str(self.OID) + str(self.root_value) + str(self.SEED)
        key_data = str(self.OID) + str(self.root_value)

        # Генерация хеша из данных ключа
        key_hash = hashlib.sha256(key_data.encode('utf-8')).digest()

        # Применение кодирования Base58Check к хэшу
        # Генерация контрольной суммы из хеша хеша
        checksum = hashlib.sha256(hashlib.sha256(key_hash).digest()).digest()[:4]

        # Конкатенация хеша и контрольной суммы
        full_key = key_hash + checksum

        # Применение кодирования Base58 к полному ключу
        address = base58.b58encode(full_key).decode('utf-8')

        # Применение кодирования Base64 к хэшу
        # address = base64.urlsafe_b64encode(key_hash).decode('utf-8').rstrip('=')

        # Возврат адреса в кодировке Base58
        return f"Out{address}"

    @staticmethod
    def is_valid_address(address):
        """
        Проверяет, действителен ли криптовалютный адрес.

        :param address: Адрес для проверки, закодированный в Base58.
        :return: True, если адрес действителен; False в противном случае.
        """
        try:
            # Декодирование адреса из Base58
            # Убираем первые 3 байта как название
            decoded_address = base58.b58decode(address[3:])

            # Отделение контрольной суммы от остальной части адреса
            main_part = decoded_address[:-4]
            checksum = decoded_address[-4:]

            # Повторное вычисление контрольной суммы для основной части адреса
            calculated_checksum = hashlib.sha256(hashlib.sha256(main_part).digest()).digest()[:4]

            # Сравнение рассчитанной контрольной суммы с контрольной суммой в адресе
            return checksum == calculated_checksum
        except Exception as e:
            # В случае ошибок декодирования или других исключений адрес считается недействительным
            return False

    def to_json(self):
        return {
            'OID': self.OID,
            'root_value': self.root_value.hex(),
            'SEED': self.SEED
        }
    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self))

    @staticmethod
    def from_bytes(bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

    # def to_bytes(self):
    #     # Кодируем OID и SEED в байты
    #     oid_bytes = self.OID.encode('utf-8') if self.OID is not None else b''
    #     seed_bytes = self.SEED.encode('utf-8') if self.SEED is not None else b''
    #
    #     # Сериализуем данные с указанием длины каждой части
    #     return bytes([len(oid_bytes)]) + oid_bytes + bytes([len(self.root_value)]) + self.root_value + bytes(
    #         [len(seed_bytes)]) + seed_bytes
    #
    # @classmethod
    # def from_bytes(cls, bytes_data):
    #     # Десериализуем OID
    #     oid_length = bytes_data[0]
    #     oid = bytes_data[1:1 + oid_length].decode('utf-8')
    #
    #     # Десериализуем root_value
    #     root_value_start = 1 + oid_length
    #     root_value_length = bytes_data[root_value_start]
    #     root_value = bytes_data[root_value_start + 1:root_value_start + 1 + root_value_length]
    #
    #     # Десериализуем SEED
    #     seed_start = root_value_start + 1 + root_value_length
    #     seed_length = bytes_data[seed_start]
    #     SEED = bytes_data[seed_start + 1:seed_start + 1 + seed_length].decode('utf-8')
    #
    #     return cls(OID=oid, root_value=root_value, SEED=SEED)

    @classmethod
    def from_json(cls, json_data):
        OID = json_data.get('OID')
        root_value_hex = json_data.get('root_value')
        SEED_hex = json_data.get('SEED')

        root_value = bytes.fromhex(root_value_hex) if root_value_hex else None
        SEED = bytes.fromhex(SEED_hex) if SEED_hex else None

        return cls(OID=OID, root_value=root_value, SEED=SEED)

class XMSSKeypair:

    def __init__(self, SK, PK, height = 4, n = 4, w = 32):
        self.SK = SK
        self.PK = PK
        self.height =height
        self.n =n
        self.w =w

class SigXMSS:
    def __init__(self, idx_sig, r, sig_ots, auth):
        self.idx_sig = idx_sig
        self.r = r
        self.sig_ots = sig_ots
        self.auth = auth

    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self))

    @staticmethod
    def from_bytes(bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

class SigWithAuthPath:
    def __init__(self, sig_ots, auth):
        self.sig_ots = sig_ots
        self.auth = auth


class ADRS:

    def __init__(self):
        self.layerAddress = bytes(4)
        self.treeAddress = bytes(8)
        self.type = bytes(4)

        self.first_word = bytes(4)
        self.second_word = bytes(4)
        self.third_word = bytes(4)

        self.keyAndMask = bytes(4)

    def setType(self, type_value):
        self.type = type_value.to_bytes(4, byteorder='big')
        self.first_word = bytearray(4)
        self.second_word = bytearray(4)
        self.third_word = bytearray(4)
        self.keyAndMask = bytearray(4)

    def getTreeHeight(self):
        return self.second_word

    def getTreeIndex(self):
        return self.third_word

    def setHashAddress(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setKeyAndMask(self, value):
        self.keyAndMask = value.to_bytes(4, byteorder='big')

    def setChainAddress(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeHeight(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeIndex(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setOTSAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLTreeAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLayerAddress(self, value):
        self.layerAddress = value.to_bytes(4, byteorder='big')

    def setTreeAddress(self, value):
        self.treeAddress = value.to_bytes(4, byteorder='big')


def WOTS_genSK(length, n):
    secret_key = [bytes()] * length

    for i in range(length):
        SEED = generate_random_value(length)

        secret_key[i] = pseudorandom_function(SEED, n)

    return secret_key

import random
def WOTS_genSK_from_seed(length, n, seed):
    # Инициализация генератора случайных чисел с использованием сида
    random.seed(seed)

    secret_key = []
    for _ in range(length):
        # Генерация элемента секретного ключа
        random_bytes = random.getrandbits(n * 8).to_bytes(n, 'big')
        secret_key.append(random_bytes)

    return secret_key

def WOTS_genPK(private_key: [bytes], length: int, w: int in {4, 16}, SEED, address):
    public_key = [bytes()] * length
    for i in range(length):
        address.setChainAddress(i)
        public_key[i] = chain(private_key[i], 0, w - 1, SEED, address, w)

    return public_key


def WOTS_sign(message: bytes, private_key: [bytes], w: int in {4, 16}, SEED, address):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    signature = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        signature[i] = chain(private_key[i], 0, msg[i], SEED, address, w)

    return signature


def WOTS_pkFromSig(message: bytes, signature: [bytes], w: int in {4, 16}, address, SEED):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    tmp_pk = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        tmp_pk[i] = chain(signature[i], msg[i], w - 1 - msg[i], SEED, address, w)

    return tmp_pk




def base_w(byte_string: bytes, w: int in {4, 16}, out_len):
    in_ = 0
    total_ = 0
    bits_ = 0
    base_w_ = []

    for i in range(0, out_len):
        if bits_ == 0:
            total_ = byte_string[in_]
            in_ += 1
            bits_ += 8

        bits_ -= log2(w)
        base_w_.append((total_ >> int(bits_)) & (w - 1))
    return base_w_


def generate_random_value(n, seed_value=None):
    # Инициализация генератора случайных чисел с заданным сидом
    seed(seed_value)

    alphabet = ascii_letters + digits
    value = ''.join(choice(alphabet) for _ in range(n))

    return value

def compute_needed_bytes(n):
    if n == 0:
        return 1
    return int(log(n, 256)) + 1


def compute_lengths(n: int, w: int in {4, 16}):
    len_1 = ceil(8 * n / log2(w))
    len_2 = floor(log2(len_1 * (w - 1)) / log2(w)) + 1
    len_all = len_1 + len_2
    return len_1, len_2, len_all


def to_byte(value, bytes_count):
    # Преобразование целого числа в bytes
    return value.to_bytes(bytes_count, byteorder='big')

def xor(one: bytearray, two: bytearray) -> bytearray:
    return bytearray(a ^ b for (a, b) in zip(one, two))


def int_to_bytes(val, count):
    byteVal = to_byte(val, count)
    acc = bytearray()
    for i in range(len(byteVal)):
        if byteVal[i] < 16:
            acc.extend(b'0')
        curr = hex(byteVal[i])[2:]
        acc.extend(curr.encode())
    return acc


def F(KEY, M):
    key_len = len(KEY)
    toBytes = to_byte(0, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def chain(X, i, s, SEED, address, w):

    if s == 0:
        return X
    if (i + s) > (w - 1):
        return None
    tmp = chain(X, i, s - 1, SEED, address, w)

    address.setHashAddress((i + s - 1))
    address.setKeyAndMask(0)
    KEY = PRF(SEED, address)
    address.setKeyAndMask(1)
    BM = PRF(SEED, address)
    tmp = F(KEY, xor(tmp, BM))
    return tmp


def PRF(KEY: str, M: ADRS) -> bytearray:
    toBytes = to_byte(3, 4)
    key_len = len(KEY)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M.keyAndMask).hexdigest()[:key_len*2]
    out = bytearray()
    out.extend(map(ord, help_))
    return out



def H(KEY: bytearray, M: bytearray) -> bytearray:
    key_len = len(KEY)
    toBytes = to_byte(1, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def PRF_XMSS(KEY: str, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(3, 4)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def H_msg(KEY: bytearray, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(2, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def RAND_HASH(left: bytearray, right: bytearray, SEED: str, adrs: ADRS):
    adrs.setKeyAndMask(0)
    KEY = PRF(SEED, adrs)
    adrs.setKeyAndMask(1)
    BM_0 = PRF(SEED, adrs)
    adrs.setKeyAndMask(2)
    BM_1 = PRF(SEED, adrs)

    return H(KEY, xor(left, BM_0) + xor(right, BM_1))

def pseudorandom_function(seed, n):
    # Создаем хеш из сида, предполагая, что seed является строкой.
    seed_bytes = seed.encode('utf-8')  # Преобразуем строку сида в байты
    hash_digest = hashlib.sha256(seed_bytes).digest()  # Создаем хеш SHA-256 от сида

    # Обрезаем или дополняем хеш до нужной длины n, возвращаем как bytearray
    return bytearray(hash_digest)[:n]


def ltree(pk: List[bytearray], address: ADRS, SEED: str, length: int) -> bytearray:

    address.setTreeHeight(0)

    while length > 1:
        for i in range(floor(length / 2)):
            address.setTreeIndex(i)
            pk[i] = RAND_HASH(pk[2 * i], pk[2 * i + 1], SEED, address)

        if length % 2 == 1:
            pk[floor(length / 2)] = pk[length - 1]

        length = ceil(length / 2)
        height = address.getTreeHeight()
        height = int.from_bytes(height, byteorder='big')
        address.setTreeHeight(height + 1)

    return pk[0]


def treeHash(SK: XMSSPrivateKey, s: int, t: int, address: ADRS, w: int in {4, 16}, length_all: int) -> bytearray:

    class StackElement:
        def __init__(self, node_value=None, height=None):
            self.node_value = node_value
            self.height = height

    Stack = []

    if s % (1 << t) != 0:
        raise ValueError("should be s % (1 << t) != 0")

    for i in range(0, int(pow(2, t))):
        SEED = SK.SEED
        address.setType(0)
        address.setOTSAddress(s + i)
        pk = WOTS_genPK(SK.wots_private_keys[s + i], length_all, w, SEED, address)
        address.setType(1)
        address.setLTreeAddress(s + i)
        node = ltree(pk, address, SEED, length_all)

        node_as_stack_element = StackElement(node, 0)

        address.setType(2)
        address.setTreeHeight(0)
        address.setTreeIndex(i + s)

        while len(Stack) != 0 and Stack[len(Stack) - 1].height == node_as_stack_element.height:
            address.setTreeIndex(int((int.from_bytes(address.getTreeHeight(), byteorder='big') - 1) / 2))

            previous_height = node_as_stack_element.height

            node = RAND_HASH(Stack.pop().node_value, node_as_stack_element.node_value, SEED, address)

            node_as_stack_element = StackElement(node, previous_height + 1)

            address.setTreeHeight(int.from_bytes(address.getTreeHeight(), byteorder='big') + 1)

        Stack.append(node_as_stack_element)

    return Stack.pop().node_value





def XMSS_keyGen(height: int, n: int, w: int in {4, 16}) -> XMSSKeypair:

    len_1, len_2, len_all = compute_lengths(n, w)

    wots_sk = []
    for i in range(0, 2 ** height):
        wots_sk.append(WOTS_genSK(len_all, n))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value(n)
    SEED = generate_random_value(n)
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    root = treeHash(SK, 0, height, adrs, w, len_all)

    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n)
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK)
    return KeyPair

def XMSS_keyGen_from_seed(seed: str, height: int, n: int, w: int) -> XMSSKeypair:
    len_1, len_2, len_all = compute_lengths(n, w)
    wots_sk = []

    # Изменяем генерацию WOTS ключей, используя уникальный сид для каждого ключа
    for i in range(0, 2 ** height):
        unique_seed = pseudorandom_function(seed + str(i), n)  # Генерация уникального сида для каждого ключа
        wots_sk.append(WOTS_genSK_from_seed(len_all, n, unique_seed))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value( n, seed + "SK_PRF")  # Генерация SK_PRF на основе сида
    SEED = generate_random_value(n, seed + "SEED")  # Генерация SEED на основе сида
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    # Генерация корня дерева
    root = treeHash(SK, 0, height, adrs, w, len_all)
    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n, seed + "OID")  # Генерация OID на основе сида
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK, height, n, w)
    return KeyPair

def buildAuth(SK: XMSSPrivateKey, index: int, address: ADRS, w: int in {4, 16}, length_all: int, h: int) -> List[bytearray]:
    auth = []

    for j in range(h):
        k = floor(index / (2 ** j)) ^ 1
        auth.append(treeHash(SK, k * (2 ** j), j, address, w, length_all))
    return auth


def treeSig(message: bytearray, SK: XMSSPrivateKey, address: ADRS, w: int in {4, 16}, length_all: int, idx_sig: int, h: int) -> SigWithAuthPath:
    auth = buildAuth(SK, idx_sig, address, w, length_all, h)
    address.setType(0)
    address.setOTSAddress(idx_sig)
    sig_ots = WOTS_sign(message, SK.wots_private_keys[idx_sig], w, SK.SEED, address)
    Sig = SigWithAuthPath(sig_ots, auth)
    return Sig

def XMSS_sign(message: bytearray, SK: XMSSPrivateKey, n, w: int, address: ADRS, h: int) -> SigXMSS:
    len_1, len_2, length_all = compute_lengths(n, w)
    idx_sig = SK.idx
    SK.idx += 1  # Инкрементируем индекс после использования

    # Генерация случайного значения на основе секретного ключа и индекса подписи
    r = PRF_XMSS(SK.SK_PRF, to_byte(idx_sig, 4), len_1)

    # Создание расширенного представления подписи с добавлением r и root_value
    arrayOfBytes = bytearray(r)
    arrayOfBytes.extend(SK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(idx_sig, n)))

    # Генерация вторичного хеша сообщения
    M2 = H_msg(arrayOfBytes, message, len_1)

    # Получение одноразовой подписи и аутентификационного пути
    sig = treeSig(M2, SK, address, w, length_all, idx_sig, h)

    # Создание и возвращение объекта SigXMSS с необходимыми данными для верификации
    return SigXMSS(idx_sig, r, sig.sig_ots, sig.auth)

def XMSS_rootFromSig(idx_sig: int, sig_ots, auth: List[bytearray], message: bytearray, h: int, w: int in {4, 16}, SEED, address: ADRS):
    n = len(message) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    address.setType(0)
    address.setOTSAddress(idx_sig)
    pk_ots = WOTS_pkFromSig(message, sig_ots, w, address, SEED)
    address.setType(1)
    address.setLTreeAddress(idx_sig)
    node = [bytearray, bytearray]
    node[0] = ltree(pk_ots, address, SEED, length_all)
    address.setType(2)
    address.setTreeIndex(idx_sig)

    for k in range(0, h):
        address.setTreeHeight(k)
        if floor(idx_sig / (2 ** k)) % 2 == 0:
            address.setTreeIndex(int.from_bytes(address.getTreeIndex(), byteorder='big') // 2)
            node[1] = RAND_HASH(node[0], auth[k], SEED, address)
        else:
            address.setTreeIndex((int.from_bytes(address.getTreeIndex(), byteorder='big') - 1) // 2)
            node[1] = RAND_HASH(auth[k], node[0], SEED, address)

        node[0] = node[1]

    return node[0]


# def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey, n, w: int in {4, 16}, SEED, height: int):
def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey):

    address = ADRS()

    height = PK.heigh
    n = PK.n
    w = PK.w
    SEED = PK.SEED

    # n = len(M) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    arrayOfBytes = bytearray()
    arrayOfBytes.extend(Sig.r)
    arrayOfBytes.extend(PK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(Sig.idx_sig, n)))

    M2 = H_msg(arrayOfBytes, M, len_1)

    node = XMSS_rootFromSig(Sig.idx_sig, Sig.sig_ots, Sig.auth, M2, height, w, SEED, address)

    if node == PK.root_value:
        return True
    else:
        return False


def generate_seed(length):
    # Простая функция для генерации псевдослучайного сида
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def XMSS_demo(messages: List[bytearray]):

    height = int(log2(len(messages)))
    n = len(messages[0]) // 2
    w = 16

    keyPair = XMSS_keyGen(height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))

def XMSS_demo_seed(messages: List[bytearray]):

    # height = int(log2(len(messages)))
    # msg_len = len(messages[0]) // 2
    # w = 16
    #
    # keyPair = XMSS_keyGen(height, msg_len, w)

    seed_client1 = "unique_seed_for_client1"  # Уникальный сид для клиента 1
    height = 4  # Высота дерева
    # n = 8  # Размер хэша в байтах
    n = len(messages[0]) // 2
    w = 16  # Параметр Winternitz

    # Генерация пары ключей на основе сида
    keyPair = XMSS_keyGen_from_seed(seed_client1, height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, n, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))


import os


def save_keys_to_file(keypair: XMSSKeypair , file_path: str):
    data = {
        'height':keypair.height,
        'n':keypair.n,
        'w':keypair.w,
        'private_key': {
            # Исправлено: обработка списка списков байтов
            'wots_private_keys': [[key.hex() for key in wots_key] for wots_key in keypair.SK.wots_private_keys],
            'idx': keypair.SK.idx,
            'SK_PRF': keypair.SK.SK_PRF,
            'root_value': keypair.SK.root_value.hex(),
            'SEED': keypair.SK.SEED
        },
        'public_key': {
            'OID': keypair.PK.OID,
            'root_value': keypair.PK.root_value.hex(),
            'SEED': keypair.PK.SEED
        }


    }
    with open(file_path, 'w') as file:
        json.dump(data, file)


def load_keys_from_file(file_path: str) -> XMSSKeypair:
    with open(file_path, 'r') as file:
        data = json.load(file)

    height = data['height']
    n  = data['n']
    w  = data['w']


    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()

    # Исправлено: корректная обработка структуры данных
    SK.wots_private_keys = [
        [bytes.fromhex(key_hex) for key_hex in wots_key]
        for wots_key in data['private_key']['wots_private_keys']
    ]
    SK.idx = data['private_key']['idx']
    SK.SK_PRF = data['private_key']['SK_PRF']
    SK.root_value = bytearray.fromhex(data['private_key']['root_value'])

    SK.SEED = data['private_key']['SEED']

    PK.OID = data['public_key']['OID']
    PK.root_value = bytes.fromhex(data['public_key']['root_value'])
    PK.SEED = data['public_key']['SEED']
    PK.heigh = height
    PK.n = n
    PK.w = w

    return XMSSKeypair(SK, PK, height, n, w)


if __name__ == '__main__':
    # WOTS_demo(bytearray(b'0e4575aa2c51'))
    # print("#" * 30)
    #

    # Пример вызова функции с сидом
    # seed = generate_seed(20)  # Генерируем сид
    # seed = "rBirgrP91TgImgg937kR"
    #
    # print(seed)
    # height = 4  # Высота дерева, определяющая количество возможных подписей
    # n = 32  # Размер хэша в байтах
    # w = 16  # Параметр Winternitz
    #
    # keyPair = XMSS_keyGen_from_seed(seed, height, n, w)
    #
    # print("Создана пара ключей XMSS с использованием сида.", keyPair.SK.generate_address())

    # seed = "some_seed_value"
    # height = 4  # Высота дерева
    # n = 256  # Длина ключа
    # keypair = XMSSKeypair.generate_keys_from_seed(seed, height, n)
    # print("Приватный ключ и публичный ключ успешно сгенерированы из сида.", keypair)


    # XMSS_demo([bytearray(b'0e4575aa2c51')])
    # XMSS_demo_seed([bytearray(b'0e4575aa2c51'), bytearray(b'1e4575aa2c51')])


    # Генерация пары ключей и адреса для Клиента 1
    seed_client1 = "unique_seed_for_client3"  # Уникальный сид для клиента 1
    height = 5  # Высота дерева
    n = 4  # Размер хэша в байтах
    w = 16  # Параметр Winternitz

    print("Количество подписей", 2**height)
    # Генерация пары ключей на основе сида
    keyPair_client1 = XMSS_keyGen_from_seed(seed_client1, height, n, w)
    save_keys_to_file(keyPair_client1, "client1.key")

    keyPair_client1= load_keys_from_file("client1.key")

    # Генерация адреса на основе публичного ключа
    address_client1 = keyPair_client1.PK.generate_address()



    print(f"Сид: {seed_client1}")
    print(f"Адрес Клиента 1: {address_client1}")
    print(f"Размер адреса Клиента 1: {len(address_client1)}")

    is_valid_address = keyPair_client1.PK.is_valid_address(address_client1)
    print(f"Адрес верен: {is_valid_address}")



    # Создание сообщения для подписи
    message_client1 = bytearray(b'This is a message from client1 to be signed.')

    # Подпись сообщения
    addressXMSS_client1 = ADRS()  # Инициализация адреса для XMSS

    d = datetime.datetime.now()
    print("Делаем подпись")
    signature_client1 = XMSS_sign(message_client1, keyPair_client1.SK, n, w, addressXMSS_client1, height)

    print(f"Подпись: {signature_client1}, размер: {len(signature_client1.to_bytes())} байт  время: {datetime.datetime.now() - d}" )

    # Верификация подписи сообщения Клиентом 2

    # Имитация получения публичного ключа Клиента 1 другим клиентом
    PK_client1_received = keyPair_client1.PK

    # Имитация получения сида Клиента 1 другим клиентом (в реальных условиях сид не передается)
    SEED_client1_received = PK_client1_received.SEED

    # Верификация подписи
    verification_result = XMSS_verify(signature_client1, message_client1, PK_client1_received)

    print(f"Результат верификации подписи: {'Подпись верна' if verification_result else 'Подпись неверна'}")


class XMSSPrivateKey:

    def __init__(self):
        self.wots_private_keys = None
        self.idx = None
        self.SK_PRF = None
        self.root_value = None
        self.SEED = None


class XMSSPublicKey:

    def __init__(self, OID=None, root_value=None, SEED=None, height = 4, n = 4, w = 32):
        self.OID = OID
        self.root_value = root_value
        self.SEED = SEED

        self.heigh = height
        self.n = n
        self.w = w


    def generate_address(self):
        # Конкатенация строковых представлений ключевых компонентов
        key_data = str(self.OID) + str(self.root_value) + str(self.SEED)

        # Генерация хеша из данных ключа
        key_hash = hashlib.sha256(key_data.encode('utf-8')).digest()

        # Применение кодирования Base58Check к хэшу
        # Генерация контрольной суммы из хеша хеша
        checksum = hashlib.sha256(hashlib.sha256(key_hash).digest()).digest()[:4]

        # Конкатенация хеша и контрольной суммы
        full_key = key_hash + checksum

        # Применение кодирования Base58 к полному ключу
        address = base58.b58encode(full_key).decode('utf-8')

        # Применение кодирования Base64 к хэшу
        # address = base64.urlsafe_b64encode(key_hash).decode('utf-8').rstrip('=')

        # Возврат адреса в кодировке Base58
        return f"Out{address}"

    @staticmethod
    def is_valid_address(address):
        """
        Проверяет, действителен ли криптовалютный адрес.

        :param address: Адрес для проверки, закодированный в Base58.
        :return: True, если адрес действителен; False в противном случае.
        """
        try:
            # Декодирование адреса из Base58
            # Убираем первые 3 байта как название
            decoded_address = base58.b58decode(address[3:])

            # Отделение контрольной суммы от остальной части адреса
            main_part = decoded_address[:-4]
            checksum = decoded_address[-4:]

            # Повторное вычисление контрольной суммы для основной части адреса
            calculated_checksum = hashlib.sha256(hashlib.sha256(main_part).digest()).digest()[:4]

            # Сравнение рассчитанной контрольной суммы с контрольной суммой в адресе
            return checksum == calculated_checksum
        except Exception as e:
            # В случае ошибок декодирования или других исключений адрес считается недействительным
            return False

    def to_json(self):
        return {
            'OID': self.OID,
            'root_value': self.root_value.hex(),
            'SEED': self.SEED
        }
    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self))

    @staticmethod
    def from_bytes(bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

    # def to_bytes(self):
    #     # Кодируем OID и SEED в байты
    #     oid_bytes = self.OID.encode('utf-8') if self.OID is not None else b''
    #     seed_bytes = self.SEED.encode('utf-8') if self.SEED is not None else b''
    #
    #     # Сериализуем данные с указанием длины каждой части
    #     return bytes([len(oid_bytes)]) + oid_bytes + bytes([len(self.root_value)]) + self.root_value + bytes(
    #         [len(seed_bytes)]) + seed_bytes
    #
    # @classmethod
    # def from_bytes(cls, bytes_data):
    #     # Десериализуем OID
    #     oid_length = bytes_data[0]
    #     oid = bytes_data[1:1 + oid_length].decode('utf-8')
    #
    #     # Десериализуем root_value
    #     root_value_start = 1 + oid_length
    #     root_value_length = bytes_data[root_value_start]
    #     root_value = bytes_data[root_value_start + 1:root_value_start + 1 + root_value_length]
    #
    #     # Десериализуем SEED
    #     seed_start = root_value_start + 1 + root_value_length
    #     seed_length = bytes_data[seed_start]
    #     SEED = bytes_data[seed_start + 1:seed_start + 1 + seed_length].decode('utf-8')
    #
    #     return cls(OID=oid, root_value=root_value, SEED=SEED)

    @classmethod
    def from_json(cls, json_data):
        OID = json_data.get('OID')
        root_value_hex = json_data.get('root_value')
        SEED_hex = json_data.get('SEED')

        root_value = bytes.fromhex(root_value_hex) if root_value_hex else None
        SEED = bytes.fromhex(SEED_hex) if SEED_hex else None

        return cls(OID=OID, root_value=root_value, SEED=SEED)

class XMSSKeypair:

    def __init__(self, SK, PK, height = 4, n = 4, w = 32):
        self.SK = SK
        self.PK = PK
        self.height =height
        self.n =n
        self.w =w

class SigXMSS:
    def __init__(self, idx_sig, r, sig_ots, auth):
        self.idx_sig = idx_sig
        self.r = r
        self.sig_ots = sig_ots
        self.auth = auth

    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self))

    @staticmethod
    def from_bytes(bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

class SigWithAuthPath:
    def __init__(self, sig_ots, auth):
        self.sig_ots = sig_ots
        self.auth = auth


class ADRS:

    def __init__(self):
        self.layerAddress = bytes(4)
        self.treeAddress = bytes(8)
        self.type = bytes(4)

        self.first_word = bytes(4)
        self.second_word = bytes(4)
        self.third_word = bytes(4)

        self.keyAndMask = bytes(4)

    def setType(self, type_value):
        self.type = type_value.to_bytes(4, byteorder='big')
        self.first_word = bytearray(4)
        self.second_word = bytearray(4)
        self.third_word = bytearray(4)
        self.keyAndMask = bytearray(4)

    def getTreeHeight(self):
        return self.second_word

    def getTreeIndex(self):
        return self.third_word

    def setHashAddress(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setKeyAndMask(self, value):
        self.keyAndMask = value.to_bytes(4, byteorder='big')

    def setChainAddress(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeHeight(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeIndex(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setOTSAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLTreeAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLayerAddress(self, value):
        self.layerAddress = value.to_bytes(4, byteorder='big')

    def setTreeAddress(self, value):
        self.treeAddress = value.to_bytes(4, byteorder='big')



def WOTS_genSK(length, n):
    secret_key = [bytes()] * length

    for i in range(length):
        SEED = generate_random_value(length)

        secret_key[i] = pseudorandom_function(SEED, n)

    return secret_key

import random
def WOTS_genSK_from_seed(length, n, seed):
    # Инициализация генератора случайных чисел с использованием сида
    random.seed(seed)

    secret_key = []
    for _ in range(length):
        # Генерация элемента секретного ключа
        random_bytes = random.getrandbits(n * 8).to_bytes(n, 'big')
        secret_key.append(random_bytes)

    return secret_key

def WOTS_genPK(private_key: [bytes], length: int, w: int in {4, 16}, SEED, address):
    public_key = [bytes()] * length
    for i in range(length):
        address.setChainAddress(i)
        public_key[i] = chain(private_key[i], 0, w - 1, SEED, address, w)

    return public_key


def WOTS_sign(message: bytes, private_key: [bytes], w: int in {4, 16}, SEED, address):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    signature = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        signature[i] = chain(private_key[i], 0, msg[i], SEED, address, w)

    return signature


def WOTS_pkFromSig(message: bytes, signature: [bytes], w: int in {4, 16}, address, SEED):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    tmp_pk = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        tmp_pk[i] = chain(signature[i], msg[i], w - 1 - msg[i], SEED, address, w)

    return tmp_pk




def base_w(byte_string: bytes, w: int in {4, 16}, out_len):
    in_ = 0
    total_ = 0
    bits_ = 0
    base_w_ = []

    for i in range(0, out_len):
        if bits_ == 0:
            total_ = byte_string[in_]
            in_ += 1
            bits_ += 8

        bits_ -= log2(w)
        base_w_.append((total_ >> int(bits_)) & (w - 1))
    return base_w_


# def generate_random_value(n):
#     alphabet = ascii_letters + digits
#     value = ''.join(choice(alphabet) for _ in range(n))
#     return value
from string import ascii_letters, digits


def generate_random_value(n, seed_value=None):
    # Инициализация генератора случайных чисел с заданным сидом
    seed(seed_value)

    alphabet = ascii_letters + digits
    value = ''.join(choice(alphabet) for _ in range(n))

    return value

def compute_needed_bytes(n):
    if n == 0:
        return 1
    return int(log(n, 256)) + 1


def compute_lengths(n: int, w: int in {4, 16}):
    len_1 = ceil(8 * n / log2(w))
    len_2 = floor(log2(len_1 * (w - 1)) / log2(w)) + 1
    len_all = len_1 + len_2
    return len_1, len_2, len_all


# def to_byte(value, bytes_count):
#     return value.to_bytes(bytes_count, byteorder='big')

def to_byte(value, bytes_count):
    # Преобразование целого числа в bytes
    return value.to_bytes(bytes_count, byteorder='big')

def xor(one: bytearray, two: bytearray) -> bytearray:
    return bytearray(a ^ b for (a, b) in zip(one, two))


def int_to_bytes(val, count):
    byteVal = to_byte(val, count)
    acc = bytearray()
    for i in range(len(byteVal)):
        if byteVal[i] < 16:
            acc.extend(b'0')
        curr = hex(byteVal[i])[2:]
        acc.extend(curr.encode())
    return acc


def F(KEY, M):
    key_len = len(KEY)
    toBytes = to_byte(0, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def chain(X, i, s, SEED, address, w):

    if s == 0:
        return X
    if (i + s) > (w - 1):
        return None
    tmp = chain(X, i, s - 1, SEED, address, w)

    address.setHashAddress((i + s - 1))
    address.setKeyAndMask(0)
    KEY = PRF(SEED, address)
    address.setKeyAndMask(1)
    BM = PRF(SEED, address)
    tmp = F(KEY, xor(tmp, BM))
    return tmp


def PRF(KEY: str, M: ADRS) -> bytearray:
    toBytes = to_byte(3, 4)
    key_len = len(KEY)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M.keyAndMask).hexdigest()[:key_len*2]
    out = bytearray()
    out.extend(map(ord, help_))
    return out



def H(KEY: bytearray, M: bytearray) -> bytearray:
    key_len = len(KEY)
    toBytes = to_byte(1, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def PRF_XMSS(KEY: str, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(3, 4)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def H_msg(KEY: bytearray, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(2, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def RAND_HASH(left: bytearray, right: bytearray, SEED: str, adrs: ADRS):
    adrs.setKeyAndMask(0)
    KEY = PRF(SEED, adrs)
    adrs.setKeyAndMask(1)
    BM_0 = PRF(SEED, adrs)
    adrs.setKeyAndMask(2)
    BM_1 = PRF(SEED, adrs)

    return H(KEY, xor(left, BM_0) + xor(right, BM_1))


# def pseudorandom_function(SEED, n):
#     seed(SEED)
#     sk_element = list()
#     for i in range(n):
#         sign = randint(0, 255)
#         sk_element.append('{:02x}'.format(sign))
#
#     return bytearray(''.join(sk_element).encode(encoding='utf-8'))

import hashlib


def pseudorandom_function(seed, n):
    # Создаем хеш из сида, предполагая, что seed является строкой.
    seed_bytes = seed.encode('utf-8')  # Преобразуем строку сида в байты
    hash_digest = hashlib.sha256(seed_bytes).digest()  # Создаем хеш SHA-256 от сида

    # Обрезаем или дополняем хеш до нужной длины n, возвращаем как bytearray
    return bytearray(hash_digest)[:n]


def ltree(pk: List[bytearray], address: ADRS, SEED: str, length: int) -> bytearray:

    address.setTreeHeight(0)

    while length > 1:
        for i in range(floor(length / 2)):
            address.setTreeIndex(i)
            pk[i] = RAND_HASH(pk[2 * i], pk[2 * i + 1], SEED, address)

        if length % 2 == 1:
            pk[floor(length / 2)] = pk[length - 1]

        length = ceil(length / 2)
        height = address.getTreeHeight()
        height = int.from_bytes(height, byteorder='big')
        address.setTreeHeight(height + 1)

    return pk[0]


def treeHash(SK: XMSSPrivateKey, s: int, t: int, address: ADRS, w: int in {4, 16}, length_all: int) -> bytearray:

    class StackElement:
        def __init__(self, node_value=None, height=None):
            self.node_value = node_value
            self.height = height

    Stack = []

    if s % (1 << t) != 0:
        raise ValueError("should be s % (1 << t) != 0")

    for i in range(0, int(pow(2, t))):
        SEED = SK.SEED
        address.setType(0)
        address.setOTSAddress(s + i)
        pk = WOTS_genPK(SK.wots_private_keys[s + i], length_all, w, SEED, address)
        address.setType(1)
        address.setLTreeAddress(s + i)
        node = ltree(pk, address, SEED, length_all)

        node_as_stack_element = StackElement(node, 0)

        address.setType(2)
        address.setTreeHeight(0)
        address.setTreeIndex(i + s)

        while len(Stack) != 0 and Stack[len(Stack) - 1].height == node_as_stack_element.height:
            address.setTreeIndex(int((int.from_bytes(address.getTreeHeight(), byteorder='big') - 1) / 2))

            previous_height = node_as_stack_element.height

            node = RAND_HASH(Stack.pop().node_value, node_as_stack_element.node_value, SEED, address)

            node_as_stack_element = StackElement(node, previous_height + 1)

            address.setTreeHeight(int.from_bytes(address.getTreeHeight(), byteorder='big') + 1)

        Stack.append(node_as_stack_element)

    return Stack.pop().node_value





def XMSS_keyGen(height: int, n: int, w: int in {4, 16}) -> XMSSKeypair:

    len_1, len_2, len_all = compute_lengths(n, w)

    wots_sk = []
    for i in range(0, 2 ** height):
        wots_sk.append(WOTS_genSK(len_all, n))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value(n)
    SEED = generate_random_value(n)
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    root = treeHash(SK, 0, height, adrs, w, len_all)

    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n)
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK)
    return KeyPair

def XMSS_keyGen_from_seed(seed: str, height: int, n: int, w: int) -> XMSSKeypair:
    len_1, len_2, len_all = compute_lengths(n, w)
    wots_sk = []

    # Изменяем генерацию WOTS ключей, используя уникальный сид для каждого ключа
    for i in range(0, 2 ** height):
        unique_seed = pseudorandom_function(seed + str(i), n)  # Генерация уникального сида для каждого ключа
        wots_sk.append(WOTS_genSK_from_seed(len_all, n, unique_seed))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value( n, seed + "SK_PRF")  # Генерация SK_PRF на основе сида
    SEED = generate_random_value(n, seed + "SEED")  # Генерация SEED на основе сида
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    # Генерация корня дерева
    root = treeHash(SK, 0, height, adrs, w, len_all)
    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n, seed + "OID")  # Генерация OID на основе сида
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK, height, n, w)
    return KeyPair

def buildAuth(SK: XMSSPrivateKey, index: int, address: ADRS, w: int in {4, 16}, length_all: int, h: int) -> List[bytearray]:
    auth = []

    for j in range(h):
        k = floor(index / (2 ** j)) ^ 1
        auth.append(treeHash(SK, k * (2 ** j), j, address, w, length_all))
    return auth


def treeSig(message: bytearray, SK: XMSSPrivateKey, address: ADRS, w: int in {4, 16}, length_all: int, idx_sig: int, h: int) -> SigWithAuthPath:
    auth = buildAuth(SK, idx_sig, address, w, length_all, h)
    address.setType(0)
    address.setOTSAddress(idx_sig)
    sig_ots = WOTS_sign(message, SK.wots_private_keys[idx_sig], w, SK.SEED, address)
    Sig = SigWithAuthPath(sig_ots, auth)
    return Sig


# def XMSS_sign(message: bytearray, SK: XMSSPrivateKey, n, w: int in {4, 16}, address: ADRS, h: int) -> SigXMSS:
#     # n = len(message) // 2
#     len_1, len_2, length_all = compute_lengths(n, w)
#     idx_sig = SK.idx
#     SK.idx = idx_sig + 1
#     r = PRF_XMSS(SK.SK_PRF, to_byte(idx_sig, 4), len_1)
#     arrayOfBytes = bytearray()
#     arrayOfBytes.extend(r)
#     arrayOfBytes.extend(SK.root_value)
#     arrayOfBytes.extend(bytearray(int_to_bytes(idx_sig, n)))
#     M2 = H_msg(arrayOfBytes, message, len_1)
#
#     value = treeSig(M2, SK, address, w, length_all, idx_sig, h)
#
#     # return SigXMSS(idx_sig, r, value, SK, M2)
#     return SigXMSS(idx_sig, r, sig_ots, auth)
def XMSS_sign(message: bytearray, SK: XMSSPrivateKey, n, w: int, address: ADRS, h: int) -> SigXMSS:
    len_1, len_2, length_all = compute_lengths(n, w)
    idx_sig = SK.idx
    SK.idx += 1  # Инкрементируем индекс после использования

    # Генерация случайного значения на основе секретного ключа и индекса подписи
    r = PRF_XMSS(SK.SK_PRF, to_byte(idx_sig, 4), len_1)

    # Создание расширенного представления подписи с добавлением r и root_value
    arrayOfBytes = bytearray(r)
    arrayOfBytes.extend(SK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(idx_sig, n)))

    # Генерация вторичного хеша сообщения
    M2 = H_msg(arrayOfBytes, message, len_1)

    # Получение одноразовой подписи и аутентификационного пути
    sig = treeSig(M2, SK, address, w, length_all, idx_sig, h)

    # Создание и возвращение объекта SigXMSS с необходимыми данными для верификации
    return SigXMSS(idx_sig, r, sig.sig_ots, sig.auth)

def XMSS_rootFromSig(idx_sig: int, sig_ots, auth: List[bytearray], message: bytearray, h: int, w: int in {4, 16}, SEED, address: ADRS):
    n = len(message) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    address.setType(0)
    address.setOTSAddress(idx_sig)
    pk_ots = WOTS_pkFromSig(message, sig_ots, w, address, SEED)
    address.setType(1)
    address.setLTreeAddress(idx_sig)
    node = [bytearray, bytearray]
    node[0] = ltree(pk_ots, address, SEED, length_all)
    address.setType(2)
    address.setTreeIndex(idx_sig)

    for k in range(0, h):
        address.setTreeHeight(k)
        if floor(idx_sig / (2 ** k)) % 2 == 0:
            address.setTreeIndex(int.from_bytes(address.getTreeIndex(), byteorder='big') // 2)
            node[1] = RAND_HASH(node[0], auth[k], SEED, address)
        else:
            address.setTreeIndex((int.from_bytes(address.getTreeIndex(), byteorder='big') - 1) // 2)
            node[1] = RAND_HASH(auth[k], node[0], SEED, address)

        node[0] = node[1]

    return node[0]


# def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey, n, w: int in {4, 16}, SEED, height: int):
def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey):

    address = ADRS()

    height = PK.heigh
    n = PK.n
    w = PK.w
    SEED = PK.SEED

    # n = len(M) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    arrayOfBytes = bytearray()
    arrayOfBytes.extend(Sig.r)
    arrayOfBytes.extend(PK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(Sig.idx_sig, n)))

    M2 = H_msg(arrayOfBytes, M, len_1)

    node = XMSS_rootFromSig(Sig.idx_sig, Sig.sig_ots, Sig.auth, M2, height, w, SEED, address)

    if node == PK.root_value:
        return True
    else:
        return False


def generate_seed(length):
    # Простая функция для генерации псевдослучайного сида
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def XMSS_demo(messages: List[bytearray]):

    height = int(log2(len(messages)))
    n = len(messages[0]) // 2
    w = 16

    keyPair = XMSS_keyGen(height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))

def XMSS_demo_seed(messages: List[bytearray]):

    # height = int(log2(len(messages)))
    # msg_len = len(messages[0]) // 2
    # w = 16
    #
    # keyPair = XMSS_keyGen(height, msg_len, w)

    seed_client1 = "unique_seed_for_client1"  # Уникальный сид для клиента 1
    height = 4  # Высота дерева
    # n = 8  # Размер хэша в байтах
    n = len(messages[0]) // 2
    w = 16  # Параметр Winternitz

    # Генерация пары ключей на основе сида
    keyPair = XMSS_keyGen_from_seed(seed_client1, height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, n, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))


import os


def save_keys_to_file(keypair: XMSSKeypair , file_path: str):
    data = {
        'height':keypair.height,
        'n':keypair.n,
        'w':keypair.w,
        'private_key': {
            # Исправлено: обработка списка списков байтов
            'wots_private_keys': [[key.hex() for key in wots_key] for wots_key in keypair.SK.wots_private_keys],
            'idx': keypair.SK.idx,
            'SK_PRF': keypair.SK.SK_PRF,
            'root_value': keypair.SK.root_value.hex(),
            'SEED': keypair.SK.SEED
        },
        'public_key': {
            'OID': keypair.PK.OID,
            'root_value': keypair.PK.root_value.hex(),
            'SEED': keypair.PK.SEED
        }


    }
    with open(file_path, 'w') as file:
        json.dump(data, file)


def load_keys_from_file(file_path: str) -> XMSSKeypair:
    with open(file_path, 'r') as file:
        data = json.load(file)

    height = data['height']
    n  = data['n']
    w  = data['w']


    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()

    # Исправлено: корректная обработка структуры данных
    SK.wots_private_keys = [
        [bytes.fromhex(key_hex) for key_hex in wots_key]
        for wots_key in data['private_key']['wots_private_keys']
    ]
    SK.idx = data['private_key']['idx']
    SK.SK_PRF = data['private_key']['SK_PRF']
    SK.root_value = bytearray.fromhex(data['private_key']['root_value'])

    SK.SEED = data['private_key']['SEED']

    PK.OID = data['public_key']['OID']
    PK.root_value = bytes.fromhex(data['public_key']['root_value'])
    PK.SEED = data['public_key']['SEED']
    PK.heigh = height
    PK.n = n
    PK.w = w

    return XMSSKeypair(SK, PK, height, n, w)


if __name__ == '__main__':
    # WOTS_demo(bytearray(b'0e4575aa2c51'))
    # print("#" * 30)
    #

    # Пример вызова функции с сидом
    # seed = generate_seed(20)  # Генерируем сид
    # seed = "rBirgrP91TgImgg937kR"
    #
    # print(seed)
    # height = 4  # Высота дерева, определяющая количество возможных подписей
    # n = 32  # Размер хэша в байтах
    # w = 16  # Параметр Winternitz
    #
    # keyPair = XMSS_keyGen_from_seed(seed, height, n, w)
    #
    # print("Создана пара ключей XMSS с использованием сида.", keyPair.SK.generate_address())

    # seed = "some_seed_value"
    # height = 4  # Высота дерева
    # n = 256  # Длина ключа
    # keypair = XMSSKeypair.generate_keys_from_seed(seed, height, n)
    # print("Приватный ключ и публичный ключ успешно сгенерированы из сида.", keypair)


    # XMSS_demo([bytearray(b'0e4575aa2c51')])
    # XMSS_demo_seed([bytearray(b'0e4575aa2c51'), bytearray(b'1e4575aa2c51')])


    # Генерация пары ключей и адреса для Клиента 1
    seed_client1 = "unique_seed_for_client2"  # Уникальный сид для клиента 1
    height = 5  # Высота дерева
    n = 4  # Размер хэша в байтах
    w = 16  # Параметр Winternitz

    print("Количество подписей", 2**height)
    # Генерация пары ключей на основе сида
    keyPair_client1 = XMSS_keyGen_from_seed(seed_client1, height, n, w)
    save_keys_to_file(keyPair_client1, "client1.key")

    keyPair_client1= load_keys_from_file("client1.key")

    # Генерация адреса на основе публичного ключа
    address_client1 = keyPair_client1.PK.generate_address()



    print(f"Сид: {seed_client1}")
    print(f"Адрес Клиента 1: {address_client1}")
    print(f"Размер адреса Клиента 1: {len(address_client1)}")

    is_valid_address = keyPair_client1.PK.is_valid_address(address_client1)
    print(f"Адрес верен: {is_valid_address}")



    # Создание сообщения для подписи
    message_client1 = bytearray(b'This is a message from client1 to be signed.')

    # Подпись сообщения
    addressXMSS_client1 = ADRS()  # Инициализация адреса для XMSS

    d = datetime.datetime.now()
    print("Делаем подпись")
    signature_client1 = XMSS_sign(message_client1, keyPair_client1.SK, n, w, addressXMSS_client1, height)

    print(f"Подпись: {signature_client1}, размер: {len(signature_client1.to_bytes())} байт  время: {datetime.datetime.now() - d}" )

    # Верификация подписи сообщения Клиентом 2

    # Имитация получения публичного ключа Клиента 1 другим клиентом
    PK_client1_received = keyPair_client1.PK

    # Имитация получения сида Клиента 1 другим клиентом (в реальных условиях сид не передается)
    SEED_client1_received = PK_client1_received.SEED

    # Верификация подписи
    verification_result = XMSS_verify(signature_client1, message_client1, PK_client1_received)

    print(f"Результат верификации подписи: {'Подпись верна' if verification_result else 'Подпись неверна'}")

