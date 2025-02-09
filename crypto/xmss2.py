import os
import math
import json
import base58
import struct
import pickle
import zlib
import hashlib
import secrets
from math import floor, ceil, log2, log
from typing import List

# ------------------------------------------------------------------------------
# Глобальные объекты и базовые определения
# ------------------------------------------------------------------------------

class Protocol:
    DEFAULT_HASH_FUNCTION_CODE = 0
    DEFAULT_HEIGHT = 4

# Список для seed-фразы: 4096 слов, каждое слово соответствует 12 битам
from crypto.world_list import word_list
# word_list = [f"word{i:04d}" for i in range(4096)]

# Простейший логгер (для отладки)
class Log:
    def info(self, message):
        print("[INFO]", message)

# Глобальный словарь хэш-функций
hash_functions = {
    0: lambda: hashlib.sha256(),
    1: lambda: hashlib.shake_128(),
    2: lambda: hashlib.shake_256()
}
Protocol.hash_functions = hash_functions

# ------------------------------------------------------------------------------
# Утилитарные функции
# ------------------------------------------------------------------------------

def to_byte(value, length):
    return value.to_bytes(length, byteorder='big')

def int_to_bytes(val, length):
    return val.to_bytes(length, byteorder='big')

def xor(one: bytes, two: bytes) -> bytes:
    return bytes(a ^ b for (a, b) in zip(one, two))

def compute_needed_bytes(n):
    if n == 0:
        return 1
    return (n.bit_length() + 7) // 8

def compute_lengths(n: int, w: int):
    step = int(math.log2(w))
    len_1 = ceil(8 * n / step)
    len_2 = floor(math.log(len_1 * (w - 1), w)) + 1
    len_all = len_1 + len_2
    return len_1, len_2, len_all

def generate_random_value(n, seed_value=None):
    return secrets.token_bytes(n)

# ------------------------------------------------------------------------------
# Функции хэширования и преобразования
# ------------------------------------------------------------------------------

def F(KEY: bytes, M: bytes) -> bytearray:
    data = to_byte(0, 4) + KEY + M
    h = hashlib.sha256(data).digest()
    return bytearray(h[:len(KEY)])

def H(KEY: bytes, M: bytes) -> bytearray:
    data = to_byte(1, 4) + KEY + M
    h = hashlib.sha256(data).digest()
    return bytearray(h[:len(KEY)])

def H_msg(KEY: bytes, M: bytes, n: int) -> bytearray:
    data = to_byte(2, 4) + KEY + M
    h = hashlib.sha256(data).digest()
    return bytearray(h[:n])

def PRF(KEY: bytes, adrs, out_len=None) -> bytearray:
    data = to_byte(3, 4) + KEY + adrs.keyAndMask
    h = hashlib.sha256(data).digest()
    if out_len is None:
        out_len = len(KEY)
    return bytearray(h[:out_len])

def PRF_XMSS(KEY: bytes, M: bytes, n: int) -> bytearray:
    data = to_byte(3, 4) + KEY + M
    h = hashlib.sha256(data).digest()
    return bytearray(h[:n])

def pseudorandom_function(seed: bytes, n, hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE):
    hash_func = hash_functions.get(hash_function_code, lambda: hashlib.shake_128())()
    hash_func.update(seed)
    return bytearray(hash_func.digest(n))

def base_w(byte_string: bytes, w: int, out_len):
    step = int(math.log2(w))
    in_idx = 0
    total_ = 0
    bits_ = 0
    base_w_list = []
    for i in range(out_len):
        if bits_ < step:
            if in_idx < len(byte_string):
                total_ = byte_string[in_idx]
                in_idx += 1
                bits_ += 8
            else:
                total_ = 0
                bits_ += 8
        bits_ -= step
        base_w_list.append((total_ >> bits_) & (w - 1))
    return base_w_list

# ------------------------------------------------------------------------------
# Основные классы
# ------------------------------------------------------------------------------

class XMSSPrivateKey:
    def __init__(self):
        self.wots_private_keys = None
        self.idx = 0
        self.SK_PRF = None
        self.root_value = None
        self.SEED = None

