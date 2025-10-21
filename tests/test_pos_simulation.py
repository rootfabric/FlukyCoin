import shutil
import time
import uuid
from pathlib import Path

import pytest

from core.Block import Block
from core.protocol import Protocol
from crypto.xmss import XMSS
from storage.chain import Chain


class LocalNetworkSimulator:
    def __init__(self):
        self.nodes = []

    def register(self, node):
        self.nodes.append(node)

    def broadcast_block(self, sender, block: Block):
        payload = block.to_json()
        for node in self.nodes:
            if node is sender:
                continue
            node.receive_block(Block.from_json(payload))


class SimulatedNode:
    def __init__(self, name: str, chain: Chain, xmss: XMSS, network: LocalNetworkSimulator):
        self.name = name
        self.chain = chain
        self.xmss = xmss
        self.network = network
        self.reward_address = xmss.address
        self.network.register(self)

    def produce_block(self):
        selected = self.chain.select_validator_for_height()
        if selected != self.xmss.address:
            return None

        last_block = self.chain.last_block()
        last_time = last_block.timestamp_seconds if last_block is not None else int(self.chain.time())
        target_time = last_time + Protocol.BLOCK_TIME_SECONDS
        current_time = self.chain.time()
        timestamp = int(target_time if target_time > current_time else current_time)

        block = Block.create(
            self.chain.blocks_count(),
            self.chain.last_block_hash(),
            timestamp,
            [],
            address_miner=self.xmss.address,
            address_reward=self.reward_address,
        )
        block.make_sign(self.xmss)

        assert self.chain.validate_and_add_block(Block.from_json(block.to_json()))
        self.network.broadcast_block(self, block)
        return block

    def receive_block(self, block: Block):
        assert self.chain.validate_and_add_block(block)


@pytest.mark.parametrize("rounds", [5])
def test_pos_simulation(rounds):
    network = LocalNetworkSimulator()

    node_count = 3
    validators = []
    nodes = []
    expected_stakes = {}
    cleanup_dirs = []
    unique_suffix = uuid.uuid4().hex

    for index in range(node_count):
        xmss = XMSS.create(height=4)
        address = xmss.address
        stake = 1_000_000 + index * 100_000
        validators.append({"address": address, "stake": stake})
        expected_stakes[address] = stake

        node_dir = f"pos_sim_{unique_suffix}_{index}"
        chain = Chain(config={"host": "127.0.0.1", "port": 6000 + index}, node_dir_base=node_dir)
        cleanup_dirs.append(node_dir)
        nodes.append(SimulatedNode(f"node_{index}", chain, xmss, network))

    genesis_producer = nodes[0]
    genesis_timestamp = int(time.time())
    genesis_block = Block.create(
        block_number=0,
        previousHash=None,
        timestamp_seconds=genesis_timestamp,
        transactions=[],
        address_miner=genesis_producer.xmss.address,
        address_reward=genesis_producer.reward_address,
        validators=validators,
    )
    genesis_block.make_sign(genesis_producer.xmss)

    for node in nodes:
        assert node.chain.validate_and_add_block(Block.from_json(genesis_block.to_json()))

    expected_stakes[genesis_producer.reward_address] += int(Protocol.reward(block_number=0))

    for height in range(1, rounds + 1):
        leader_address = nodes[0].chain.select_validator_for_height(height)
        leader = next(node for node in nodes if node.xmss.address == leader_address)
        produced_block = leader.produce_block()
        assert produced_block is not None

        expected_stakes[leader_address] += int(Protocol.reward(block_number=height))

        expected_block_count = height + 1
        for node in nodes:
            assert node.chain.blocks_count() == expected_block_count
            assert node.chain.last_block().hash == produced_block.hash

    for node in nodes:
        for address, stake in expected_stakes.items():
            assert node.chain.stake_registry.get_stake(address) == stake

    for node in nodes:
        total = sum(node.chain.stake_registry.get_stake(v["address"]) for v in validators)
        assert total == node.chain.stake_registry.total_stake()

    for directory in cleanup_dirs:
        node_path = Path("node_data") / directory.replace(":", "_")
        if node_path.exists():
            shutil.rmtree(node_path)
