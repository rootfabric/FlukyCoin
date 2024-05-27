import logging
import os
import datetime
import sys
import time
import codecs

class Log:
    '''
    Клас для ведения логов
    '''

    def __init__(self, log_name="fc", stdout=True, save_log=True, log_level_text="INFO", work_dir='logs'):
        """ Инициализация класса"""

        self._log = logging.getLogger(log_name)
        self.save_log = save_log
        self.log_name = log_name
        self.log_level = log_level_text
        self.work_dir = work_dir if work_dir else 'logs'
        self.current_date = datetime.date.today()

        if save_log:
            self.create_log_directory()

        # можно задавать уровень логирования, во избежания записи лишней информации в файл
        if log_level_text == "CRITICAL":
            self._log.setLevel(logging.CRITICAL)
        elif log_level_text == "ERROR":
            self._log.setLevel(logging.ERROR)
        elif log_level_text == "DEBUG":
            self._log.setLevel(logging.DEBUG)
        elif log_level_text == "INFO":
            self._log.setLevel(logging.INFO)

        stream_formatter = logging.Formatter(
            '[%(asctime)-15s] %(message)s')

        # По умолчанию всю информацию выводим в консоль
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.stream_handler.setFormatter(stream_formatter)

        if stdout:
            # Добавляем если нет уже созданных заголовков
            if not self._log.handlers:
                self._log.addHandler(self.stream_handler)

        self.file_handler = None

    def create_log_directory(self):
        try:
            if not os.path.exists(self.work_dir):
                os.mkdir(self.work_dir)
        except Exception as ex:
            print(f'\n\nОшибка создания директории {self.work_dir}:\n', ex)
            self.work_dir = 'logs'
            try:
                if not os.path.exists(self.work_dir):
                    os.mkdir(self.work_dir)
            except Exception as ex:
                print(f'\n\nОшибка создания директории {self.work_dir} в рабочем каталоге:\n', ex)
                print('\nЛогирование осуществляется в консоль.')
                self.save_log = False

    def _check_open_file(self):
        """ Проверка открытого файла для логирования"""

        if self.save_log:
            today = datetime.date.today()
            if self.file_handler is None or self.current_date != today:
                self.current_date = today
                if self.file_handler:
                    self._log.removeHandler(self.file_handler)
                    self.file_handler.close()

                # создаем файл единожды только после того как была попытка записи логов
                if not os.path.isdir(self.work_dir):
                    os.mkdir(self.work_dir)

                log_formatter = logging.Formatter(
                    '%(asctime)-15s::%(levelname)s::%(filename)s::%(funcName)s::%(lineno)d::%(message)s')

                try:
                    self.file_handler = logging.FileHandler(
                        f"{self.work_dir}/{self.log_name}_{self.current_date}.log", encoding='utf-8')
                except Exception as e:
                    self.file_handler = logging.FileHandler(
                        f"logs/{self.log_name}_{self.current_date}.log", encoding='utf-8')
                self.file_handler.setFormatter(log_formatter)

                # Не накапливаем в потоках file_handler. Первый вывод в stdout. Второй в файл
                if len(self._log.handlers) < 2:
                    self._log.addHandler(self.file_handler)
                else:
                    self._log.handlers[1] = self.file_handler

    def close(self):
        self._log.handlers = []
        del self._log

    def debug(self, *args):
        self._check_open_file()
        self._log.debug(" ".join(args))

    def args_to_str(self, args):
        return [str(arg) if not isinstance(arg, str) else arg for arg in args]

    def info(self, *args, **kwargs):
        self._check_open_file()
        self._log.info(" ".join(self.args_to_str(args)))

    def warning(self, *args, **kwargs):
        self._check_open_file()
        self._log.warning(" ".join(self.args_to_str(args)))

    def error(self, *args, **kwargs):
        self._check_open_file()
        self._log.error(" ".join(self.args_to_str(args)))

    def exception(self, *args, **kwargs):
        self._check_open_file()
        self._log.exception(" ".join(self.args_to_str(args)), **kwargs)


if __name__ == '__main__':
    log = Log("test_log")
    while 1:
        log.info("тест")
        time.sleep(60*60)