class XMSSPublicKey:
    def __init__(self, OID=None, root_value=None, SEED=None, height=4, n=4, w=32):
        self.OID = OID
        self.root_value = root_value
        self.SEED = SEED
        self.height = height
        self.n = n
        self.w = w
        self.hash_functions = Protocol.hash_functions
        self.address_start = ""
    def max_height(self):
        return 2 ** self.height
    def verify_sign(self, signature_str, message):
        signature = SigXMSS.from_base64(signature_str)
        return XMSS_verify(signature, message, self, self.n, self.w)
    def generate_address(self, hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE):
        tree_height = self.height
        signature_scheme_code = 0  # XMSS
        params = ((hash_function_code << 4) | tree_height).to_bytes(1, 'big') + signature_scheme_code.to_bytes(1, 'big')
        key_data = params + str(self.OID).encode() + self.root_value + str(self.SEED).encode()
        hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_256())()
        hash_func.update(key_data)
        if hash_function_code in {1, 2}:
            key_hash = hash_func.digest(32)
        else:
            key_hash = hash_func.digest()
        hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_256())()
        hash_func.update(key_hash)
        checksum = hash_func.digest(32)[:4] if hash_function_code in {1, 2} else hash_func.digest()[:4]
        full_key = key_hash + params + checksum
        address = base58.b58encode(full_key).decode('utf-8')
        return f"{self.address_start}{address}"
    def address_info(self, address):
        decoded_address = base58.b58decode(address[len(self.address_start):])
        key_hash = decoded_address[:-6]
        params = decoded_address[-6:-4]
        checksum = decoded_address[-4:]
        hash_function_code = params[0] >> 4
        tree_height = params[0] & 0x0F
        return {"hash_function_code": hash_function_code, "tree_height": tree_height, "key_hash": key_hash, "params": params, "checksum": checksum}
    def address_height(self, address):
        return self.address_info(address)['tree_height']
    def address_max_sign(self, address):
        return 2 ** self.address_height(address)
    def is_valid_address(self, address):
        try:
            decoded_address = base58.b58decode(address[len(self.address_start):])
            params = decoded_address[-6:-4]
            hash_function_code = params[0] >> 4
            main_part = decoded_address[0:-6]
            checksum = decoded_address[-4:]
            hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_128())()
            hash_func.update(main_part)
            calculated_checksum = hash_func.digest(32)[:4] if hash_function_code in {1, 2} else hash_func.digest()[:4]
            return checksum == calculated_checksum
        except Exception as e:
            return False
    def to_json(self):
        return {
            'OID': self.OID,
            'root_value': self.root_value.hex(),
            'SEED': self.SEED.hex() if isinstance(self.SEED, bytes) else self.SEED,
            'height': self.height,
            'n': self.n,
            'w': self.w
        }
    def to_bytes(self):
        return zlib.compress(pickle.dumps(self.to_json()))
    def to_str(self):
        return base58.b58encode(self.to_bytes()).decode('utf-8')
    @classmethod
    def from_str(cls, text_pk):
        return XMSSPublicKey.from_json(XMSSPublicKey._from_bytes(base58.b58decode(text_pk)))
    @classmethod
    def _from_bytes(cls, bytes_data):
        return pickle.loads(zlib.decompress(bytes_data))
    @classmethod
    def from_bytes(cls, bytes_data):
        return XMSSPublicKey.from_json(pickle.loads(zlib.decompress(bytes_data)))
    def to_hex(self):
        return self.to_bytes().hex()
    @classmethod
    def from_hex(cls, pk_hex):
        return XMSSPublicKey.from_bytes(bytes.fromhex(pk_hex))
    @classmethod
    def from_json(cls, json_data):
        OID = json_data.get('OID')
        root_value_hex = json_data.get('root_value')
        SEED = json_data.get('SEED')
        height = json_data.get('height')
        n = json_data.get('n')
        w = json_data.get('w')
        root_value = bytes.fromhex(root_value_hex) if root_value_hex else None
        return cls(OID=OID, root_value=root_value, SEED=bytes.fromhex(SEED) if isinstance(SEED, str) else SEED, height=height, n=n, w=w)

class XMSSKeypair:
    def __init__(self, SK: XMSSPrivateKey, PK: XMSSPublicKey, height=4, n=4, w=32):
        self.SK = SK
        self.PK = PK
        self.height = height
        self.n = n
        self.w = w

class SigXMSS:
    def __init__(self, idx_sig, r, sig_ots, auth):
        self.idx_sig = idx_sig
        self.r = r
        self.sig_ots = sig_ots
        self.auth = auth
    def to_bytes(self):
        return zlib.compress(pickle.dumps(self))
    def to_hex(self):
        return self.to_bytes().hex()
    def to_base64(self):
        return base58.b58encode(self.to_bytes()).decode('utf-8')
    @classmethod
    def from_bytes(cls, bytes_data):
        return pickle.loads(zlib.decompress(bytes_data))
    @classmethod
    def from_hex(cls, hex_data):
        return cls.from_bytes(zlib.decompress(bytes.fromhex(hex_data)))
    @classmethod
    def from_base64(cls, sign_str):
        return cls.from_bytes(base58.b58decode(sign_str.encode()))

