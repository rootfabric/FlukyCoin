import hashlib
import base64
# from pyspx.xmss import XMSS_SHA2_10_256 as XMSS
import hashlib
import base64
import base58
from hashlib import sha256
from datetime import datetime

from crypto.xmss2 import XMSS, XMSS_verify, XMSSPublicKey, SigXMSS
class ValidatorVRF_XMSS:
    def __init__(self, keypair=None):
        """
        Инициализация валидатора. Если ключи не заданы, создаем новые.
        """
        if keypair:
            self.xmss = keypair  # Переданный экземпляр XMSS
        else:
            self.xmss = XMSS.create(height=5)  # Генерируем новую пару ключей

    def get_public_key(self):
        """Возвращает публичный ключ в base64."""
        return self.xmss.keyPair.PK.to_hex()

    def get_private_key(self):
        """Возвращает приватный ключ в base64 (для хранения нодой)."""
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

            # Передаём дополнительные параметры n и w из публичного ключа
            verification_result = XMSS_verify(proof_bytes, input_data, pk_xmss, pk_xmss.n, pk_xmss.w)

            # Повторно вычисляем хеш доказательства и сравниваем с предоставленным VRF-значением
            expected_vrf_output = sha256(proof_bytes.to_bytes()).digest()
            return verification_result and (expected_vrf_output == output_bytes)

        except Exception as e:
            print(f"Ошибка верификации VRF: {e}")
            return False



# --- Тестирование работы VRF на базе XMSS ---

# Генерируем ключи ноды
node = ValidatorVRF_XMSS()
print(f"🔑 Публичный ключ ноды: {node.get_public_key()}")

# Исходный хеш предыдущего блока
prev_block_hash = "abc123def4567890"

# Генерация VRF
vrf_data = node.generate_vrf(prev_block_hash)
print(f"🎲 VRF Output: {vrf_data['vrf_output']}")
print(f"✅ VRF Proof: {vrf_data['vrf_proof']}")

# Верификация VRF
is_valid = ValidatorVRF_XMSS.verify_vrf(vrf_data["public_key"], prev_block_hash, vrf_data["vrf_output"], vrf_data["vrf_proof"])
print(f"🔍 Верификация VRF: {is_valid}")