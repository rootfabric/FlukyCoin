import base64
import hashlib
import random
from hashlib import sha256
from crypto.xmss2 import XMSS, XMSS_verify, XMSSPublicKey, SigXMSS, XMSS_keyGen_from_private_key

THRESHOLD_99P = int((2 ** 256) * 0.99)

class ValidatorVRF_XMSS:
    def __init__(self, keypair, extended_key_hex: str):
        """
        Инициализация валидатора с переданной парой ключей XMSS.
        Параметр extended_key_hex – это исходный extended key (36 байт в hex-представлении),
        использованный для генерации пары ключей.
        """
        self.xmss = XMSS.create(height=keypair.height, key=extended_key_hex)  # Используем правильный extended key

    def get_public_key(self):
        """Возвращает публичный ключ в hex-представлении."""
        return self.xmss.keyPair.PK.to_hex()

    def get_private_key(self):
        """Возвращает приватный ключ в hex-представлении."""
        return self.xmss.private_key.hex()

    def generate_vrf(self, prev_block_hash: str):
        """
        Генерирует VRF-значение и доказательство (подписывает хеш предыдущего блока).
        """
        input_data = prev_block_hash.encode()
        signature = self.xmss.sign(input_data)
        vrf_output = sha256(signature.to_bytes()).digest()
        return {
            "vrf_output": base64.b64encode(vrf_output).decode(),
            "vrf_proof": signature.to_base64(),
            "public_key": self.get_public_key()
        }

    @staticmethod
    def verify_vrf(public_key: str, prev_block_hash: str, vrf_output: str, vrf_proof: str) -> bool:
        """
        Проверяет VRF-значение, используя публичный ключ валидатора.
        """
        try:
            pk_xmss = XMSSPublicKey.from_hex(public_key)
            input_data = prev_block_hash.encode()
            proof_bytes = SigXMSS.from_base64(vrf_proof)
            output_bytes = base64.b64decode(vrf_output)

            # Верифицируем подпись
            verification_result = XMSS_verify(proof_bytes, input_data, pk_xmss, pk_xmss.n, pk_xmss.w)
            expected_vrf_output = sha256(proof_bytes.to_bytes()).digest()
            return verification_result and (expected_vrf_output == output_bytes)
        except Exception as e:
            print(f"Ошибка верификации VRF: {e}")
            return False

def select_validators(validators, prev_block_hash):
    """
    Выбирает валидаторов на основе VRF.
    - Генерирует VRF-значение для каждого валидатора.
    - Преобразует VRF-значение в число.
    - Сортирует список по убыванию VRF-значений.
    """
    selected = []
    for validator in validators:
        vrf_data = validator["instance"].generate_vrf(prev_block_hash)
        vrf_output_bytes = base64.b64decode(vrf_data["vrf_output"])
        vrf_value = int.from_bytes(vrf_output_bytes, byteorder="big")
        selected.append({
            "address": validator["address"],
            "instance": validator["instance"],
            "vrf_data": vrf_data,
            "vrf_value": vrf_value
        })

    # Сортировка по убыванию VRF-значения
    sorted_validators = sorted(selected, key=lambda x: x["vrf_value"], reverse=True)
    return sorted_validators


def select_leader_90p(validators, prev_block_hash):
    """
    Выбирает первого валидатора, чье VRF-значение меньше 90% от максимума (2^256).
    """
    selected = []
    for validator in validators:
        vrf_data = validator["instance"].generate_vrf(prev_block_hash)
        vrf_output_bytes = base64.b64decode(vrf_data["vrf_output"])
        vrf_value = int.from_bytes(vrf_output_bytes, byteorder="big")

        # Проверяем, не меньше ли vrf_value заданного порога
        if vrf_value > THRESHOLD_99P:
            selected.append({
                "address": validator["address"],
                "instance": validator["instance"],
                "vrf_data": vrf_data,
                "vrf_value": vrf_value
            })

    # Сортировка по убыванию VRF-значения
    sorted_validators = sorted(selected, key=lambda x: x["vrf_value"], reverse=True)
    return sorted_validators

def verify_selection(sorted_validators, prev_block_hash):
    """
    Проверяет корректность VRF для каждого валидатора в списке.
    """
    for validator in sorted_validators:
        vrf = validator["vrf_data"]
        valid = ValidatorVRF_XMSS.verify_vrf(vrf["public_key"], prev_block_hash, vrf["vrf_output"], vrf["vrf_proof"])
        if not valid:
            print(f"❌ VRF проверка НЕ пройдена для адреса: {validator['address']}")
        else:
            print(f"✅ VRF проверка пройдена для адреса: {validator['address']}")

if __name__ == '__main__':
    # Используем реальные приватные ключи для генерации XMSS
    # Для validator1
    xmss1 = XMSS.create(key="45be862faf6e0dd0ec3d4b9da8f8e12b3e4e130f8ba5c7ce67d8b1894b80c1a7e4d9c29d")

    validator1 = ValidatorVRF_XMSS(
        keypair=xmss1.keyPair,
        extended_key_hex=xmss1.private_key_hex()
    )
    address1 = xmss1.address

    # Для validator2
    xmss2 = XMSS.create(key="45f82094df93616c349d2cbb587bea590e8396a44e457f99ce11324bc11d5e190c9bb9e9")

    validator2 = ValidatorVRF_XMSS(
        keypair=xmss2.keyPair,
        extended_key_hex=xmss2.private_key_hex()
    )
    address2 = xmss2.address



    # Для validator3
    xmss3 = XMSS.create(key="43bc879a2219e29793f8487782c1ef408dd9d72aee50570a2ac11260cb5588b66e3b7ce4")

    validator3 = ValidatorVRF_XMSS(
        keypair=xmss3.keyPair,
        extended_key_hex=xmss3.private_key_hex()
    )
    address3 = xmss3.address


    # Собираем валидаторов в список
    validators_list = [
        {"address": address1, "instance": validator1},
        {"address": address2, "instance": validator2},
        {"address": address3, "instance": validator3}
    ]

    prev_block_hash = "abc123def4567890"+str(random.random())

    # Выбор валидаторов на основе VRF
    sorted_validators = select_validators(validators_list, prev_block_hash)

    # sorted_validators = select_leader_90p(validators_list, prev_block_hash)
    print(sorted_validators)

    print("\n🔹 Порядок валидаторов (первый — лидер):")
    for i, validator in enumerate(sorted_validators, start=1):
        print(f"{i}. {validator['address']} - VRF value: {validator['vrf_value']}")

    print("\n🔍 Проверка корректности VRF для каждого валидатора:")
    verify_selection(sorted_validators, prev_block_hash)
