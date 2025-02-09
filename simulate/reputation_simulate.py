import random
from hashlib import sha256
import matplotlib.pyplot as plt


# Класс Node – представляет узел сети
class Node:
    def __init__(self, name):
        self.name = name
        self.reputation_tokens = 0
        self.vrf_value = int(sha256(name.encode()).hexdigest(), 16)
        self.balance = 0

    def generate_vrf_output(self, last_block_hash):
        """Compute VRF output based on last_block_hash and node name (simplified)."""
        seed_str = str(last_block_hash) + self.name
        rng = random.Random(seed_str)  # Используем локальный генератор случайных чисел
        self.vrf_value = rng.getrandbits(256)
        return self.vrf_value


def select_validators_by_proximity(validators, block_hash_value):
    """Выбирает валидаторов по VRF-близости к хешу блока."""
    selected = []
    for validator in validators:
        diff = abs(validator.vrf_value - block_hash_value)
        selected.append({"address": validator.name, "difference": diff})
    return sorted(selected, key=lambda x: x["difference"])


class ReputationSimulator:
    def __init__(self, num_nodes):
        self.nodes_count = 0
        self.nodes = []
        self.reputation_history = {}
        self.add_nodes(num_nodes)
        self.steps = 0

    def add_nodes(self, num_nodes):
        for i in range(num_nodes):
            self.add_node()

    def add_node(self):
        self.nodes_count += 1
        node_name = f"node_{self.nodes_count}"
        new_node = Node(node_name)
        self.nodes.append(new_node)
        # Заполняем историю для нового узла нулями за уже прошедшие блоки
        history_length = len(next(iter(self.reputation_history.values()))) if self.reputation_history else 0
        self.reputation_history[node_name] = [0] * history_length

    def step(self):
        """Эмулируем один блок с динамическими порогами и сбалансированными наградами/штрафами."""
        last_block_hash = random.getrandbits(256)
        for node in self.nodes:
            node.generate_vrf_output(last_block_hash)

        # Расчет динамических порогов на основе квантилей распределения репутации
        reputations = sorted([node.reputation_tokens for node in self.nodes])
        n = len(reputations)
        idx_validator = int(0.7 * n)
        idx_leader = int(0.9 * n)
        # Используем базовый минимум для порогов: 10 для валидаторов и 50 для лидера
        validator_threshold = max(10, reputations[min(idx_validator, n - 1)])
        leader_threshold = max(50, reputations[min(idx_leader, n - 1)])
        self.VALIDATOR_THRESHOLD = validator_threshold
        self.LEADER_THRESHOLD = leader_threshold

        # Рассчитываем средний уровень репутации
        # avg_reputation = sum(node.reputation_tokens for node in self.nodes) / len(self.nodes)
        #
        # # Динамические пороги (с запасом на начальном этапе)
        # self.VALIDATOR_THRESHOLD = max(450, avg_reputation * 0.5)
        # self.LEADER_THRESHOLD = max(490, avg_reputation * 0.9)
        # self.VALIDATOR_THRESHOLD = 300
        # self.LEADER_THRESHOLD = 400

        # Для отладки можно вывести пороги и среднее значение (если необходимо)
        avg_rep = sum(reputations) / n if n else 0
        if self.steps % 1000 == 0:
            print(
                f"Avg rep: {avg_rep:.2f}, Validator threshold: {self.VALIDATOR_THRESHOLD}, Leader threshold: {self.LEADER_THRESHOLD}")

        sorted_nodes = select_validators_by_proximity(self.nodes, last_block_hash)
        leader, validators = self.select_leader_and_validators(sorted_nodes)

        # Обновление баланса лидера
        leader.balance += 1

        # Награды (балансируем награды и штрафы)
        LEADER_REWARD = 30
        VALIDATOR_REWARD = 10
        PING_REWARD = 20
        PING_PROBABILITY = 1 / 1000
        MAX_REPUTATION_TOKEN = 500

        leader.reputation_tokens = min(leader.reputation_tokens + LEADER_REWARD, MAX_REPUTATION_TOKEN)
        for v in validators:
            v.reputation_tokens = min(v.reputation_tokens + VALIDATOR_REWARD, MAX_REPUTATION_TOKEN)

        # Пинг-вознаграждения для случайных узлов
        for node in self.nodes:
            if random.random() < PING_PROBABILITY:
                node.reputation_tokens = min(node.reputation_tokens + PING_REWARD, MAX_REPUTATION_TOKEN)

        # Штрафы (балансируем вероятность и величину штрафа)
        LEADER_PENALTY_PROBABILITY = 1 / 5000  # Лидер получает штраф реже
        VALIDATOR_PENALTY_PROBABILITY = 1 / 1000  # Валидаторы получают штраф немного чаще
        LEADER_PENALTY_AMOUNT = 200
        VALIDATOR_PENALTY_AMOUNT = 100

        # Штраф для лидера
        if random.random() < LEADER_PENALTY_PROBABILITY:
            leader.reputation_tokens = max(0, leader.reputation_tokens - LEADER_PENALTY_AMOUNT)

        # Штраф для валидаторов
        for v in validators:
            if random.random() < VALIDATOR_PENALTY_PROBABILITY:
                v.reputation_tokens = max(0, v.reputation_tokens - VALIDATOR_PENALTY_AMOUNT)

        # Обновляем историю репутации
        for node in self.nodes:
            self.reputation_history[node.name].append(node.reputation_tokens)

        self.steps += 1

    def select_leader_and_validators(self, sorted_nodes):
        """Выбираем лидера и валидаторов на основании динамических порогов и VRF-близости."""
        max_validators = max(1, len(self.nodes) // 10)
        leader = None

        # Поиск кандидата на лидера, который соответствует порогу
        for candidate in sorted_nodes:
            node = next(n for n in self.nodes if n.name == candidate["address"])
            if node.reputation_tokens >= self.LEADER_THRESHOLD:
                leader = node
                break
        # Если ни один узел не достиг порога лидера – выбираем ближайшего кандидата
        if leader is None:
            leader = next(n for n in self.nodes if n.name == sorted_nodes[0]["address"])

        # Выбираем валидаторов по порогу валидатора
        validators = [n for n in self.nodes if n.name in [c["address"] for c in sorted_nodes]
                      and n.name != leader.name and n.reputation_tokens >= self.VALIDATOR_THRESHOLD]

        # Если валидаторов меньше, чем требуется, дополняем выборку оставшимися узлами по близости
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
        sorted_nodes = sorted(self.nodes, key=lambda node: node.balance, reverse=True)
        print("=" * 100)
        print("Days:", self.steps / (60 * 24))
        for node in sorted_nodes:
            print(f"{node.name} Reputation: {node.reputation_tokens} Balance: {node.balance}")


if __name__ == '__main__':
    # Имитируем сеть из нескольких узлов
    sim = ReputationSimulator(num_nodes=3)

    sim.run_simulation(num_blocks=10000)

    sim.add_nodes(3)

    sim.run_simulation(num_blocks=30000)

    sim.add_nodes(30)

    sim.run_simulation(num_blocks=300000)
    #
    # sim.add_nodes(50)
    #
    # sim.run_simulation(num_blocks=30000)

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
