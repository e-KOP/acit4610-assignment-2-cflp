# %% 教学小例子：这不是 OR-Library benchmark，不用于正式实验。
from cflp.data import Instance
from cflp.evaluation import evaluate
from cflp.feasibility import facility_loads
from cflp.representation import opened_facilities
from itertools import product

instance = Instance(
    name="teaching_example",
    capacities=(12, 7, 5),
    fixed_costs=(100, 60, 70),
    demands=(4, 3, 5),
    allocation_costs=((24, 18, 30), (8, 6, 40), (30, 24, 10)),
)

# %% A=0, B=1, C=2。每个位置对应一个客户。
assignment = [1, 1, 2]  # [B, B, C]
print("客户分配：", assignment)
print("开放仓库：", opened_facilities(instance, assignment))
print("各仓库负载：", facility_loads(instance, assignment))

# %% 先检查可行性，再计算 f1 和 f2。
f1, f2 = evaluate(instance, assignment)
print("开仓费用 f1 =", f1)
print("分配费用 f2 =", f2)
assert (f1, f2) == (130, 24)

# %% 将全部客户交给 B，会超载；不能把这个方案当作可行结果。
try:
    evaluate(instance, [1, 1, 1])
except ValueError as error:
    print("预期的不可行提示：", error)

# %% 练习：先手算以下两个方案，再取消注释执行，核对结果。
print(evaluate(instance, [0, 0, 0]))
print(evaluate(instance, [0, 1, 2]))
# 下一步：自己用 itertools.product 枚举 3**3 种分配，筛出可行解。
# %% 枚举所有分配，保留可行解

feasible_solutions = []
total_count = 0

for assignment in product(
    range(instance.n_facilities),
    repeat=instance.n_customers,
):
    total_count += 1

    try:
        f1, f2 = evaluate(instance, assignment)
    except ValueError:
        # evaluate 检查到不可行方案，跳过本次循环。
        continue

    feasible_solutions.append((assignment, f1, f2))

print("全部方案数：", total_count)
print("可行方案数：", len(feasible_solutions))
print("不可行方案数：", total_count - len(feasible_solutions))

for assignment, f1, f2 in feasible_solutions:
    print(f"分配={assignment}, 开仓费用={f1}, 分配费用={f2}")