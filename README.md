# ACIT4610 Assignment 2: Multi-objective CFLP

A project for learning and implementing multi-objective evolutionary algorithms
for the Capacitated Facility Location Problem (CFLP). Its structure follows the
previous JSSP project: data, a problem package, configurations, tests,
documentation, and results.

**The project currently supports all six required instances, data integrity
checks, feasible-solution evaluation, shared capacity repair, and a
one-generation NSGA-II walkthrough.** General population initialization, the
complete NSGA-II loop, SPEA2, and hypervolume remain learning tasks. No formal
benchmark experiment results have been generated.

## Quick start

Use Python 3.10 or newer. The current code uses only the standard library.
From the repository root, run:

```bash
python3 learn_workflow.py
```

This combined walkthrough contains 12 `# %%` cells covering data, a small teaching
example, one generation on cap101, and capacity constraints on cap61. It reuses
`cflp/` modules; you do not need to execute the separate lessons first.
Its evolution evaluation count is 16: 8 initial individuals and 8 offspring.
Separate teaching examples before and after that demonstration are not included
in this count. This is a learning walkthrough, not a full experimental run.

For the existing local checkout, first run `cd /home/xue/ACIT4610/CFLP`.
After cloning elsewhere, use your own repository directory instead. Additional
commands, all entered in a terminal:

```bash
python3 -m cflp --all
python3 -m cflp --verify-data
python3 -m cflp --instance cap61
python3 learn_data.py
python3 learn_solution.py
python3 learn_cap101.py
python3 learn_population.py
python3 learn_selection.py
python3 learn_offspring.py
python3 learn_environment.py
python3 learn_cap61.py
python3 -m unittest discover -s tests -v
python3 -m cflp --plan
```

The `learn_*.py` files support execution in cells using an editor that recognizes
`# %%`. Run cells in order because later cells depend on earlier variables.
Alternatively, start `python3` from the repository root and paste Python code
into its `>>>` prompt. Do not paste Python statements such as `from ...` directly
into a Bash shell.

An isolated environment is optional:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Structure and implementation status

```text
CFLP/
├── data/
│   ├── or_library/            Six unmodified official instances
│   ├── checksums.json         Source URLs, retrieval dates, sizes, SHA-256 hashes
│   └── README.md              Source format and field mapping
├── cflp/
│   ├── data.py                Implemented: loading and data validation
│   ├── representation.py      Implemented: assignment encoding and open facilities
│   ├── feasibility.py         Implemented: necessary conditions and capacity checks
│   ├── evaluation.py          Implemented: two objectives for feasible assignments
│   ├── initialization.py      To implement: shared population initialization
│   ├── repair.py              Implemented: deterministic shared capacity repair
│   ├── operators.py           Implemented: single-point crossover and per-gene mutation
│   ├── pareto.py              Implemented: dominance and non-dominated sorting
│   ├── nsga2.py               Selection implemented; multi-generation loop unfinished
│   ├── spea2.py               To implement: SPEA2
│   ├── metrics.py             To implement: two-dimensional hypervolume
│   ├── statistics.py          Statistical analysis responsibilities
│   ├── plotting.py            Plotting responsibilities
│   ├── experiments.py         Configuration preview implemented; execution unfinished
│   └── __main__.py            Data inspection and experiment-plan entry point
├── configs/experiments.json   Three proposed configurations and ten random seeds
├── learn_workflow.py          Combined walkthrough in 12 cells
├── learn_data.py              Read and inspect the real cap61 data
├── learn_solution.py          Encoding, constraints, objectives, and small enumeration
├── learn_cap101.py            Real assignments, costs, and solution comparisons
├── learn_population.py        Eight random cap101 individuals and non-dominated sorting
├── learn_selection.py         Crowding distance and binary tournament selection
├── learn_offspring.py         Pairing, crossover, mutation, and offspring evaluation
├── learn_environment.py       Merge the original population and offspring; select survivors
├── learn_cap61.py             Capacity checks, feasible construction, and overload example
├── nsgs2.py                   Data-reading practice using the selected instance
├── docs/learning.md           Learning sequence, exercises, and completion criteria
├── tests/                    Checks for data, model, and implemented algorithm operations
├── results/                  Destination for future experiment outputs
└── requirements.txt           No third-party dependencies currently required
```

## Required benchmark data

The updated assignment uses:

| Category | Instances | Facilities m | Customers n |
|---|---|---:|---:|
| Small | cap61, cap62 | 16 | 50 |
| Medium | cap101, cap102 | 25 | 50 |
| Large | cap121, cap122 | 50 | 50 |

