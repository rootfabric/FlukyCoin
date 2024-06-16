import os, sys
from datetime import datetime, timedelta
import grpc
from flask import Flask, request, render_template
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Добавляем путь к директории с модулями
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_directory)

from protos import network_pb2, network_pb2_grpc
from wallet_app.Wallet import Wallet

app = Flask(__name__)
wallet = Wallet()
# node_addresses = '192.168.0.26:9334'
node_addresses = '5.35.98.126:9333'


@app.route('/', methods=['GET', 'POST'])
def index():
    node_info = get_info()
    if request.method == 'POST':
        address = request.form['address']
        info = wallet.info(address)
        balance = info.balance / 10000000

        return render_template('index.html', address=address, balance=balance, node_info=node_info)
    return render_template('index.html', node_info=node_info)


@app.route('/addresses', methods=['GET'])
def addresses():
    channel = grpc.insecure_channel(node_addresses)
    stub = network_pb2_grpc.NetworkServiceStub(channel)
    response = stub.GetAllAddresses(network_pb2.Empty())
    sorted_addresses = sorted(response.addresses, key=lambda x: float(x.balance) / 10000000, reverse=True)
    return render_template('addresses.html', sorted_addresses=sorted_addresses)


def get_info(server=node_addresses):
    channel = grpc.insecure_channel(server)
    stub = network_pb2_grpc.NetworkServiceStub(channel)
    try:
        response = stub.GetNetInfo(network_pb2.Empty())
        logging.debug(f'Received response: {response}')
        return parse_node_info(response)
    except grpc._channel._InactiveRpcError as e:
        logging.error(f'gRPC error: {e}')
        return {
            "synced": "N/A",
            "blocks": "N/A",
            "last_block_time": "N/A",
            "last_block_hash": "N/A",
            "difficulty": "N/A",
            "peers": [],
            "peer_count": 0
        }


def parse_node_info(response):
    last_block_time = datetime.fromtimestamp(response.last_block_time).strftime(
        "%Y-%m-%d %H:%M:%S") if response.last_block_time else "N/A"
    peers = []
    for peer in response.peers_info:
        if peer:
            network_info = peer.network_info if peer.network_info else 'N/A'
            synced = peer.synced if peer.synced else 'N/A'
            blocks = peer.blocks if peer.blocks else 'N/A'
            latest_block = peer.latest_block if peer.latest_block else 'N/A'
            uptime = str(timedelta(seconds=int(peer.uptime))) if peer.uptime else 'N/A'
            difficulty = peer.difficulty if peer.difficulty else 'N/A'

            peers.append({
                "network_info": network_info,
                "synced": synced,
                "blocks": blocks,
                "latest_block": latest_block,
                "uptime": uptime,
                "difficulty": difficulty
            })

    return {
        "synced": response.synced if response.synced else 'N/A',
        "blocks": response.blocks if response.blocks else 'N/A',
        "last_block_time": last_block_time,
        "last_block_hash": response.last_block_hash if response.last_block_hash else 'N/A',
        "difficulty": response.difficulty if response.difficulty else 'N/A',
        "peers": peers,
        "peer_count": len(peers)
    }


if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=80)
    app.run(debug=True, host=node_addresses.split(":")[0], port=80)
