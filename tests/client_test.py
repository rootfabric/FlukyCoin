import time
from net.client import Client

def test_client_server_interaction():
    # Создание клиента и отправка запроса
    client = Client(host='localhost', port=5555)
    try:
        # Даем время серверу на запуск, если это первый запуск клиента после сервера
        # time.sleep(1)

        # Отправка запроса и получение ответа
        response = client.get_info(ignore_timer=True)

        # Ожидаемый результат
        expected_response = {'response': f'{"123"*1000000}'}

        # Проверка ответа
        assert response == expected_response, f"Expected {expected_response}, but got {response}"
        print("Test passed!")
    except AssertionError as error:
        print(error)
    finally:
        client.close()

if __name__ == '__main__':
    for i in range(10000):
        test_client_server_interaction()
