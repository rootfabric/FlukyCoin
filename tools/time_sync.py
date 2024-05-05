import ntplib
from time import time, ctime, sleep
import datetime

class NTPTimeSynchronizer:
    def __init__(self, ntp_server="pool.ntp.org"):
        self.ntp_server = ntp_server
        self.time_delta = None
        self.ntp_client = ntplib.NTPClient()
        self.synchronize_time()

    def synchronize_time(self):
        """Синхронизация времени с NTP-сервером и расчет дельты времени."""
        try:
            response = self.ntp_client.request(self.ntp_server, version=3)
            ntp_timestamp = response.tx_time
            system_timestamp = time()
            self.time_delta = ntp_timestamp - system_timestamp
            print(f"Время синхронизировано. Текущее NTP время: {ctime(ntp_timestamp)}")
            print(f"Дельта времени: {self.time_delta} секунд")
        except Exception as e:
            print(f"Не удалось получить время от NTP-сервера: {e}")

    def get_corrected_time(self):
        """Получение корректированного времени на основе сохраненной дельты."""
        if self.time_delta is not None:
            corrected_timestamp = time() + self.time_delta
            # return ctime(corrected_timestamp)
            return corrected_timestamp
        else:
            print("Время не было синхронизировано. Возвращение системного времени.")
            return time()
    def get_corrected_datetime(self):
        """Получение корректированной даты на основе сохраненной дельты."""
        return datetime.datetime.fromtimestamp(self.get_corrected_time())

if __name__ == '__main__':
    # Использование класса
    ntp_sync = NTPTimeSynchronizer("pool.ntp.org")

    # Получаем корректированное время
    print("Корректированное время:", ntp_sync.get_corrected_time())

    # Пример задержки
    sleep(10)  # Подождем 10 секунд

    # Получаем корректированное время снова
    print("Корректированное время после 10 секунд:", ntp_sync.get_corrected_time())
