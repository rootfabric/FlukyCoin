import os, sys
from datetime import datetime
import grpc
from flask import Flask, request, render_template

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
    sorted_addresses = sorted(response.addresses, key=lambda x: float(x.balance)/10000000, reverse=True)
    return render_template('addresses.html', sorted_addresses=sorted_addresses)

def get_info(server=node_addresses):
    channel = grpc.insecure_channel(server)
    stub = network_pb2_grpc.NetworkServiceStub(channel)
    response = stub.GetNetInfo(network_pb2.Empty())
    return parse_node_info(response)

def parse_node_info(response):
    last_block_time = datetime.fromtimestamp(response.last_block_time).strftime("%Y-%m-%d %H:%M:%S") if response.last_block_time else "N/A"
    return {
        "synced": response.synced,
        "blocks": response.blocks,
        "peers": list(response.peers),
        "peer_count": len(response.peers),
        "last_block_time": last_block_time,
        "last_block_hash": response.last_block_hash,
        "difficulty":response.difficulty
    }

if __name__ == '__main__':
    # app.run(debug=True, port=80)
    app.run(debug=False, host='5.35.98.126', port=80)
