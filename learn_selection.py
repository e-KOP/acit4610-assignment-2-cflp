# %% 1. 重现上一节的 cap101 种群，不导入学习脚本，以免触发额外输出。
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.nsga2 import crowding_distance, rank_and_crowding, tournament_winner

instance = load_instance("cap101")
population_size = 8
rng = Random(42)
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires capacity >= total demand.")
population = []
for individual in range(population_size):
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    assignment = [rng.choice(facility_pool) for customer in range(instance.n_customers)]
    population.append(assignment)
objectives = [evaluate(instance, assignment) for assignment in population]

# %% 2. 每层内部单独计算拥挤距离。它是目标空间的疏密指标，不是仓库地理距离。
fronts, ranks, distances = rank_and_crowding(objectives)
print("分层：", fronts)
print("个体  层级  拥挤距离      f1           f2")
for i, (f1, f2) in enumerate(objectives):
    print(f"{i:4} {ranks[i]:5} {distances[i]:9.4f} {f1:11.2f} {f2:13.2f}")
print("inf 表示边界保护；不是费用无限大，也不能跨层压过更好的 rank。")

# %% 3. 单独展开真实第二层的距离计算；不改变任何原始数据。
front = fronts[1]
print("\n展开第二层：", front)
for objective in range(2):
    ordered = sorted(front, key=lambda i: (objectives[i][objective], i))
    minimum = objectives[ordered[0]][objective]
    maximum = objectives[ordered[-1]][objective]
    print(f"按 f{objective + 1} 排序：{ordered}；范围 {minimum:.2f} 到 {maximum:.2f}")
    if maximum == minimum:
        print("这一目标没有跨度，跳过，避免除以零。")
        continue
    print(f"边界个体 {ordered[0]}、{ordered[-1]} 的拥挤距离设为 inf。")
    for position in range(1, len(ordered) - 1):
        i = ordered[position]
        previous_value = objectives[ordered[position - 1]][objective]
        next_value = objectives[ordered[position + 1]][objective]
        contribution = (next_value - previous_value) / (maximum - minimum)
        print(f"个体 {i} 的 f{objective + 1} 贡献 = {contribution:.4f}")

# %% 4. 手算辅助：四个互不支配的点，帮助看清两个内部点的距离不同。
# 仅讲解距离，不作为 cap101 的数据或实验结果。
teaching_points = [(1, 10), (2, 7), (5, 4), (9, 1)]
print("\n手算点的拥挤距离：", crowding_distance(teaching_points, [0, 1, 2, 3]))
# 个体1：(5-1)/(9-1) + (10-4)/(10-1) = 1.166666...
# 个体2：(9-2)/(9-1) + (7-1)/(10-1) = 1.541666...

# %% 5. 同一层比较拥挤距离；不同层先比较 rank。
selection_rng = Random(7)
for a, b in ((6, 7), (3, 4), (5, 6)):
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    print(f"个体 {a} vs {b}：胜者 {winner}")
print("规则：rank 小优先；rank 相同时距离大优先；两者相同时随机。")

# %% 6. 随机抽两人比赛，选一个父代；独立重复 8 次。
# 单次抽样不重复；不同比赛可以再次抽到同一个人，也能多次选中同一个父代。
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    parent_indices.append(winner)
    print(f"第 {draw + 1} 次：抽中 {a}、{b} -> 选中 {winner}")
parents = [population[i].copy() for i in parent_indices]
print("父代编号：", parent_indices)
assert all(parent == population[i] and parent is not population[i]
           for parent, i in zip(parents, parent_indices))
print("这里只复制并选出了父代，没有创造新方案，也没有替换原种群。")
print("下一步：配对父代，交叉和变异产生子代，然后评价子代。")