class SigWithAuthPath:
    def __init__(self, sig_ots, auth):
        self.sig_ots = sig_ots
        self.auth = auth

# ------------------------------------------------------------------------------
# Класс ADRS (адресация) с методом clone
# ------------------------------------------------------------------------------
class ADRS:
    def __init__(self):
        self.layerAddress = bytes(4)
        self.treeAddress = bytes(8)
        self.type = bytes(4)
        self.first_word = bytes(4)
        self.second_word = bytes(4)
        self.third_word = bytes(4)
        self.keyAndMask = bytes(4)
    def clone(self):
        new_addr = ADRS()
        new_addr.layerAddress = self.layerAddress
        new_addr.treeAddress = self.treeAddress
        new_addr.type = self.type
        new_addr.first_word = self.first_word
        new_addr.second_word = self.second_word
        new_addr.third_word = self.third_word
        new_addr.keyAndMask = self.keyAndMask
        return new_addr
    def setType(self, type_value):
        self.type = to_byte(type_value, 4)
        self.first_word = bytearray(4)
        self.second_word = bytearray(4)
        self.third_word = bytearray(4)
        self.keyAndMask = bytearray(4)
    def getTreeHeight(self):
        return self.second_word
    def getTreeIndex(self):
        return self.third_word
    def setHashAddress(self, value):
        self.third_word = to_byte(value, 4)
    def setKeyAndMask(self, value):
        self.keyAndMask = to_byte(value, 4)
    def setChainAddress(self, value):
        self.second_word = to_byte(value, 4)
    def setTreeHeight(self, value):
        self.second_word = to_byte(value, 4)
    def setTreeIndex(self, value):
        self.third_word = to_byte(value, 4)
    def setOTSAddress(self, value):
        self.first_word = to_byte(value, 4)
    def setLTreeAddress(self, value):
        self.first_word = to_byte(value, 4)
    def setLayerAddress(self, value):
        self.layerAddress = to_byte(value, 4)
    def setTreeAddress(self, value):
        self.treeAddress = to_byte(value, 4)

# ------------------------------------------------------------------------------
# Функции WOTS
# ------------------------------------------------------------------------------

def WOTS_genSK(length, n):
    secret_key = []
    for i in range(length):
        SEED = generate_random_value(n)
        sk_elem = pseudorandom_function(SEED, n)
        secret_key.append(sk_elem)
    return secret_key

def WOTS_genSK_from_seed(length, n, seed: bytes):
    secret_key = []
    for i in range(length):
        data = seed + int_to_bytes(len(secret_key), 4)
        sk_elem = hashlib.sha256(data).digest()[:n]
        secret_key.append(sk_elem)
    return secret_key

def WOTS_sign(message: bytes, private_key: List[bytes], n: int, w: int, SEED: bytes, address: ADRS) -> List[bytearray]:
    checksum = 0
    len_1, len_2, len_all = compute_lengths(n, w)
    msg_base = base_w(message, w, len_1)
    for i in range(len_1):
        checksum += w - 1 - msg_base[i]
    shift_amount = (len_2 * int(math.log2(w))) % 8
    checksum = checksum << (8 - shift_amount) if shift_amount != 0 else checksum
    len_2_bytes = compute_needed_bytes(checksum)
    checksum_bytes = int_to_bytes(checksum, len_2_bytes)
    msg_base.extend(base_w(checksum_bytes, w, len_2))
    signature = []
    for i in range(len_all):
        local_addr = address.clone()
        local_addr.setChainAddress(i)
        sig_elem = chain(private_key[i], 0, msg_base[i], SEED, local_addr, w)
        signature.append(sig_elem)
    return signature

def WOTS_pkFromSig(message: bytes, signature: List[bytes], n: int, w: int, address: ADRS, SEED: bytes) -> List[bytearray]:
    checksum = 0
    len_1, len_2, len_all = compute_lengths(n, w)
    msg_base = base_w(message, w, len_1)
    for i in range(len_1):
        checksum += w - 1 - msg_base[i]
    shift_amount = (len_2 * int(math.log2(w))) % 8
    checksum = checksum << (8 - shift_amount) if shift_amount != 0 else checksum
    len_2_bytes = compute_needed_bytes(checksum)
    checksum_bytes = int_to_bytes(checksum, len_2_bytes)
    msg_base.extend(base_w(checksum_bytes, w, len_2))
    tmp_pk = []
    for i in range(len_all):
        local_addr = address.clone()
        local_addr.setChainAddress(i)
        pk_elem = chain(signature[i], msg_base[i], w - 1 - msg_base[i], SEED, local_addr, w)
        tmp_pk.append(pk_elem)
    return tmp_pk

