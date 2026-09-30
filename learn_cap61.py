# %% 1. 读取更新后的小规模实例。所有需求、容量、费用保持原始数值。
from cflp.data import load_instance, verify_data
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility, necessary_feasibility_issues

verify_data()
instance = load_instance("cap61")  # 也可以改成 cap62。
print("实例：", instance.name)
print("仓库数：", instance.n_facilities, "客户数：", instance.n_customers)
print("总容量：", sum(instance.capacities), "总需求：", sum(instance.demands))
print("最大仓库容量：", max(instance.capacities), "最大客户需求：", max(instance.demands))

# %% 2. 必要条件通过不等于任意分配都可行，还需构造并检查完整分配。
issues = necessary_feasibility_issues(instance)
if issues:
    raise ValueError("; ".join(issues))
print("必要条件通过。下面尝试构造一个完整分配。")

# %% 3. 教学构造：先分配大客户，选择放入后剩余容量最少的可容纳仓库。
# 这是确定性贪心示范，不是完整 MOEA，也不是通用修复。
remaining = list(instance.capacities)
assignment = [-1] * instance.n_customers
customer_order = sorted(range(instance.n_customers), key=lambda j: (-instance.demands[j], j))

for customer in customer_order:
    demand = instance.demands[customer]
    candidates = [i for i in range(instance.n_facilities) if remaining[i] >= demand]
    if not candidates:
        raise RuntimeError("本次贪心构造失败；不能由此断言实例无解。")
    facility = min(candidates, key=lambda i: (remaining[i] - demand, i))
    assignment[customer] = facility
    remaining[facility] -= demand

# %% 4. 重新检查所有客户与所有容量，再计算两个目标。
loads = check_feasibility(instance, assignment)
print("50 个客户的完整分配：", assignment)
for facility in sorted(set(assignment)):
    print(f"仓库 {facility}：负载 {loads[facility]:g} / 容量 {instance.capacities[facility]:g}")
print("目标 (开仓费, 分配费)：", evaluate(instance, assignment))
print("这是可行性见证，不代表费用最优。")

# %% 5. 两个客户分别能装下，合在一起却不一定装得下。
largest, second_largest = customer_order[:2]
combined_demand = instance.demands[largest] + instance.demands[second_largest]
print(f"客户 {largest} 和 {second_largest} 的合计需求：{combined_demand:g}")
bad_assignment = assignment.copy()
bad_assignment[second_largest] = bad_assignment[largest]
try:
    evaluate(instance, bad_assignment)
except ValueError as error:
    print("预期的容量错误：", error)
else:
    raise AssertionError("此教学候选应当被容量检查拒绝。")

# %% 6. 下一步仍需要共享的可行性处理，不能因为更换实例就跳过修复。
print("初始化、交叉、变异后的候选均需检查；不可行时按共同规则修复或重新生成。")
print("通用初始化与修复模块仍待实现；不得拆分需求、删除客户或更改数据。")
