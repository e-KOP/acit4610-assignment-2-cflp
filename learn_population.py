# %% 1. 一个个体 = 一个长度为 50 的客户分配；一个种群 = 多个个体。
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.pareto import dominates, nondominated_sort
from cflp.representation import opened_facilities

instance = load_instance("cap101")
population_size = 8
seed = 42
rng = Random(seed)

# 这段教学初始化依赖“任何单个仓库都能容纳全部需求”。不能用于 cap121。
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires each facility to hold total demand.")

# %% 2. 随机生成 8 个方案。重新执行此段会重置种子，便于重复核对。
rng = Random(seed)
population = []
for individual in range(population_size):
    # 先选一个仓库子集，让不同个体有机会使用不同数量的仓库。
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    print(individual, facility_pool)
    assignment = []
    for customer in range(instance.n_customers):
        assignment.append(rng.choice(facility_pool))
    # 子集中的仓库可能未被抽中；最终只有实际服务客户的仓库才算开放。
    population.append(assignment)

print("个体数：", len(population))

print("每个个体的客户数：", len(population[0]))

print("每个个体的完整分配：")
for i, assignment in enumerate(population):
    print(f"个体 {i}: {assignment}")

# %% 3. 每个方案先检查可行性，再计算两个费用。
objectives = []
for assignment in population:
    objectives.append(evaluate(instance, assignment))

print("\n个体  开放仓库数      f1            f2")
for i, assignment in enumerate(population):
    f1, f2 = objectives[i]
    count = len(opened_facilities(instance, assignment))
    print(f"{i:4} {count:10} {f1:12.2f} {f2:14.2f}")
print("本段评价次数：", len(objectives))

# %% 4. 查看支配关系：两个费用均不更高，并且至少一项更低。
print("\n支配关系：")
for a in range(population_size):
    for b in range(population_size):
        if dominates(objectives[a], objectives[b]):
            print(f"个体 {a} 支配个体 {b}")

# %% 5. 非支配排序：第一层不被任何个体支配；移除它后再找下一层。
fronts = nondominated_sort(objectives)
for rank, front in enumerate(fronts, start=1):
    print(f"第 {rank} 层：个体编号 {front}")

# %% 6. 把层级写回每个个体，便于下一步选择。
ranks = [0] * population_size
for rank, front in enumerate(fronts, start=1):
    for i in front:
        ranks[i] = rank

print("\n个体   层级      f1            f2")
for i, (f1, f2) in enumerate(objectives):
    print(f"{i:4} {ranks[i]:6} {f1:12.2f} {f2:14.2f}")
assert sorted(i for front in fronts for i in front) == list(range(population_size))
print("第一层只是当前 8 个方案中的非支配集合，不是真实全局 Pareto 前沿。")
print("尚未执行交叉、变异或进化；下一步学习同一层内的拥挤距离和父代选择。")
