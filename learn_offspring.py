# %% 1. 重现 cap101 的八个体种群，和前两节使用同样的随机过程。
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility
from cflp.nsga2 import rank_and_crowding, tournament_winner
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

# %% 2. 选择父代：这一步只选已有个体，没有产生新分配。
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    parent_indices.append(tournament_winner(a, b, ranks, distances, selection_rng))
parents = [population[i].copy() for i in parent_indices]
print("父代编号：", parent_indices)

# %% 3. 设置概率并两两配对。0.02 是每个客户的变异概率，不是整条染色体。
crossover_probability = 0.9
mutation_probability = 0.02
variation_rng = Random(21)  # 独立种子让本节可以重复运行核对。
offspring = []
before_population = [assignment.copy() for assignment in population]
for start in range(0, population_size, 2):
    print(f"\n父代配对：{parent_indices[start]} 和 {parent_indices[start + 1]}")
    parent_a, parent_b = parents[start], parents[start + 1]

    # 单点交叉：随机切一个位置，互换两个父代的后半段。
    # 具体随机切点见 cflp/operators.py；未触发交叉则返回父代的独立副本。
    crossed_a, crossed_b = crossover(parent_a, parent_b, crossover_probability, variation_rng)
    for parent, crossed in ((parent_a, crossed_a), (parent_b, crossed_b)):
        changed = [j for j in range(instance.n_customers) if crossed[j] != parent[j]]
        print("交叉后相对对应父代发生变化的客户编号：", changed)

    # 逐客户变异：触发时，把仓库编号改为另外一个合法仓库编号。
    for crossed in (crossed_a, crossed_b):
        child = mutate(crossed, instance.n_facilities, mutation_probability, variation_rng)
        changes = [(j, crossed[j], child[j]) for j in range(instance.n_customers)
                   if crossed[j] != child[j]]
        print("变异记录（客户编号, 原仓库, 新仓库）：", changes)
        # cap101 每个仓库均能容纳总需求，因此这里无需修复，但仍实际检查。
        check_feasibility(instance, child)
        offspring.append(child)

# %% 4. 此时有 8 个子代。对通过可行性检查的子代各评价一次。
offspring_objectives = [evaluate(instance, child) for child in offspring]
print("\n子代编号   开仓费用 f1     分配费用 f2")
for i, (f1, f2) in enumerate(offspring_objectives):
    print(f"{i:8} {f1:13.2f} {f2:15.2f}")
print("目标评价次数：初始种群 8 次 + 子代 8 次 =", len(objectives) + len(offspring_objectives))
assert len(offspring) == population_size
assert population == before_population
assert parents == [population[i] for i in parent_indices]
assert len({id(child) for child in offspring}) == population_size

# %% 5. 观察：子代不一定更优，也不一定与父代不同。
print("\n父代或子代的费用可能改善，也可能变差，不能假设交叉变异一定改进。")
print("原种群仍有 8 个，子代另有 8 个；本节尚未执行环境选择。")
print("下一步：合并这 16 个个体，重新分层、计算拥挤距离，保留 8 个进入下一代。")