# ------------------------------------------------------------------------------
# Функция ltree (построение L-дерева)
# ------------------------------------------------------------------------------
def ltree(pk: List[bytearray], address: ADRS, SEED: bytes, length: int) -> bytearray:
    local_addr = address.clone()
    local_addr.setTreeHeight(0)
    while length > 1:
        for i in range(floor(length / 2)):
            temp_addr = local_addr.clone()
            temp_addr.setTreeIndex(i)
            pk[i] = RAND_HASH(pk[2 * i], pk[2 * i + 1], SEED, temp_addr)
        if length % 2 == 1:
            pk[floor(length / 2)] = pk[length - 1]
        length = ceil(length / 2)
        current_height = int.from_bytes(local_addr.getTreeHeight(), byteorder='big')
        local_addr.setTreeHeight(current_height + 1)
    return pk[0]

# ------------------------------------------------------------------------------
# Функция RAND_HASH
# ------------------------------------------------------------------------------
def RAND_HASH(left: bytearray, right: bytearray, SEED: bytes, adrs: ADRS) -> bytearray:
    adrs.setKeyAndMask(0)
    KEY_val = PRF(SEED, adrs)
    adrs.setKeyAndMask(1)
    BM_0 = PRF(SEED, adrs)
    adrs.setKeyAndMask(2)
    BM_1 = PRF(SEED, adrs)
    combined = xor(left, BM_0) + xor(right, BM_1)
    return H(KEY_val, combined)

# ------------------------------------------------------------------------------
# Функция chain с использованием cloned адресов
# ------------------------------------------------------------------------------
def chain(X: bytes, i: int, s: int, SEED: bytes, address: ADRS, w: int):
    if s == 0:
        return X
    if (i + s) > (w - 1):
        raise ValueError("Invalid chain length: i + s exceeds w-1")
    local_addr = address.clone()
    prev = chain(X, i, s - 1, SEED, local_addr, w)
    local_addr = address.clone()
    local_addr.setHashAddress(i + s - 1)
    local_addr.setKeyAndMask(0)
    KEY_val = PRF(SEED, local_addr)
    local_addr = address.clone()
    local_addr.setKeyAndMask(1)
    BM = PRF(SEED, local_addr)
    result = F(KEY_val, xor(prev, BM))
    return result

def WOTS_genPK(private_key: List[bytes], length: int, w: int, SEED: bytes, address: ADRS) -> List[bytearray]:
    public_key = []
    for i in range(length):
        local_addr = address.clone()
        local_addr.setChainAddress(i)
        pk_elem = chain(private_key[i], 0, w - 1, SEED, local_addr, w)
        public_key.append(pk_elem)
    return public_key

