import hashlib
from typing import Dict, Iterable, List, Optional


class StakeWeightedSelector:
    """Детерминированный выбор валидатора пропорционально стейку."""

    @staticmethod
    def choose(validators: Iterable[Dict[str, int]], seed: bytes) -> Optional[Dict[str, int]]:
        candidates: List[Dict[str, int]] = []
        total_stake = 0

        for validator in validators:
            stake = int(validator.get("stake", 0))
            if stake <= 0:
                continue
            candidate = dict(validator)
            candidate["stake"] = stake
            candidates.append(candidate)
            total_stake += stake

        if total_stake <= 0 or not candidates:
            return None

        candidates.sort(key=lambda item: item.get("address", ""))

        random_bytes = hashlib.sha256(seed).digest()
        random_value = int.from_bytes(random_bytes, byteorder="big")
        target = random_value % total_stake

        cumulative = 0
        for validator in candidates:
            cumulative += validator["stake"]
            if target < cumulative:
                return validator

        return candidates[-1]

