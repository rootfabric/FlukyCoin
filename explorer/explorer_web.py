import os, sys

# Получаем путь на директорию выше
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Добавляем этот путь в sys.path
sys.path.append(parent_directory)

import grpc
from flask import Flask, request, render_template_string
from protos import network_pb2, network_pb2_grpc
from wallet_app.Wallet import Wallet  # Убедитесь, что путь импорта корректен
from datetime import datetime

app = Flask(__name__)
wallet = Wallet()  # Инициализируйте ваш кошелек здесь

# node_addres= '5.35.98.126:9333'
node_addresses= '192.168.0.26:9334'

def parse_node_info(response):
    """ Преобразование ответа gRPC в словарь """
    last_block_time = response.last_block_time
    if last_block_time:
        last_block_time = datetime.fromtimestamp(last_block_time).strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_block_time = "N/A"

    return {
        "synced": response.synced,
        "blocks": response.blocks,
        "peers": list(response.peers),
        "peer_count": len(response.peers),
        "last_block_time": last_block_time
    }


def get_info(server="5.35.98.126:9333"):
    """ Информация с ноды """
    # Создание канала связи с сервером
    channel = grpc.insecure_channel(server)
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    # Запрос на получение информации о сети
    net_info_request = network_pb2.Empty()

    try:
        # Отправка запроса и получение ответа
        response = stub.GetNetInfo(net_info_request)
        return parse_node_info(response)

    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {str(e)}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    node_info = get_info()
    print(node_info)
    if node_info is None:
        return "Ошибка получения информации о ноде"

    if request.method == 'POST':
        address = request.form['address']
        try:
            info = wallet.info(address)  # Метод info должен возвращать объект с атрибутом balance
            balance = info.balance / 10000000  # Предполагаем, что баланс нужно сконвертировать
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Wallet Balance</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                        }
                        .balance-info {
                            font-size: 1.2em;
                            margin-top: 20px;
                        }
                        .address {
                            font-weight: bold;
                        }
                        .balance {
                            color: green;
                        }
                    </style>
                </head>
                <body>
                    <h1>Node Information</h1>
                    <p><strong>Synced:</strong> {{ node_info.synced }}</p>
                    <p><strong>Blocks:</strong> {{ node_info.blocks }}</p>
                    <p><strong>Peers ({{ node_info.peer_count }}):</strong></p>
                    <ul>
                        {% for peer in node_info.peers %}
                        <li>{{ peer }}</li>
                        {% endfor %}
                    </ul>
                    <p><strong>Last Block Time:</strong> {{ node_info.last_block_time }}</p>
                    <div class="balance-info">
                        <p class="address">Balance for address {{ address }}:</p>
                        <p class="balance">{{ balance }}</p>
                    </div>
                    <a href="/">Check another address</a>
                </body>
                </html>
            ''', address=address, balance=balance, node_info=node_info)
        except Exception as e:
            return f"An error occurred: {str(e)}"

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wallet Balance</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                }
                .balance-info {
                    font-size: 1.2em;
                    margin-top: 20px;
                }
                .address {
                    font-weight: bold;
                }
                .balance {
                    color: green;
                }
            </style>
        </head>
        <body>
            <h1>Node Information</h1>
            <p><strong>Synced:</strong> {{ node_info.synced }}</p>
            <p><strong>Blocks:</strong> {{ node_info.blocks }}</p>
            <p><strong>Peers ({{ node_info.peer_count }}):</strong></p>
            <ul>
                {% for peer in node_info.peers %}
                <li>{{ peer }}</li>
                {% endfor %}
            </ul>
            <p><strong>Last Block Time:</strong> {{ node_info.last_block_time }}</p>
            <h1>Enter Wallet Address</h1>
            <form method="post">
                <input type="text" name="address" placeholder="Enter wallet address" required>
                <input type="submit" value="Get Balance">
            </form>
        </body>
        </html>
    ''', node_info=node_info)

@app.route('/addresses', methods=['GET'])
def addresses():
    """Страница со списком всех адресов и их балансов."""
    # Создание канала связи с сервером
    # channel = grpc.insecure_channel('5.35.98.126:9333')  # Укажите адрес вашего сервера
    channel = grpc.insecure_channel(node_addresses)  # Укажите адрес вашего сервера
    stub = network_pb2_grpc.NetworkServiceStub(channel)

    # Запрос на получение всех адресов
    all_addresses_request = network_pb2.Empty()

    try:
        # Отправка запроса и получение ответа
        response = stub.GetAllAddresses(all_addresses_request)
        # Сортировка полученных адресов по балансу в порядке убывания
        sorted_addresses = sorted(response.addresses, key=lambda x: float(x.balance), reverse=True)
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>All Addresses</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        border: 1px solid #dddddd;
                        text-align: left;
                        padding: 8px;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                </style>
            </head>
            <body>
                <h1>All Addresses and Balances</h1>
                <table>
                    <tr>
                        <th>Address</th>
                        <th>Balance</th>
                    </tr>
                    {% for address_info in sorted_addresses %}
                    <tr>
                        <td>{{ address_info.address }}</td>
                        <td>{{ address_info.balance }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </body>
            </html>
        ''', sorted_addresses=sorted_addresses)

    except grpc.RpcError as e:
        print(f"Ошибка gRPC: {str(e)}")
        return "Ошибка получения данных о адресах"

if __name__ == '__main__':
    # app.run(debug=False, host='5.35.98.126', port=80)
    app.run()