# ------------------------------------------------------------------------------
# Функции построения аутентификационного пути и восстановления корневого узла
# ------------------------------------------------------------------------------
def treeHash(SK, s: int, t: int, address: ADRS, w: int, length_all: int) -> bytearray:
    class StackElement:
        def __init__(self, node_value=None, height=0):
            self.node_value = node_value
            self.height = height
    stack = []
    if s % (1 << t) != 0:
        raise ValueError("Invalid s for given t in treeHash")
    for i in range(0, (1 << t)):
        local_addr = address.clone()
        local_addr.setType(0)
        local_addr.setOTSAddress(s + i)
        pk = WOTS_genPK(SK.wots_private_keys[s + i], length_all, w, SK.SEED, local_addr)
        local_addr = address.clone()
        local_addr.setType(1)
        local_addr.setLTreeAddress(s + i)
        node_value = ltree(pk, local_addr, SK.SEED, length_all)
        elem = StackElement(node_value, 0)
        local_addr = address.clone()
        local_addr.setType(2)
        local_addr.setTreeHeight(0)
        local_addr.setTreeIndex(s + i)
        while stack and stack[-1].height == elem.height:
            last_elem = stack.pop()
            temp_addr = address.clone()
            temp_addr.setTreeIndex((s + i) // 2)
            combined = RAND_HASH(last_elem.node_value, elem.node_value, SK.SEED, temp_addr)
            elem = StackElement(combined, elem.height + 1)
        stack.append(elem)
    return stack.pop().node_value

def buildAuth(SK, index: int, address: ADRS, w: int, length_all: int, h: int) -> List[bytearray]:
    auth = []
    for j in range(h):
        i_j = index // (2 ** j)
        sibling = i_j ^ 1
        s = sibling * (2 ** j)
        auth_node = treeHash(SK, s, j, address.clone(), w, length_all)
        auth.append(auth_node)
    return auth

def XMSS_rootFromSig(idx_sig: int, sig_ots, auth: List[bytearray], message: bytearray, h: int, w: int, SEED: bytes, address: ADRS, n: int) -> bytearray:
    local_addr = address.clone()
    local_addr.setType(0)
    local_addr.setOTSAddress(idx_sig)
    pk_ots = WOTS_pkFromSig(message, sig_ots, n, w, local_addr, SEED)
    local_addr = address.clone()
    local_addr.setType(1)
    len_all_val = compute_lengths(n, w)[2]
    node = ltree(pk_ots, local_addr, SEED, len_all_val)
    for j in range(h):
        i_j = idx_sig // (2 ** j)
        temp_addr = address.clone()
        temp_addr.setType(2)
        temp_addr.setTreeHeight(j)
        if i_j % 2 == 0:
            temp_addr.setTreeIndex((i_j + 1) // 2)
            node = RAND_HASH(node, auth[j], SEED, temp_addr)
        else:
            temp_addr.setTreeIndex((i_j - 1) // 2)
            node = RAND_HASH(auth[j], node, SEED, temp_addr)
    return node

def treeSig(message: bytearray, SK, address: ADRS, w: int, length_all: int, idx_sig: int, h: int, n: int):
    auth = buildAuth(SK, idx_sig, address, w, length_all, h)
    local_addr = address.clone()
    local_addr.setType(0)
    local_addr.setOTSAddress(idx_sig)
    sig_ots = WOTS_sign(message, SK.wots_private_keys[idx_sig], n, w, SK.SEED, local_addr)
    return SigWithAuthPath(sig_ots, auth)

# ------------------------------------------------------------------------------
# Функции генерации ключей
# ------------------------------------------------------------------------------
def XMSS_keyGen(height: int, n: int, w: int) -> XMSSKeypair:
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
    return XMSSKeypair(SK, PK, height, n, w)

def XMSS_keyGen_from_seed_phrase(seed_phrase: str, height: int, n: int, w: int,
                                 hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE):
    extended_key = seed_phrase_to_key(seed_phrase)
    SEED = hashlib.sha256(extended_key + b"SEED").digest()[:n]
    SK_PRF = hashlib.sha256(extended_key + b"SK_PRF").digest()[:n]
    OID = hashlib.sha256(extended_key + b"OID").digest()[:n]
    len_1, len_2, len_all = compute_lengths(n, w)
    wots_sk = []
    for i in range(0, 2 ** height):
        unique_seed = hashlib.sha256(extended_key + int_to_bytes(i, 4)).digest()[:n]
        wots_sk.append(WOTS_genSK_from_seed(len_all, n, unique_seed))
    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    SK.wots_private_keys = wots_sk
    SK.idx = 0
    SK.SK_PRF = SK_PRF
    SK.SEED = SEED
    adrs = ADRS()
    root = treeHash(SK, 0, height, adrs, w, len_all)
    SK.root_value = root
    PK.OID = OID
    PK.root_value = root
    PK.SEED = SEED
    PK.height = height
    PK.n = n
    PK.w = w
    return XMSSKeypair(SK, PK, height, n, w)

def XMSS_keyGen_from_private_key(private_key_hex: str, height: int, n: int, w: int,
                                 hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE):
    extended_key = bytes.fromhex(private_key_hex)
    SEED = hashlib.sha256(extended_key + b"SEED").digest()[:n]
    SK_PRF = hashlib.sha256(extended_key + b"SK_PRF").digest()[:n]
    OID = hashlib.sha256(extended_key + b"OID").digest()[:n]
    len_1, len_2, len_all = compute_lengths(n, w)
    wots_sk = []
    for i in range(0, 2 ** height):
        unique_seed = hashlib.sha256(extended_key + int_to_bytes(i, 4)).digest()[:n]
        wots_sk.append(WOTS_genSK_from_seed(len_all, n, unique_seed))
    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    SK.wots_private_keys = wots_sk
    SK.idx = 0
    SK.SK_PRF = SK_PRF
    SK.SEED = SEED
    adrs = ADRS()
    root = treeHash(SK, 0, height, adrs, w, len_all)
    SK.root_value = root
    PK.OID = OID
    PK.root_value = root
    PK.SEED = SEED
    PK.height = height
    PK.n = n
    PK.w = w
    return XMSSKeypair(SK, PK, height, n, w)

# ------------------------------------------------------------------------------
# Функции подписи и верификации XMSS
# ------------------------------------------------------------------------------
def XMSS_sign(message: bytearray, SK: XMSSPrivateKey, n: int, w: int, address: ADRS, h: int) -> SigXMSS:
    len_1, len_2, len_all = compute_lengths(n, w)
    idx_sig = SK.idx
    SK.idx += 1
    # print(f"🔹 Подписываем сообщение: {message.hex()} (длина {len(message)} байт)")
    # print(f"🔹 Используем SK.SEED: {SK.SEED.hex()}")
    # print(f"🔹 Используем SK.SK_PRF: {SK.SK_PRF.hex()}")
    r = PRF_XMSS(SK.SK_PRF, to_byte(idx_sig, 4), len_1)
    arrayOfBytes = bytearray(r)
    arrayOfBytes.extend(SK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(idx_sig, n)))
    M2 = H_msg(arrayOfBytes, message, len_1)
    # print(f"🔹 Хешированное сообщение (M2): {M2.hex()}")
    sig = treeSig(M2, SK, address, w, len_all, idx_sig, h, n)
    return SigXMSS(idx_sig, r, sig.sig_ots, sig.auth)

def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey, n: int, w: int):
    address = ADRS()
    height = PK.height
    SEED = PK.SEED
    print(f"🔹 Проверяем подпись для сообщения: {M.hex()} (длина {len(M)} байт)")
    print(f"🔹 Используем SEED из публичного ключа: {SEED.hex()}")
    print(f"🔹 Используем root_value из публичного ключа: {PK.root_value.hex()}")
    len_1, len_2, len_all = compute_lengths(n, w)
    arrayOfBytes = bytearray()
    arrayOfBytes.extend(Sig.r)
    arrayOfBytes.extend(PK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(Sig.idx_sig, n)))
    M2 = H_msg(arrayOfBytes, M, len_1)
    print(f"🔹 Хешированное сообщение при проверке (M2): {M2.hex()}")
    node = XMSS_rootFromSig(Sig.idx_sig, Sig.sig_ots, Sig.auth, M2, height, w, SEED, address, n)
    print(f"🔹 Восстановленный root: {node.hex()}")
    print(f"🔹 Ожидаемый root: {PK.root_value.hex()}")
    return node == PK.root_value

