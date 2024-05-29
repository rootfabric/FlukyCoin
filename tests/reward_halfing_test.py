import matplotlib.pyplot as plt
import math


# Упрощенная версия функции для построения графика
def reward(block_number, initial_reward=3000000, halving_interval=1500000, ratio1=0.5):
    # Определение количества прошедших халвингов
    halvings_passed = block_number // halving_interval

    # Учёт уменьшения награды из-за халвингов
    current_reward = initial_reward / (2 ** halvings_passed)

    # Применяем функцию с дополнительной нелинейностью для более сильного различия в наградах
    adjusted_ratio = (ratio1 ** 2) * math.log(1 + ratio1 * 100)

    # Умножаем текущую награду на скорректированный коэффициент
    reward = int(current_reward * adjusted_ratio)

    # Округление награды до миллиона
    reward = round(reward, -6)

    return reward


# Параметры для построения графика
total_blocks = 3000000
halving_interval = 1500000
initial_reward = 3000000
ratio1 = 0.5  # Можно изменить для исследования разных значений

# Вычисление наград для каждого блока
block_numbers = list(range(0, total_blocks + 1, 10000))
rewards = [reward(block, initial_reward, halving_interval, ratio1) for block in block_numbers]

# Построение графика
plt.figure(figsize=(12, 6))
plt.plot(block_numbers, rewards, label="Reward per Block")
plt.xlabel("Block Number")
plt.ylabel("Reward")
plt.title("Block Reward Reduction Over Time with Halvings")
plt.legend()
plt.grid(True)
plt.show()
