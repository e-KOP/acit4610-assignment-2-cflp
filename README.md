# ACIT4610 Assignment 2: Multi-objective CFLP

这是用于逐步学习与搭建算法的项目框架，沿用上次 `JSSP` 的组织方式：
`data/`、问题包、`configs/`、`tests/`、`docs/` 和 `results/`。

**当前可以直接读取六个真实实例、检查数据完整性、学习方案编码与费用计算。**
NSGA-II、SPEA2、初始化、修复和 HV 是明确标记的待实现部分；
当前没有运行优化算法，也没有实验结果。

## 快速开始

**合成学习入口：** `python3 learn_workflow.py`，在一个文件中按 12 个 `# %%` 段落
学习读数、小案例、cap101 的一次代际更新，以及 cap61 的容量限制。
复用 `cflp/` 算法模块，不需要依次运行其他学习文件；原有单节文件仍可单独使用。
本次进化评价计数为 16（初始 8 + 子代 8），不包含前后用于讲解的示例评价。
它是教学流程，不是完整多代优化器或正式实验。

**采用更新后的实例清单：** Small 为 cap61、cap62；Medium 为 cap101、cap102；
Large 为 cap121、cap122。六个实例均使用原始 OR-Library 数据。
cap61、cap62 的单仓容量为 15000，已有完整可行分配通过验证；但某个候选方案仍可能超载。
每次初始化、交叉或变异后都必须检查容量，并按作业要求处理不可行候选。
不拆分客户需求、不排除客户、不改写原始数据。通用初始化与修复模块仍待实现。
运行 `python3 learn_cap61.py` 可逐段学习可行构造与不可行候选的区别。

Python 3.10 或更新版本；当前只用标准库，不必先安装其他依赖。
在终端执行以下命令（这些是终端命令，不是 Python 代码）：

```bash
cd /home/xue/ACIT4610/CFLP
python3 -m cflp --all
python3 -m cflp --verify-data
python3 -m cflp --instance cap61
python3 learn_data.py
python3 learn_cap61.py
python3 learn_cap101.py
python3 learn_population.py
python3 learn_selection.py
python3 learn_offspring.py
python3 learn_environment.py
python3 learn_solution.py
python3 -m unittest discover -s tests -v
python3 -m cflp --plan
```

项目迁移到其他电脑时，先进入实际保存的 CFLP 根目录，其余命令不变。
也可以直接运行 `/home/xue/ACIT4610/CFLP/learn_data.py` 的绝对路径。
学习文件 `learn_*.py` 使用 `# %%` 分段，支持有 Python cell 功能的编辑器；也可逐段粘贴到
从项目根目录启动的 `python3` 交互环境中。不要把 `from ...` 等 Python 语句粘到 Bash 提示符。

可选的隔离环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 目录和当前状态

```text
CFLP/
├── data/
│   ├── or_library/            六个未经改写的官方实例
│   ├── checksums.json         下载地址、时间、大小、SHA-256
│   └── README.md              文件格式及字段对应关系
├── cflp/
│   ├── data.py                已完成：读取与数据校验
│   ├── representation.py      已完成：客户分配编码与开放仓库
│   ├── feasibility.py         已完成：负载与容量检查
│   ├── evaluation.py          已完成：可行方案的双目标计算
│   ├── initialization.py      待实现：共享初始化
│   ├── repair.py              待实现：共享可行性处理
│   ├── operators.py           已完成：单点交叉与逐客户变异
│   ├── pareto.py              已完成：支配关系与非支配分层
│   ├── nsga2.py               已完成拥挤距离、父代与环境选择；多代循环待实现
│   ├── spea2.py               待实现：SPEA2
│   ├── metrics.py             待实现：二维 HV
│   ├── statistics.py          统计分析模块的职责说明
│   ├── plotting.py            绘图模块的职责说明
│   ├── experiments.py         已完成配置预览；实验执行待实现
│   └── __main__.py            已完成：数据检查与配置预览入口
├── configs/experiments.json   三组参数草案与十个随机种子
├── learn_data.py              从真实 cap61 开始，逐段学习读数
├── learn_cap61.py             真实 cap61 的容量检查、可行构造与超载演示
├── learn_cap101.py            真实 cap101 的分配、约束、费用与方案比较
├── learn_population.py        cap101 的八个随机个体与非支配排序
├── learn_selection.py         拥挤距离与二元锦标赛选择
├── learn_offspring.py         父代配对、交叉、变异与子代评价
├── learn_environment.py       合并原种群和子代，选出下一代
├── learn_solution.py          从教学例子学习编码、约束与目标
├── docs/learning.md           学习顺序、练习和完成标准
├── tests/                    数据与模型的正确性检查
├── results/                  将来保存实验结果
└── requirements.txt           当前无第三方依赖
```

