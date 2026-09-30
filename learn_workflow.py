"""合成学习入口：按 # %% 顺序运行，完成一次代际更新，再学习容量限制。

终端：python3 /home/xue/ACIT4610/CFLP/learn_workflow.py
本文件复用 cflp 中的实现，不导入其他学习脚本，不包含完整多代实验。
"""

# %% 1. 导入与真实数据：先认识 cap61 中的四类已知数据。
from random import Random

from cflp.data import Instance, load_instance, verify_data
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility, necessary_feasibility_issues
from cflp.nsga2 import (
    crowding_distance,
    environmental_selection,
    rank_and_crowding,
    tournament_winner,
)
from cflp.operators import crossover, mutate
from cflp.pareto import dominates
from cflp.representation import opened_facilities

verify_data()
small_instance = load_instance("cap61")
print("\n[1] 读取真实数据 cap61")
print("仓库数、客户数：", small_instance.n_facilities, small_instance.n_customers)
print("仓库 0：容量 S[0] =", small_instance.capacities[0],
      "开仓费 F[0] =", small_instance.fixed_costs[0])
print("客户 0：需求 d[0] =", small_instance.demands[0],
      "分配费 C[0][0] =", small_instance.allocation_costs[0][0])
print("C[i][j] 已包含客户全部需求，不能再乘 d[j]。")

# %% 2. 小案例复习：编码、容量和双目标；教学数据不用于正式实验。
toy = Instance(
    "teaching_example", (12, 7, 5), (100, 60, 70), (4, 3, 5),
    ((24, 18, 30), (8, 6, 40), (30, 24, 10)),
)
toy_assignment = [1, 1, 2]  # 位置是客户，值是仓库：B、B、C。
print("\n[2] 小案例复习")
print("分配：", toy_assignment, "负载：", check_feasibility(toy, toy_assignment))
print("目标：", evaluate(toy, toy_assignment))
assert evaluate(toy, toy_assignment) == (130, 24)

# %% 3. 转入 cap101：先比较三个直观方案，再进入种群搜索。
# cap101 每个仓库都能装下总需求，便于先学习进化步骤。
# 后面的随机分配依赖这个性质；不要直接将实例名改成 cap61。
instance = load_instance("cap101")
m, n = instance.n_facilities, instance.n_customers
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("本节的教学初始化要求每个仓库都能容纳全部需求。")
single_facility = [0] * n
cheapest = min(range(m), key=lambda i: instance.fixed_costs[i])
low_opening = [cheapest] * n
low_allocation = [
    min(range(m), key=lambda i: instance.allocation_costs[i][j])
    for j in range(n)
]
print("\n[3] cap101 的三个方案（不是完整 Pareto 前沿）")
example_objectives = {}
for label, assignment in (("A", single_facility), ("B", low_opening), ("C", low_allocation)):
    example_objectives[label] = evaluate(instance, assignment)
    print(label, "开放仓库数：", len(opened_facilities(instance, assignment)),
          "(f1, f2)：", example_objectives[label])
print("B 是否支配 A：", dominates(example_objectives["B"], example_objectives["A"]))
print("B 与 C 各有取舍；零开仓费用来自官方数据。")

# %% 4. 初始化种群：8 个个体，每个个体包含 50 个客户的完整分配。
# 与分开的学习文件使用相同随机种子，结果可以逐项对照。
population_size = 8
initialization_rng = Random(42)
population = []
for individual in range(population_size):
    pool_size = initialization_rng.randint(1, m)
    facility_pool = initialization_rng.sample(range(m), pool_size)
    assignment = [initialization_rng.choice(facility_pool) for _ in range(n)]
    population.append(assignment)

objectives = [evaluate(instance, assignment) for assignment in population]
# 仅计本次进化示范的评价，前面讲解方案的评价不属于这次运行。
evolution_evaluations = len(objectives)
print("\n[4] 初始种群（编号均从 0 开始）")
print("个体  开放仓库数       f1             f2")
for i, (f1, f2) in enumerate(objectives):
    count = len(opened_facilities(instance, population[i]))
    print(f"{i:4} {count:10} {f1:12.2f} {f2:14.2f}")
print("个体 0 的完整分配：", population[0])

# %% 5. 非支配排序与拥挤距离：先比较层级，再比较同层的疏密。
fronts, ranks, distances = rank_and_crowding(objectives)
print("\n[5] 分层与拥挤距离")
for rank, front in enumerate(fronts, start=1):
    print(f"第 {rank} 层：", front)
for i in range(population_size):
    print(f"个体 {i}：rank={ranks[i]}，crowding={distances[i]:.4f}")
print("inf 是边界保护标记；拥挤距离不能跨层优先于 rank。")
# 这个小型目标集合只用于手算拥挤距离，不替换 benchmark 数据。
teaching_points = [(1, 10), (2, 7), (5, 4), (9, 1)]
print("手算距离对照：", crowding_distance(teaching_points, [0, 1, 2, 3]))

