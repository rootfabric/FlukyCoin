import argparse
import faulthandler
import os
import yaml

# from node.blockchain_node import BlockchainNode
from node.node_manager import NodeManager
from tools.config_loader import ConfigLoader

import sys
sys.path.append('/home/rdpuser/FlukyCoin/crypto')


def parse_arguments():
    parser = argparse.ArgumentParser(description='FluckyCoin node')
    parser.add_argument('--config', '-c', type=str, required=False,
                        default='node_config.yaml', help="Node host")
                        # default='node_config3.yaml', help="Node host")
                        # default='node_config_off.yaml', help="Node host")
    # parser.add_argument('--host', '-h', type=str, required=False,
    #                     default='localhost', help="Node host")
    # parser.add_argument('--port', '-p', type=str ,required=False,
    #                     default='5555', help="Node port")

    # parser.add_argument('--mining_thread_count', '-m', dest='mining_thread_count', type=int, required=False,
    #                     default=None, help="Number of threads for mining")
    # parser.add_argument('--quiet', '-q', dest='quiet', action='store_true', required=False, default=False,
    #                     help="Avoid writing data to the console")
    parser.add_argument("-l", "--loglevel", dest="logLevel", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()

    config_loader = ConfigLoader('config/', args.config)
    config = config_loader.load_config()

    # run_node(port, known_peers)

    node = NodeManager(config)

    try:
        node.run_node()
    except KeyboardInterrupt:
        pass

