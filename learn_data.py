# %% 读取一个真实实例：可以运行整个文件，也可以在编辑器中逐个 cell 运行。
# 终端运行：python3 /home/xue/ACIT4610/CFLP/learn_data.py
from cflp.data import DATA_DIR, load_instance

instance = load_instance("cap61")
print("实例：", instance.name)

# %% 理解 m 和 n：候选仓库数、客户数。
m = instance.n_facilities
n = instance.n_customers
print("仓库数 m =", m)
print("客户数 n =", n)

# %% F[i] 和 S[i]：仓库开设费用与容量。编号从 0 开始。
fixed_costs = instance.fixed_costs
capacities = instance.capacities
print("仓库 0 的开设费用 F[0] =", fixed_costs[0])
print("仓库 0 的容量 S[0] =", capacities[0])

# %% d[j] 和 C[i][j]：客户需求与服务该客户全部需求的费用。
demands = instance.demands
costs = instance.allocation_costs
print("客户 0 的需求 d[0] =", demands[0])
print("仓库 0 服务客户 0 的费用 C[0][0] =", costs[0][0])
print("注意：计算分配费用时，不要再乘客户需求。")

# %% 同一客户由不同仓库服务时的费用。
customer = 0
for facility in range(3):
    print(f"仓库 {facility} -> 客户 {customer}: {costs[facility][customer]}")

# %% 对照原文件：前两个 token 是 m,n，接着是 m 对容量和开设费用。
# split() 按空白分词，不假设每个客户的数据恰好占一行。
tokens = (DATA_DIR / "cap61.txt").read_text(encoding="ascii").split()
customer_start = 2 + 2 * m
print("原文件前 6 个 token：", tokens[:6])
print("第一个客户的需求 token：", tokens[customer_start])
print("第一个客户的前 3 项费用：", tokens[customer_start + 1:customer_start + 4])
assert float(tokens[customer_start]) == demands[0]
assert float(tokens[customer_start + 1]) == costs[0][0]

# %% 初步规模检查。总容量足够只是必要条件，不保证不可拆分分配一定可行。
print("总需求：", sum(demands))
print("总容量：", sum(capacities))
print("读取学习完成。接下来打开 cflp/data.py，逐步理解 parse_instance。")