# %% 6. 二元锦标赛：每次抽两个，选出一个父代，重复 8 次。
selection_rng = Random(7)
parent_indices = []
print("\n[6] 父代选择")
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    parent_indices.append(winner)
    print(f"抽中 {a}、{b} -> 选中 {winner}")
parents = [population[i].copy() for i in parent_indices]
print("父代编号：", parent_indices)
print("同一个个体可以多次成为父代；此时还没有产生子代。")

# %% 7. 父代配对、交叉、变异：产生 8 个子代，并逐个检查容量。
crossover_probability = 0.9  # 每对父代的概率。
mutation_probability = 0.02  # 每个客户位置的概率。
variation_rng = Random(21)
offspring = []
population_before_variation = [assignment.copy() for assignment in population]
print("\n[7] 生成子代")
for start in range(0, population_size, 2):
    print("父代配对：", parent_indices[start:start + 2])
    children = crossover(parents[start], parents[start + 1], crossover_probability, variation_rng)
    for crossed in children:
        child = mutate(crossed, m, mutation_probability, variation_rng)
        changes = [(j, crossed[j], child[j]) for j in range(n) if crossed[j] != child[j]]
        print("变异（客户、原仓库、新仓库）：", changes)
        check_feasibility(instance, child)
        offspring.append(child)
assert population == population_before_variation
assert parents == [population[i] for i in parent_indices]

# %% 8. 评价子代：可行之后才计算目标；重复个体也计一次评价。
offspring_objectives = [evaluate(instance, child) for child in offspring]
evolution_evaluations += len(offspring_objectives)
print("\n[8] 子代目标")
for i, values in enumerate(offspring_objectives):
    print(f"C{i}：", values)
print("本次进化示范评价次数：", evolution_evaluations)

# %% 9. 合并整个原种群和子代，重新分层；不是合并挑选的父代名单。
combined = population + offspring
combined_objectives = objectives + offspring_objectives
labels = [f"P{i}" for i in range(population_size)] + [f"C{i}" for i in range(len(offspring))]
combined_fronts, combined_ranks, combined_distances = rank_and_crowding(combined_objectives)
print("\n[9] 合并 16 个个体并重新排序：P=原种群，C=子代")
for rank, front in enumerate(combined_fronts, start=1):
    print(f"第 {rank} 层：", [labels[i] for i in front])

# %% 10. 环境选择：完整层优先；最后放不下的层按拥挤距离截取。
environment_rng = Random(11)
survivors = environmental_selection(combined_objectives, population_size, environment_rng)
next_population = [combined[i].copy() for i in survivors]
next_objectives = [combined_objectives[i] for i in survivors]
print("\n[10] 下一代")
print("保留来源：", [labels[i] for i in survivors])
for i, values in enumerate(next_objectives):
    print(f"新个体 {i}：", values)
for assignment in next_population:
    check_feasibility(instance, assignment)
assert len(next_population) == population_size
assert evolution_evaluations == 16
print("评价仍为 16 次，环境选择复用已计算的目标。")
print("已完成一次代际更新；后续多代循环应从 next_population 继续，不要每代重置种子。")

# %% 11. 回到 cap61：总需求不能放进单仓，构造时需要检查剩余容量。
# 与上面的进化示范分开：这里只展示可行构造，不执行 cap61 的进化算法。
if necessary_feasibility_issues(small_instance):
    raise ValueError("cap61 未通过必要条件检查。")
remaining = list(small_instance.capacities)
capacity_assignment = [-1] * small_instance.n_customers
customer_order = sorted(
    range(small_instance.n_customers), key=lambda j: (-small_instance.demands[j], j)
)
for customer in customer_order:
    demand = small_instance.demands[customer]
    candidates = [i for i in range(small_instance.n_facilities) if remaining[i] >= demand]
    if not candidates:
        raise RuntimeError("本次贪心构造失败；不能据此判断实例无解。")
    facility = min(candidates, key=lambda i: (remaining[i] - demand, i))
    capacity_assignment[customer] = facility
    remaining[facility] -= demand

capacity_loads = check_feasibility(small_instance, capacity_assignment)
print("\n[11] cap61 可行分配：先安排大客户")
for facility in sorted(set(capacity_assignment)):
    print(f"仓库 {facility}：{capacity_loads[facility]:g} / {small_instance.capacities[facility]:g}")
print("目标：", evaluate(small_instance, capacity_assignment))

# %% 12. 实例可行，不代表任意候选可行：把两个大客户移到同一个仓库。
largest, second_largest = customer_order[:2]
bad_assignment = capacity_assignment.copy()
bad_assignment[second_largest] = bad_assignment[largest]
print("\n[12] 不可行候选演示")
try:
    evaluate(small_instance, bad_assignment)
except ValueError as error:
    print("容量检查拒绝了候选：", error)
else:
    raise AssertionError("该候选应当超载。")
print("不能拆分需求、排除客户或修改数据。通用共享初始化与修复仍待实现。")
print("学习路线：读数 -> 评价 -> 种群 -> 排序 -> 父代 -> 子代 -> 下一代 -> 容量约束。")
print("本文件完成一代 NSGA-II 流程示范；完整多代循环、SPEA2 和正式实验仍是后续内容。")