Source: [J. E. Beasley's OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/capinfo.html).
Original file bytes are stored in `data/or_library/`; costs, capacities, and
demands have not been changed. See `data/checksums.json` for exact download URLs
and integrity hashes. Git attributes preserve the raw benchmark line endings.

```python
from cflp.data import load_instance

instance = load_instance("cap61")
print(instance.n_facilities, instance.n_customers)  # 16 50
print(instance.capacities[0])                      # 15000.0
print(instance.fixed_costs[0])                     # 7500.0
print(instance.demands[0])                         # 146.0
print(instance.allocation_costs[0][0])             # 6739.725
```

`allocation_costs[i][j]` is the cost of serving **all demand** of customer j from
facility i. Do not multiply it by `demands[j]` again. The source groups costs by
customer; the reader stores them by facility and customer. This changes the
in-memory layout, not the numeric values. Instance data uses immutable tuples;
candidate assignments are stored separately.

Both small instances have facility capacity 15000, and complete feasible
assignments have been verified. However, individual candidates can still exceed
capacity. Check candidates after initialization, crossover, and mutation, and
handle infeasibility as required by the assignment. Do not split customer
demand, omit customers, or alter the OR-Library data. Shared capacity repair is
implemented; general initialization remains unfinished. Run
`python3 learn_cap61.py` to explore feasible construction and an overloaded
candidate.

## Representation and objectives

The assignment list uses `assignment[j] = i`, with zero-based IDs. Each customer
has exactly one serving facility. Used facilities are open; unused facilities
are closed. With nonnegative opening costs, opening unused facilities cannot
improve the objectives. Unused facilities with zero opening cost could produce
equivalent objective values; this encoding does not represent them separately.

`evaluate(instance, assignment)` checks the encoding and capacities before
returning `(f1, f2)`:

- `f1 = sum(F[i] for i in opened_facilities)`: count each opening cost once.
- `f2 = sum(C[assignment[j]][j] for j in customers)`: no extra demand multiplier.
- Facility load is the sum of its assigned customers' demands and must not exceed
  that facility's capacity.

Invalid solutions raise `ValueError` rather than receiving feasible objective
values. The small example in `learn_solution.py` is for learning only; formal
experiments must use the six required official instances.

## Capacity repair

`repair_assignment(instance, assignment, rng=None)` restores capacity feasibility
while prioritising fewer gene changes. It uses the following deterministic rule:

1. Select the facility with the largest overload.
2. Consider only customers that another facility can accommodate completely.
3. Choose the smallest-demand customer whose removal eliminates the overload.
   If none qualifies, choose the largest-demand customer that can be moved.
4. Choose the destination with the least remaining capacity after receiving that
   customer. Unused facilities are eligible.
5. Update the assignment and loads, then repeat until feasible.

All ties use the lowest relevant facility or customer ID. The function returns
a separate list and leaves the original assignment and benchmark data intact.
The optional `rng` argument supports the shared operator interface but is not
consumed. Invalid encodings or a lack of feasible moves raise `ValueError`;
failure to find a move does not prove the instance is infeasible. Destinations
never become overloaded, so each customer moves at most once. The heuristic
does not guarantee globally minimum gene changes or objective values.

```python
from cflp.data import load_instance
from cflp.repair import repair_assignment
from cflp.evaluation import evaluate

instance = load_instance("cap61")
assignment = [0] * instance.n_customers
repaired = repair_assignment(instance, assignment)
print(evaluate(instance, repaired))
```

In the report example, facility 0 has load 20,492 and facility 1 has load 9,505.
Moving customer 10 (demand 5,495) from facility 0 to facility 1 repairs the
5,492 overload with one gene change, leaving loads of 14,997 and 15,000.

The repair function is available for initialization and variation. Integrating
it into the complete NSGA-II and SPEA2 loops remains part of those unfinished
algorithms; the existing learning walkthroughs have not been changed.

## Learning sequence

Use [the learning guide](docs/learning.md), either with the combined walkthrough
or with the separate lessons:

1. Read a facility and customer record from cap61.
2. Calculate the teaching example's loads and objectives by hand.
3. Enumerate its 27 assignments and identify the non-dominated solutions.
4. Study cap101 solution comparisons, population generation, and sorting.
5. Follow parent selection, variation, and one environmental selection step.
6. Study cap61 capacity constraints and shared repair; implement initialization.
7. Complete NSGA-II and SPEA2 using the same problem-specific components.
8. Implement and validate HV, then add experiments, statistics, and plots.

Unimplemented functions raise `NotImplementedError` so placeholders cannot be
mistaken for working optimizers. NSGA-II and SPEA2 are the planned algorithms;
the final choice must be consistent with the algorithms covered in class.

## Proposed experiment configurations

`configs/experiments.json` specifies six instances, two algorithms, three proposed
configurations, and seeds 0-9. Population sizes are 50, 100, and 200. All share a
crossover probability of 0.9 per parent pair, a mutation probability of 0.02 per
customer gene, and an objective evaluation budget of 10000 including
initialization. These are editable learning settings, not tuned or benchmarked
configurations. SPEA2 archive size is provisionally equal to population size.
Count every objective evaluation against the budget.

The complete plan contains `2 × 6 × 3 × 10 = 360` runs. `--plan` previews settings
only; it does not execute them. `analysis_instances` selects cap61, cap101, and
cap121 for detailed comparisons across the three sizes.

Before formal experiments, implement shared initialization, integrate shared
repair and its failure handling into both algorithms and the experiment
configuration, and define stopping rules, common normalization bounds per
instance, and a common HV reference point. The configuration's `null` reference
point is unset and cannot be used to compute HV.

This repository contains learning code and technical documentation, not the
submission report. Experimental results, statistical conclusions, and the report
remain to be completed after the algorithms are implemented.
