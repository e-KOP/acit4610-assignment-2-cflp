# %% 1. 重现前几节的 cap101 种群。此段仅复习，不改变初始化规则。
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility
from cflp.nsga2 import environmental_selection, rank_and_crowding, tournament_winner
from cflp.operators import crossover, mutate

instance = load_instance("cap101")
population_size = 8
rng = Random(42)
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires capacity >= total demand.")
population = []
for individual in range(population_size):
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    population.append([rng.choice(facility_pool) for customer in range(instance.n_customers)])
objectives = [evaluate(instance, assignment) for assignment in population]
fronts, ranks, distances = rank_and_crowding(objectives)

# %% 2. 重现父代选择、交叉与变异，生成并评价八个子代。
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    parent_indices.append(tournament_winner(a, b, ranks, distances, selection_rng))
variation_rng = Random(21)
offspring = []
for start in range(0, population_size, 2):
    parent_a = population[parent_indices[start]]
    parent_b = population[parent_indices[start + 1]]
    children = crossover(parent_a, parent_b, 0.9, variation_rng)
    for child in children:
        offspring.append(mutate(child, instance.n_facilities, 0.02, variation_rng))
offspring_objectives = [evaluate(instance, child) for child in offspring]

# %% 3. 合并的是整个原种群，不是锦标赛挑出的父代名单。
combined = population + offspring
combined_objectives = objectives + offspring_objectives
labels = [f"P{i}" for i in range(population_size)] + [f"C{i}" for i in range(len(offspring))]
print("P=原种群个体，C=子代；后面的编号均从 0 开始。")
print("合并个体数：", len(combined))
print("合并后的 0..7 对应 P0..P7，8..15 对应 C0..C7。")

# %% 4. 在合并集合中重新分层；原来的层级和拥挤距离不能直接沿用。
combined_fronts, combined_ranks, combined_distances = rank_and_crowding(combined_objectives)
for rank, front in enumerate(combined_fronts, start=1):
    print(f"第 {rank} 层：", [labels[i] for i in front])

# %% 5. 完整的一层放得下就全部保留，只有放不下的那层需要按距离截取。
remaining = population_size
for rank, front in enumerate(combined_fronts, start=1):
    if remaining == 0:
        break
    print(f"还剩 {remaining} 个名额；第 {rank} 层有 {len(front)} 个个体。")
    if len(front) <= remaining:
        print("全部保留：", [labels[i] for i in front])
        remaining -= len(front)
    else:
        print("本层放不下，按拥挤距离从大到小选；同距离随机打破平局：")
        for i in front:
            print(f"  {labels[i]}：{combined_distances[i]:.4f}")
        break

# %% 6. 执行环境选择，只返回合并集合中的下标。
environment_rng = Random(11)
survivors = environmental_selection(combined_objectives, population_size, environment_rng)
print("\n保留的合并下标：", survivors)
print("保留的来源标签：", [labels[i] for i in survivors])
print("淘汰的来源标签：", [labels[i] for i in range(len(combined)) if i not in survivors])

# %% 7. 建立下一代，复用已计算的费用，不增加目标评价次数。
next_population = [combined[i].copy() for i in survivors]
next_objectives = [combined_objectives[i] for i in survivors]
print("\n新编号  来源    f1            f2")
for new_index, old_index in enumerate(survivors):
    f1, f2 = next_objectives[new_index]
    print(f"{new_index:6} {labels[old_index]:5} {f1:12.2f} {f2:14.2f}")
assert len(next_population) == population_size
assert len(set(survivors)) == population_size
for assignment in next_population:
    check_feasibility(instance, assignment)
print("评价次数仍为 16：初始化 8 次 + 子代 8 次；排序和保留不重新评价。")
print("完成一次代际更新。下一轮应从 next_population 开始，而不是原 population。")
print("随机种子在本文件仅初始化一次；以后写多代循环时，不要每代重置种子。")
print("下一步：接入评价预算与循环，连续运行多代；当前仍非完整实验。")