# ------------------------------------------------------------------------------
# Функции работы с seed-фразой и сериализация ключей
# ------------------------------------------------------------------------------
def create_extended_secret_key(hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE, height=Protocol.DEFAULT_HEIGHT):
    secret_key = secrets.token_bytes(35)
    combined_parameters = (hash_function_code << 6) | height
    parameters = struct.pack('B', combined_parameters)
    extended_key = parameters + secret_key
    return extended_key

def extract_parameters_from_key(extended_key):
    combined_parameters = struct.unpack('B', extended_key[:1])[0]
    hash_function_code = (combined_parameters >> 6) & 0b11
    height = combined_parameters & 0b111111
    return hash_function_code, height, extended_key

def key_to_seed_phrase(key: bytes):
    if len(key) != 36:
        raise ValueError("Key must be exactly 36 bytes long")
    bit_string = ''.join(f'{byte:08b}' for byte in key)
    seed_phrase = ' '.join(word_list[int(bit_string[i:i+12], 2)] for i in range(0, 288, 12))
    return seed_phrase

def seed_phrase_to_key(seed_phrase: str):
    indices = [word_list.index(word) for word in seed_phrase.split()]
    bit_string = ''.join(f'{index:012b}' for index in indices)
    byte_array = bytearray(int(bit_string[i:i+8], 2) for i in range(0, 288, 8))
    return bytes(byte_array)

def keypair_to_json(keypair: XMSSKeypair):
    return {
        'height': keypair.height,
        'n': keypair.n,
        'w': keypair.w,
        'private_key': {
            'wots_private_keys': [[key.hex() for key in wots_key] for wots_key in keypair.SK.wots_private_keys],
            'idx': keypair.SK.idx,
            'SK_PRF': keypair.SK.SK_PRF.hex() if isinstance(keypair.SK.SK_PRF, bytes) else keypair.SK.SK_PRF,
            'root_value': keypair.SK.root_value.hex(),
            'SEED': keypair.SK.SEED.hex() if isinstance(keypair.SK.SEED, bytes) else keypair.SK.SEED
        },
        'public_key': {
            'OID': keypair.PK.OID.hex() if isinstance(keypair.PK.OID, bytes) else keypair.PK.OID,
            'root_value': keypair.PK.root_value.hex(),
            'SEED': keypair.PK.SEED.hex() if isinstance(keypair.PK.SEED, bytes) else keypair.PK.SEED
        }
    }

def save_keys_to_file(keypair: XMSSKeypair, file_path: str):
    data = keypair_to_json(keypair)
    with open(file_path, 'w') as file:
        json.dump(data, file)