## 数据已经就位

| 类别 | 实例 | 仓库数 m | 客户数 n |
|---|---|---:|---:|
| Small | cap61, cap62 | 16 | 50 |
| Medium | cap101, cap102 | 25 | 50 |
| Large | cap121, cap122 | 50 | 50 |

来源：[J. E. Beasley OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/capinfo.html)。
原始字节保存在 `data/or_library/`，没有改写费用、容量或客户需求。
具体下载 URL 和校验值见 `data/checksums.json`。

```python
from cflp.data import load_instance

instance = load_instance("cap61")
print(instance.n_facilities, instance.n_customers)  # 16 50
print(instance.capacities[0])                     # 15000.0
print(instance.fixed_costs[0])                    # 7500.0
print(instance.demands[0])                        # 146.0
print(instance.allocation_costs[0][0])            # 6739.725
```

`allocation_costs[i][j]` 是仓库 i 服务客户 j **全部需求**的费用，不能再乘 `demands[j]`。
文件中费用按客户组织，读取器转换为按仓库索引的矩阵；这只改变内存布局，不改变数值。
原数据使用不可变 tuple 保存，候选方案单独保存。

## 方案表示与目标

采用客户分配列表：`assignment[j] = i`。所有编号从 0 开始。
每个客户恰好有一个仓库；被使用的仓库开放，其余关闭。
在开仓费用非负时，开放完全不用的仓库不会改善目标；零费用空仓可能对应同样目标值，
当前编码不单独表示它们。

`evaluate(instance, assignment)` 先检查编码与容量，再返回 `(f1, f2)`：

- `f1 = sum(F[i] for i in opened_facilities)`：每个开放仓库只计一次。
- `f2 = sum(C[assignment[j]][j] for j in customers)`：不再乘需求。
- 仓库负载为 `sum(d[j] for j assigned to i)`，不得超过 `S[i]`。

违反约束时抛出 `ValueError`，不会把不可行方案当作有效解评价。
`learn_solution.py` 中的小例子只是教学材料；正式实验只能使用六个官方实例。

## 接下来怎样搭建算法

按 [学习指南](docs/learning.md) 进行：

1. 读懂 cap61 的一个仓库和一个客户。
2. 手算教学例子，再核对容量和双目标。
3. 自己枚举小例子的 27 种分配，提取准确的非支配前沿。
4. 实现共享初始化、交叉、变异和必要的修复。
5. 实现 NSGA-II，再实现 SPEA2；两者共用问题相关模块。
6. 实现并验证 HV，再接入实验、统计和绘图。

待实现函数使用 `NotImplementedError` 明确提示状态，避免把空实现当作算法结果。
这里暂按 NSGA-II / SPEA2 预留入口，最终选择应与课堂讨论过的算法一致。

## 实验配置草案

`configs/experiments.json` 预留六个实例、两种算法、三组配置和种子 0–9。
种群大小为 50、100、200；共享每对父代交叉概率 0.9、每个客户基因变异概率 0.02，
目标评价预算均为 10000（包含初始化）。这是可修改的学习草案，尚未试运行或调参。
SPEA2 档案大小暂约定等于种群大小；所有目标评价调用都需要计入预算。

全部组合为 `2 × 6 × 3 × 10 = 360` 次运行。`--plan` 仅预览，不执行。
`analysis_instances` 暂选 cap61、cap101、cap121，供三个规模的深入比较。
开始正式实验前必须确定共享初始化/修复方法、停止与失败规则、每实例统一的归一化边界和
HV 参考点（配置中的 `null` 表示尚未设置，不可直接用于计算）。

本项目提供代码学习框架与技术说明，不包含提交用报告。运行结果、统计结论和报告留待完成算法后整理。
