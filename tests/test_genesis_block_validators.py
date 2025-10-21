import pytest

from core.Block import Block
from core.protocol import Protocol


def test_genesis_block_serialization_preserves_validators():
    validators = [
        {"address": "validator_b", "stake": "200"},
        ("validator_a", 100),
        {"address": "validator_c", "stake": 300, "public_key": "pk_c"},
    ]

    timestamp = 1716710000
    block = Block.create(
        0,
        Protocol.prev_hash_genesis_block.hex(),
        timestamp,
        [],
        address_miner="miner_address",
        address_reward="reward_address",
        validators=validators,
    )

    expected_validators = [
        {"address": "validator_a", "stake": 100},
        {"address": "validator_b", "stake": 200},
        {"address": "validator_c", "stake": 300, "public_key": "pk_c"},
    ]

    assert block.validators == expected_validators

    json_payload = block.to_json()
    restored = Block.from_json(json_payload)

    assert restored.validators == expected_validators
    assert restored.hash == block.hash
    assert restored.hash_block() == block.hash_block()


def test_non_genesis_block_rejects_validators():
    with pytest.raises(ValueError):
        Block.create(
            1,
            Protocol.prev_hash_genesis_block.hex(),
            1716710001,
            [],
            address_miner="miner_address",
            address_reward="reward_address",
            validators=[{"address": "validator_a", "stake": 10}],
        )


def test_validators_affect_block_hash():
    timestamp = 1716710002
    block_one = Block.create(
        0,
        Protocol.prev_hash_genesis_block.hex(),
        timestamp,
        [],
        address_miner="miner_address",
        address_reward="reward_address",
        validators=[{"address": "validator_a", "stake": 10}],
    )

    block_two = Block.create(
        0,
        Protocol.prev_hash_genesis_block.hex(),
        timestamp,
        [],
        address_miner="miner_address",
        address_reward="reward_address",
        validators=[{"address": "validator_b", "stake": 10}],
    )

    assert block_one.hash != block_two.hash
