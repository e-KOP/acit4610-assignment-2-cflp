# Learn while building

Data loading and the basic model are implemented. Each step below has a small,
verifiable result. Start with working examples instead of trying to run the
unfinished algorithms together.

## Combined walkthrough

Run `python3 learn_workflow.py`, or execute its `# %%` cells in order:

```text
Real data -> small example -> three cap101 solutions -> initial population
-> ranks and crowding -> tournament selection -> crossover and mutation
-> offspring evaluation -> merge and rerank -> next generation
-> feasible cap61 construction -> overloaded candidate
```

Each cell uses variables from earlier cells. If you change an earlier parameter,
rerun from the relevant initialization cell onward. Cell 10 completes one
generation update. Its 16 evaluations count only that evolution demonstration;
separate teaching examples before and after it also call the evaluator.
Do not apply the cap101 initialization directly to cap61. General capacity-aware
initialization and repair remain to be implemented.

## Reading data

From the project root, run `python3 learn_data.py`. In a cell-aware editor, begin
with the first `# %%` cell. Alternatively, start `python3` from the project root
and enter the following at the `>>>` prompt:

```python
from cflp.data import load_instance
instance = load_instance("cap61")
instance.n_facilities
instance.n_customers
instance.demands[0]
instance.allocation_costs[0][0]
```

Expected values: 16, 50, 146.0, and 6739.725. Find them in the original
`data/or_library/cap61.txt`, then read `cflp/data.py`.
Consider why the reader uses `split()` instead of treating each line as a complete
customer record.

## Encoding, constraints, and evaluation

Run `python3 learn_solution.py`. The `[1, 1, 2]` example has loads `(0, 7, 5)` and
objectives `(130, 24)`. Read `representation.py`, `feasibility.py`, and
`evaluation.py` in that order.

Explain what a list position means, what its value means, and why an opening cost
is counted only once. Check assignments `[0, 0, 0]` and `[0, 1, 2]`, which produce
`(100, 72)` and `(230, 40)`. Assigning every customer to facility B (ID 1) should
raise an overload error rather than return valid objectives.

## Small enumeration and Pareto comparisons

For the three-facility, three-customer teaching example only, use
`itertools.product(range(3), repeat=3)` to enumerate 27 assignments. Keep feasible
assignments before computing their objectives. The example has 15 feasible and
12 infeasible assignments. Study the dominance and sorting functions in
`cflp/pareto.py` to extract the non-dominated set. Do not enumerate `16**50`
assignments for a real small benchmark.

Check these relationships by hand:

- `(130, 24)` dominates `(160, 44)`.
- `(100, 72)` and `(130, 24)` are mutually non-dominated.
- Equal objective vectors do not strictly dominate each other.

Verify that no output point dominates another and document whether metrics
count distinct objective vectors or distinct assignments.

## Real cap101 solutions

Run `python3 learn_cap101.py`: load the real data, assign all customers to
facility 0, check the three constraints, expand both objective sums, and compare
solutions favoring opening cost or allocation cost.

Each cap101 facility can hold total demand, and facility 10 has an original
opening cost of zero. This makes it useful for learning two objectives and
population selection without capacity-repair difficulties. This file does not
run a MOEA, and comparing three solutions does not establish the complete Pareto
front.

## Initial population and non-dominated sorting

Run `python3 learn_population.py`. Seed 42 generates eight complete assignments,
each with 50 customers. Each individual first selects a random facility subset,
then randomly assigns customers within it. Only used facilities contribute to
opening cost.

This teaching initialization relies on cap101's large capacities; general
capacity-constrained initialization is still unfinished. The expected fronts are:

| Front | Individual IDs |
|---|---|
| 1 | 5, 6 |
| 2 | 3, 4, 7 |
| 3 | 0 |
| 4 | 1, 2 |

The shared dominance and non-dominated sorting functions in `cflp/pareto.py` are
implemented. This lesson does not yet perform variation or environmental
selection. Non-dominated within this population does not mean globally optimal.

## Crowding distance and parent selection

Run `python3 learn_selection.py` to reproduce the same population and compute
crowding distance separately within each front. In front `[3, 4, 7]`, individual
3 has distance 2; boundary individuals 4 and 7 have infinite distance.

`inf` protects the front's extremes. It is not infinite cost and does not take
priority over a better rank. For each objective, crowding adds the gap between
neighboring points divided by that objective's range within the front.

Implementation conventions:

- Fronts containing one or two points receive infinite distances.
- Constant objectives are skipped.
- A front of at least three identical vectors receives zero distances.
- Ties in objective values use a stable ordering by original index.

Each tournament samples two different individuals. Prefer lower rank, then
larger crowding distance, then break complete ties randomly. Different
tournaments may sample and select the same individual again. Selection returns
indices; the lesson copies the corresponding assignments. It neither changes the
original population nor reevaluates the selected parents.

