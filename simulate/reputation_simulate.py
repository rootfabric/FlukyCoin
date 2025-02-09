import random
from hashlib import sha256
import matplotlib.pyplot as plt


# Класс Node – представляет узел сети
class Node:
    def __init__(self, name):
        self.name = name
        self.reputation_tokens = 0
        self.vrf_value = int(sha256(name.encode()).hexdigest(), 16)

    def generate_vrf_output(self, last_block_hash):
        """Вычисляем VRF-выход на основе last_block_hash и имени узла (упрощенно)."""
        seed_str = str(last_block_hash) + self.name
        random.seed(seed_str)
        self.vrf_value = random.getrandbits(256)
        return self.vrf_value


def select_validators_by_proximity(validators, block_hash_value):
    """Выбирает валидаторов по VRF-близости к хешу блока."""
    selected = []
    for validator in validators:
        diff = abs(validator.vrf_value - block_hash_value)
        selected.append({"address": validator.name, "difference": diff})
    return sorted(selected, key=lambda x: x["difference"])


class ReputationSimulator:
    LEADER_THRESHOLD = 1000  # порог репутации для лидерства
    VALIDATOR_THRESHOLD = 50  # порог репутации для валидатора
    nodes_count = 0
    nodes = []
    reputation_history = {}

    def __init__(self, num_nodes):
        self.add_nodes(num_nodes)

    def add_nodes(self, num_nodes):
        for i in range(num_nodes):
            self.add_node()

    def add_node(self):
        self.nodes_count += 1
        node_name = f"node_{self.nodes_count}"
        new_node = Node(node_name)
        self.nodes.append(new_node)

        # Заполняем историю нулями для синхронизации с прошедшими блоками
        self.reputation_history[node_name] = [0] * len(next(iter(self.reputation_history.values()), []))

    def step(self):
        """Эмулируем один блок с динамическим порогом"""

        last_block_hash = random.getrandbits(256)
        for node in self.nodes:
            node.generate_vrf_output(last_block_hash)

        # Рассчитываем средний уровень репутации
        avg_reputation = sum(node.reputation_tokens for node in self.nodes) / len(self.nodes)

        # Динамические пороги (с запасом на начальном этапе)
        self.VALIDATOR_THRESHOLD = max(10, avg_reputation * 0.5)
        self.LEADER_THRESHOLD = max(100, avg_reputation * 1.5)

        sorted_nodes = select_validators_by_proximity(self.nodes, last_block_hash)
        leader, validators = self.select_leader_and_validators(sorted_nodes)

        # Раздача репутационных токенов
        LEADER_REWARD = 1
        VALIDATOR_REWARD = 0.1
        PING_REWARD = 1
        PING_PROBABILITY = 1 / 100
        MAX_REPUTATION_TOKEN = 300

        leader.reputation_tokens = min(leader.reputation_tokens + LEADER_REWARD, MAX_REPUTATION_TOKEN)
        for v in validators:
            v.reputation_tokens = min(v.reputation_tokens + VALIDATOR_REWARD, MAX_REPUTATION_TOKEN)

        for node in self.nodes:
            if random.random() < PING_PROBABILITY:
                node.reputation_tokens = min(node.reputation_tokens + PING_REWARD, MAX_REPUTATION_TOKEN)

        LEADER_PENALTY_PROBABILITY = 1 / 500  # Лидер получает штраф раз в 500 блоков
        VALIDATOR_PENALTY_PROBABILITY = 1 / 300  # Валидаторы получают штраф раз в 300 блоков

        LEADER_PENALTY_AMOUNT = 50  # Штраф для лидера
        VALIDATOR_PENALTY_AMOUNT = 10  # Штраф для валидаторов

        # Штраф для лидера
        if random.random() < LEADER_PENALTY_PROBABILITY:
            leader.reputation_tokens = max(0, leader.reputation_tokens - LEADER_PENALTY_AMOUNT)

        # Штраф для валидаторов
        for v in validators:
            if random.random() < VALIDATOR_PENALTY_PROBABILITY:
                v.reputation_tokens = max(0, v.reputation_tokens - VALIDATOR_PENALTY_AMOUNT)
        for node in self.nodes:
            self.reputation_history[node.name].append(node.reputation_tokens)

    def select_leader_and_validators(self, sorted_nodes):
        """Выбираем лидера и валидаторов."""
        max_validators = max(1, len(self.nodes) // 3)
        leader = None

        for candidate in sorted_nodes:
            node = next(n for n in self.nodes if n.name == candidate["address"])
            if node.reputation_tokens >= self.LEADER_THRESHOLD:
                leader = node
                break

        if leader is None:
            leader = next(n for n in self.nodes if n.name == sorted_nodes[0]["address"])

        validators = [n for n in self.nodes if n.name in [c["address"] for c in sorted_nodes]
                      and n.name != leader.name and n.reputation_tokens >= self.VALIDATOR_THRESHOLD]

        if len(validators) < max_validators:
            for candidate in sorted_nodes:
                node = next(n for n in self.nodes if n.name == candidate["address"])
                if node.name != leader.name and node not in validators:
                    validators.append(node)
                    if len(validators) >= max_validators:
                        break

        return leader, validators[:max_validators]

    def run_simulation(self, num_blocks):
        for _ in range(num_blocks):
            self.step()

    def report(self):
        for node in self.nodes:
            print(f"{node.name} {node.reputation_tokens}")


if __name__ == '__main__':
    # Имитируем сеть из нескольких узлов
    sim = ReputationSimulator(num_nodes=50)

    sim.run_simulation(num_blocks=10000)

    sim.add_nodes(1)

    sim.run_simulation(num_blocks=10000)

    sim.add_nodes(1)

    sim.run_simulation(num_blocks=10000)

    sim.add_nodes(1)

    sim.run_simulation(num_blocks=10000)

    sim.add_nodes(1)

    sim.run_simulation(num_blocks=10000)

    sim.report()

    # Построение графика с учетом динамического добавления узлов
    plt.figure(figsize=(12, 6))

    for node_name, rep_values in sim.reputation_history.items():
        plt.plot(range(len(rep_values)), rep_values, label=node_name)

    plt.xlabel("Блоки")
    plt.ylabel("Репутационные токены")
    plt.title("Динамика изменения репутации узлов")
    # plt.legend()
    plt.grid(True)
    plt.show()
