import os
import base64
import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

class FileEncryptor:
    def __init__(self, password):
        self.password = password.encode()  # Пароль должен быть в байтах

    def generate_key(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.password)
        return base64.urlsafe_b64encode(key)

    def encrypt_data_to_file(self, data, output_file):
        salt = os.urandom(16)  # Генерация соли
        key = self.generate_key(salt)  # Генерация ключа
        fernet = Fernet(key)  # Создание объекта Fernet
        data_json = json.dumps(data)  # Сериализация словаря в JSON
        encrypted_data = fernet.encrypt(data_json.encode())  # Шифрование данных
        with open(output_file, 'wb') as file:
            file.write(salt + encrypted_data)  # Запись соли и зашифрованных данных

    def decrypt_file(self, encrypted_file_path):
        with open(encrypted_file_path, 'rb') as file:
            file_data = file.read()
        salt = file_data[:16]  # Извлечение соли
        encrypted_data = file_data[16:]  # Извлечение зашифрованных данных
        key = self.generate_key(salt)  # Генерация ключа из пароля
        fernet = Fernet(key)  # Создание объекта Fernet для расшифровки
        decrypted_data = fernet.decrypt(encrypted_data)
        data_json = decrypted_data.decode()  # Декодирование из байтов в строку
        return json.loads(data_json)  # Десериализация JSON обратно в словарь
if __name__ == '__main__':
    ## Пример использования
    password = 'очень сложный пароль'
    file_encryptor = FileEncryptor(password)

    data = {
        "secret": "Секретное сообщение",
        "number": 42
    }
    output_file = 'encrypted_data.encrypted'

    # Шифрование данных в файл
    file_encryptor.encrypt_data_to_file(data, output_file)

    # Расшифровка данных из файла
    decrypted_data = file_encryptor.decrypt_file(output_file)
    print(decrypted_data)