# %% 1. 读取真实 cap101，保留所有原始值。
# 终端：cd /home/xue/ACIT4610/CFLP，然后 python3 learn_cap101.py
from math import isclose

from cflp.data import load_instance, verify_data
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility, necessary_feasibility_issues
from cflp.representation import opened_facilities

verify_data()
instance = load_instance("cap101")
m = instance.n_facilities
n = instance.n_customers
print("仓库数 m：", m, "客户数 n：", n)
print("总需求：", sum(instance.demands))
print("每个仓库的容量：", instance.capacities[0])
assert not necessary_feasibility_issues(instance)

# %% 2. 构造一个最容易理解的方案：全部客户交给仓库 0。
# assignment[j] = i：客户 j 由仓库 i 服务。编号从 0 开始。
assignment = [0] * n
print("方案 A 的客户分配：", assignment)
print("开放仓库：", opened_facilities(instance, assignment))

# %% 3. 检查三个约束：每客户分配一次、仅使用开放仓库、容量不超限。
# 当前编码由使用情况推导开放仓库，因此前两个约束由合法编码保证。
loads = check_feasibility(instance, assignment)
print("仓库 0 的负载：", loads[0])
print("仓库 0 的容量：", instance.capacities[0])
print("其他仓库的负载：", loads[1:])
assert loads[0] == sum(instance.demands) == instance.capacities[0]

# %% 4. 展开两个求和公式，再与公共评价函数核对。
f1 = 0.0
for facility in opened_facilities(instance, assignment):
    f1 += instance.fixed_costs[facility]

f2 = 0.0
for customer, facility in enumerate(assignment):
    cost = instance.allocation_costs[facility][customer]
    f2 += cost  # C[i][j] 已包含客户全部需求，不再乘 demands[j]。
    if customer < 3:
        print(f"客户 {customer} -> 仓库 {facility}：分配费用 {cost}")

evaluated_f1, evaluated_f2 = evaluate(instance, assignment)
# 浮点小数的逐项累加与 sum 可能有极小舍入差，用 isclose 核对。
assert isclose(f1, evaluated_f1) and isclose(f2, evaluated_f2)
print(f"方案 A：f1={f1:.2f}, f2={f2:.2f}")

# %% 5. 方案 B：找开设费用最低的仓库，让它服务全部客户。
cheapest_facility = min(range(m), key=lambda i: instance.fixed_costs[i])
assignment_b = [cheapest_facility] * n
objectives_b = evaluate(instance, assignment_b)
print("最便宜仓库编号：", cheapest_facility)
print("该仓库开设费用：", instance.fixed_costs[cheapest_facility])
print(f"方案 B：f1={objectives_b[0]:.2f}, f2={objectives_b[1]:.2f}")
print("零开仓费来自官方数据，不是漏算，也不要自行替换。")

# %% 6. 方案 C：每个客户独立选择分配费用最低的仓库。
assignment_c = []
for customer in range(n):
    best_facility = min(
        range(m),
        key=lambda i: instance.allocation_costs[i][customer],
    )
    assignment_c.append(best_facility)

objectives_c = evaluate(instance, assignment_c)
print("方案 C 开放仓库数量：", len(opened_facilities(instance, assignment_c)))
print(f"方案 C：f1={objectives_c[0]:.2f}, f2={objectives_c[1]:.2f}")
print("cap101 每个仓库都能容纳总需求，因此这种独立分配不会超载。")
print("在其他容量较小的实例上，不能直接假设这种方法可行。")

# %% 7. 比较三个真实方案。这里还没有运行 MOEA，也没有求出完整 Pareto 前沿。
print("\n方案       开仓费用 f1       分配费用 f2")
for label, candidate in (("A", assignment), ("B", assignment_b), ("C", assignment_c)):
    opening, allocation = evaluate(instance, candidate)
    print(f"{label:4} {opening:16.2f} {allocation:16.2f}")

assert isclose(f1, 7500) and isclose(f2, 1935118)
assert isclose(objectives_b[0], 0) and isclose(objectives_b[1], 1248142.9)
assert isclose(objectives_c[0], 180000) and isclose(objectives_c[1], 652291.15)
print("B 的两个费用都低于 A：B 支配 A。")
print("B 开仓费用更低，C 分配费用更低：B 与 C 互不支配。")
print("这只是在三个方案中比较；不能据此把它们称为完整真实 Pareto 前沿。")
print("下一步：用固定随机种子生成一个种群，评价并进行非支配排序。")