def keypair_from_json(keypair_json):
    height = keypair_json['height']
    n = keypair_json['n']
    w = keypair_json['w']
    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    SK.wots_private_keys = [
        [bytes.fromhex(key_hex) for key_hex in wots_key]
        for wots_key in keypair_json['private_key']['wots_private_keys']
    ]
    SK.idx = keypair_json['private_key']['idx']
    SK.SK_PRF = bytes.fromhex(keypair_json['private_key']['SK_PRF'])
    SK.root_value = bytes.fromhex(keypair_json['private_key']['root_value'])
    SK.SEED = bytes.fromhex(keypair_json['private_key']['SEED'])
    PK.OID = bytes.fromhex(keypair_json['public_key']['OID'])
    PK.root_value = bytes.fromhex(keypair_json['public_key']['root_value'])
    PK.SEED = bytes.fromhex(keypair_json['public_key']['SEED'])
    PK.height = height
    PK.n = n
    PK.w = w
    return XMSSKeypair(SK, PK, height, n, w)

def load_keys_from_file(file_path: str) -> XMSSKeypair:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return keypair_from_json(data)

# ------------------------------------------------------------------------------
# Класс-обертка для XMSS
# ------------------------------------------------------------------------------
class XMSS:
    def __init__(self, height, n, w, seed_phrase, private_key, address, key_pair, idx = 0, log=Log()):
        self.height = height
        self.n = n
        self.w = w
        self.seed_phrase = seed_phrase
        self.private_key = private_key
        self.address = address
        self.keyPair = key_pair
        self.keyPair.SK.idx = idx
        self.log = log
    def count_sign(self):
        return self.keyPair.PK.max_height() - self.keyPair.SK.idx
    @classmethod
    def create(cls, height=5, hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE, key=None, seed_phrase=None):
        n = 32
        w = 16
        if seed_phrase is not None:
            key_pair = XMSS_keyGen_from_seed_phrase(seed_phrase, height, n, w, hash_function_code)
            extended_key = seed_phrase_to_key(seed_phrase)
        elif key is not None:
            if isinstance(key, str):
                key = bytes.fromhex(key)
            hash_function_code, height, extended_key = extract_parameters_from_key(key)
            key_pair = XMSS_keyGen_from_private_key(extended_key.hex(), height, n, w, hash_function_code)
            seed_phrase = key_to_seed_phrase(extended_key)
        else:
            extended_key = create_extended_secret_key(hash_function_code, height)
            seed_phrase = key_to_seed_phrase(extended_key)
            key_pair = XMSS_keyGen_from_private_key(extended_key.hex(), height, n, w, hash_function_code)
        address = key_pair.PK.generate_address(hash_function_code)
        return cls(height, n, w, seed_phrase, extended_key, address, key_pair)
    def sign(self, message):
        signature = XMSS_sign(message, self.keyPair.SK, self.n, self.w, ADRS(), self.height)
        return signature
    def to_json(self):
        return {
            'height': self.height,
            'n': self.n,
            'w': self.w,
            'idx': self.idx(),
            'seed_phrase': self.seed_phrase,
            'private_key': self.private_key.hex(),
            'address': self.address,
            'keyPair': keypair_to_json(self.keyPair),
        }
    @classmethod
    def from_json(cls, json_data):
        height = json_data['height']
        n = json_data['n']
        w = json_data['w']
        idx =  json_data['idx']
        seed_phrase = json_data['seed_phrase']
        private_key = bytes.fromhex(json_data['private_key'])
        address = json_data['address']
        key_pair = keypair_from_json(json_data['keyPair'])
        return cls(height, n, w, seed_phrase, private_key, address, key_pair, idx=idx)
    def set_idx(self, new_idx):
        new_idx_fixed = max(0, min(new_idx, self.keyPair.PK.max_height()))
        self.keyPair.SK.idx = new_idx_fixed
        return self.keyPair.SK.idx
    def idx(self):
        return self.keyPair.SK.idx
    def private_key_hex(self):
        return self.private_key.hex()


def private_key_hex_to_seed_phrase(private_key_hex: str) -> str:
    private_key_bytes = bytes.fromhex(private_key_hex)
    return key_to_seed_phrase(private_key_bytes)