Source for crowding distance and crowded comparison:
[Deb et al., NSGA-II (2002)](https://doi.org/10.1109/4235.996017).
Continue with variation and environmental selection in the following lessons.

## Pairing, crossover, and mutation

Run `python3 learn_offspring.py`. Reproduce the population and parent selection,
then pair parents by position, generating two children per pair.

Single-point crossover occurs with probability 0.9 per pair and exchanges
assignments after a random cut. Mutation acts independently on each customer with
probability 0.02 and, when triggered, selects a different facility uniformly. A
50-customer individual has an expected one mutation, but may actually have zero
or several. Both operations return independent lists and preserve the parents.

Initialization, selection, and variation use seeds 42, 7, and 21 to make individual
lessons reproducible. Define a consistent run-level seed policy for formal
experiments. The selected parents are `[5, 6, 6, 1, 3, 3, 6, 3]`; four pairs
produce eight offspring.

Valid assignments cannot overload a cap101 facility, so no repair is needed in
this example. Nevertheless, each child is checked before evaluation. The run uses
16 evaluations: 8 initial plus 8 offspring. There is no objective cache, and
duplicate individuals still count as separate evaluations.

Offspring are not guaranteed to differ from their parents or have better costs.
Single-point crossover preserves the encoding, not capacity feasibility in
general. Shared repair is still unfinished. This lesson leaves the original
population intact; environmental selection is next.

## Environmental selection: one generation update

Run `python3 learn_environment.py`. P labels original individuals and C labels
offspring. Merge the **entire original population** with the offspring, not the
possibly repeated mating-parent list.

Recompute non-dominated ranks and crowding on the combined set. Keep complete
fronts while they fit. For the first front that does not fit, take individuals in
descending crowding-distance order, using the supplied random generator to break
ties. Later fronts are not considered.

This example retains P5, P6, C0, P4, P7, C1, P0, and C6. These exactly fill the
first three fronts, so this particular update does not truncate a front. The
next generation has eight individuals and reuses their objective values; the
evaluation count stays at 16.

Partial-front truncation is implemented and checked with hand-calculated tests.
To observe it separately, call
`environmental_selection(combined_objectives, 7, Random(11))`. Only one of the
third front's two boundary points then fits, and the tie is resolved randomly.
This is an additional demonstration, not a change to the experimental population
size. Continue subsequent generations from `next_population`; do not reset the
random generators each generation.

## Capacity constraints on cap61

The updated small instances are cap61 and cap62. Run `python3 learn_cap61.py`:
load data, check necessary conditions, allocate customers in descending demand
order, validate the complete assignment, evaluate objectives, and deliberately
put two large customers together to observe overload rejection.

Both small instances have capacity 15000 per facility and maximum customer demand
12912. Complete feasible assignments have been verified. However, customers 33
and 10 demand 12912 and 5495 respectively. Their combined demand is 18407, so they
cannot share one facility.

A feasible instance does not make every candidate feasible. This deterministic
greedy construction is not a random population initializer, repair method, or
complete MOEA. A failed greedy attempt does not prove the instance infeasible;
passing necessary conditions does not prove feasibility either.
Keep customer demands indivisible, include every customer, and preserve the
original OR-Library values.

## Shared initialization and repair

Implement `initialization.py` using the supplied `random.Random(seed)` rather
than modifying global random state throughout the code. One starting point is
to order customers by demand and choose facilities with sufficient remaining
capacity, with bounded retries or reassignment when an attempt fails.

Sufficient total capacity is necessary but not sufficient. Define failure
handling in `repair.py`; do not retry forever or reduce demands to make solutions
fit. Use necessary conditions to identify proven-infeasible instances, then
validate every constructed candidate with `check_feasibility`. Record and handle
failures explicitly. Finding a feasible solution is not evidence of good cost.

Use the same encoding, initialization, crossover, mutation, and problem-specific
feasibility handling in both MOEAs. The operators are in `operators.py` and must
not modify parents in place. Their probabilities apply per parent pair for
crossover and per customer gene for mutation. Check candidates after variation
and apply the common repair procedure when needed.

## Complete NSGA-II and SPEA2

- NSGA-II: non-dominated sorting, crowding distance, tournament selection,
  offspring, and elitist selection from the merged population.
- SPEA2: strength, raw fitness, density, archive selection and truncation,
  selection, and offspring.

Implement core evolutionary operations yourself. Numerical and data libraries
do not replace the required evolutionary logic. Begin with small examples and
increase problem size and budget gradually.

Completion criteria: every output solution is feasible, evaluation counts include
initialization and search, the same seed and settings reproduce objective
results, and small cases can be checked against enumeration. Equal generation
counts alone do not establish equal computational budgets.

## Metrics, experiments, and analysis

Implement `metrics.py`. Two-dimensional HV is the area of a union of rectangles;
overlap must not be counted twice. First verify that point `(2, 3)` with reference
`(5, 6)` gives HV 9, then check overlapping rectangles. All comparisons for an
instance need common normalization and a common reference point. Do not normalize
each run separately or treat OR-Library's single-objective optimum as the true
two-objective front.

Use `python3 -m cflp --plan` to inspect proposed experiments. The actual runner in
`experiments.py` still needs to execute and record each instance, algorithm,
configuration, and seed. A plan is not a completed experiment. Use consistent
timing boundaries and save raw per-run results for means and sample standard
deviations. Choose statistical tests and multiple-comparison handling according
to the actual independence or pairing design.

Run the existing checks with:

```bash
python3 -m unittest discover -s tests -v
```

As development continues, validate meaningful edge cases: zero objective range
in crowding, duplicate HV points, repair failure, archive overflow, and an
insufficient remaining evaluation budget for a full offspring batch.