def generate_private_key_and_seed_phrase(hash_function_code=Protocol.DEFAULT_HASH_FUNCTION_CODE,
                                         height=Protocol.DEFAULT_HEIGHT) -> (str, str):
    """
    Генерирует приватный ключ (расширённый ключ размером 36 байт) и соответствующую seed‑фразу.

    :param hash_function_code: код используемой хэш‑функции (0, 1 или 2)
    :param height: высота дерева (количество подписей будет 2^height)
    :return: кортеж (private_key_hex, seed_phrase)
    """
    # Генерируем расширённый приватный ключ (36 байт)
    extended_key = create_extended_secret_key(hash_function_code, height)
    # Преобразуем его в шестнадцатеричное представление
    private_key_hex = extended_key.hex()
    # Преобразуем ключ в seed‑фразу с помощью функции key_to_seed_phrase
    seed_phrase = key_to_seed_phrase(extended_key)
    return private_key_hex, seed_phrase
# ------------------------------------------------------------------------------
# Тестовый блок
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # seed_client1 = "word0001 word0002 word0003 word0004 word0005 word0006 word0007 word0008 word0009 word0010 word0011 word0012 word0013 word0014 word0015 word0016 word0017 word0018 word0019 word0020 word0021 word0022 word0023 word0024"

    # res = generate_private_key_and_seed_phrase()
    # print(res)
    # exit()

    # seed_client1 = "word0003 word0003 word0003 word0004 word0005 word0006 word0007 word0008 word0009 word0010 word0011 word0012 word0013 word0014 word0015 word0016 word0017 word0018 word0019 word0020 word0021 word0022 word0023 word0024"
    seed_client1 = "agreed oath stride petty rhexia isaac serum cool syntax ice mesh row liquid weight salute obtain admire seldom snowy plenty fair trend clever baby"
    height = 4      # 2^height подписей
    n = 32        # фиксированный размер хэш-вывода (32 байта)
    w = 16        # параметр Winternitz



    print("Количество подписей:", 2 ** height)

    # 1. Генерация ключей из seed-фразы
    keyPair_from_seed = XMSS_keyGen_from_seed_phrase(seed_client1, height, n, w)
    address_from_seed = keyPair_from_seed.PK.generate_address()

    print(f"Seed-фраза: {seed_client1}")
    print(f"Адрес из сид-фразы: {address_from_seed}")

    # 2. Извлечение приватного ключа (extended key)
    private_key_bytes = seed_phrase_to_key(seed_client1)
    private_key_hex = private_key_bytes.hex()

    seed_phrase = private_key_hex_to_seed_phrase(private_key_hex)
    print("seed_phrase rstore", seed_phrase)
    # private_key_hex = "00100200300400500600700800900a00b00c00d00e00f010011012013014015016017018"

    print(f"Приватный ключ (hex): {private_key_hex}")

    # 3. Генерация ключей на основе приватного ключа
    keyPair_from_private = XMSS_keyGen_from_private_key(private_key_hex, height, n, w)
    address_from_private = keyPair_from_private.PK.generate_address()
    print(f"Адрес из приватного ключа: {address_from_private}")

    # 4. Проверка детерминированности
    if address_from_seed != address_from_private:
        print("❌ Ошибка: адреса НЕ совпадают! Анализируем различия...")
        print("\n--- Различия в параметрах ---")
        print(f"SK.SEED из seed-фразы:      {keyPair_from_seed.SK.SEED.hex()}")
        print(f"SK.SEED из приватного ключа:{keyPair_from_private.SK.SEED.hex()}")
        print(f"SK.SK_PRF из seed-фразы:      {keyPair_from_seed.SK.SK_PRF.hex()}")
        print(f"SK.SK_PRF из приватного ключа:{keyPair_from_private.SK.SK_PRF.hex()}")
        print(f"OID из seed-фразы:      {keyPair_from_seed.PK.OID.hex()}")
        print(f"OID из приватного ключа:{keyPair_from_private.PK.OID.hex()}")
        raise ValueError("❌ Адреса не совпадают!")
    else:
        print("✅ Адреса совпадают, проверка пройдена!")

    # 5. Подпись сообщения
    message_client1 = bytearray(b'This is a message from client1 to be signed.')
    print("Делаем подпись...")
    signature_client1 = XMSS_sign(message_client1, keyPair_from_seed.SK, n, w, ADRS(), height)
    sig_bytes = signature_client1.to_bytes()
    print(f"Подпись: {signature_client1}, размер: {len(sig_bytes)} байт")
    sign_str = signature_client1.to_base64()
    pk_str = keyPair_from_seed.PK.to_hex()
    print("pk_str:", pk_str)
    print("sign_str:", sign_str)
    # Восстановление подписи
    PK = XMSSPublicKey.from_hex(pk_str)
    signature = SigXMSS.from_base64(sign_str)
    print("OTS idx:", signature.idx_sig)
    verification_result = XMSS_verify(signature, message_client1, PK, n, w)
    print(f"Результат верификации подписи: {'Подпись верна' if verification_result else 'Подпись неверна'}")


    x = XMSS()
