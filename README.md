# ACIT4610 Assignment 2: Multi-objective CFLP with MOEAs

NSGA-II and SPEA2 search for facility locations and customer assignments that
minimise **facility opening cost** and **customer allocation cost**, subject to
capacity constraints. Group number: **Group-8**. Group members: **Zhongye Xue,
Syed Mohammad Abdur-Rahman Tirmizey, Jakob Andreas Amtedal, Khoa Anh Huynh**.

The sections below describe the intended algorithm design. Encoding, evaluation,
variation, capacity repair, and NSGA-II selection are implemented. General
initialization, the complete NSGA-II loop, SPEA2, and hypervolume are unfinished;
**formal experiment results are pending**.

## 1. How the next generation is created

Example configuration: `cap61`, population **50**, crossover probability **0.9**
per parent pair, mutation probability **0.02** per gene, seed **0**, and a budget
of **10,000 objective evaluations**, including initialization.

Both algorithms share this preparation and offspring pipeline:

```text
Read cap61: 16 facilities, 50 customers
    -> generate 50 chromosomes (50 facility IDs each)
    -> decode assignments and repair capacity violations
    -> evaluate opening cost f1 and allocation cost f2 separately

Select parents -> single-point crossover -> per-gene mutation
    -> decode and repair each child -> evaluate feasible children
```

### NSGA-II

```text
Start with the current population
    -> calculate non-dominated ranks and crowding distances
    -> select parents by binary tournaments
    -> generate offspring using the shared pipeline
    -> combine parents and offspring
    -> recalculate ranks and crowding distances
    -> keep complete fronts in rank order
    -> fill remaining places from the next front by largest crowding distance
    -> repeat within the evaluation budget
    -> return non-dominated solutions from the final population
```

Parents can be selected more than once. Parent and offspring populations compete
for survival, so **elitism is part of replacement**. Crowding distance promotes
spread within a front; it is not an additional problem objective.

### SPEA2

```text
Start with the current population and an initially empty archive
    -> combine population and archive
    -> calculate strength, raw fitness, and nearest-neighbour density
    -> update the archive with non-dominated individuals
    -> fill vacancies by fitness, or truncate an oversized archive by distance
    -> select parents from the archive by binary tournaments
    -> generate the next population using the shared pipeline
    -> repeat within the evaluation budget
    -> update the archive with the last evaluated population
    -> return non-dominated solutions from the final archive
```

The external archive preserves elites. Its proposed capacity equals population
size. Archive filling can include dominated individuals, so the final output
must still be filtered for non-dominance.

## 2. Algorithm design

| Block | Design |
| --- | --- |
| Encoding | `a[j]` is the facility serving customer `j`, using zero-based IDs. Each chromosome has one gene per customer; cap61 has 50 genes with values 0–15. Used facilities are open; unused facilities are closed. |
| Initialization | Planned: randomly select a nonempty subset of facilities, assign each customer to a random facility in that subset, then repair. Use a seeded random-number generator. |
| NSGA-II selection | Binary tournaments prefer lower non-dominated rank, then larger crowding distance. Remaining ties are random. |
| SPEA2 selection | Planned: binary tournaments on archive members prefer lower strength-based fitness plus density; remaining ties are random. |
| Crossover | With probability `pc` per pair, exchange chromosome tails after a random cut. Otherwise copy the parents. Skip crossover for one-gene chromosomes. |
| Mutation | Independently, with probability `pm` per gene, assign that customer to a different randomly selected facility. Skip mutation when only one facility exists. |
| Repair | Relocate customers from overloaded facilities, prioritising a single move that resolves the overload. Details below. |
| Evaluation | Calculate opening and allocation costs separately, only after checking feasibility. |
| Replacement | NSGA-II selects survivors from parents and offspring; SPEA2 replaces the population with offspring while retaining its archive. |
| Termination | Planned: stop at 10,000 objective evaluations, including initial individuals. Do not use a fixed generation count across different population sizes. |

Crossover and mutation preserve valid facility IDs and one assignment per
customer, but can violate capacities. Repair returns a separate chromosome and
does not alter benchmark data. Initialization's subset-size rule and bounded
reconstruction policy remain to be specified and implemented.

### Objectives and feasibility

For facility `i` and customer `j`, `F[i]` is the opening cost, `C[i][j]` is the
allocation cost, `S[i]` is capacity, and `d[j]` is demand. Let `y[i]` indicate an
open facility and `x[i][j]` indicate an assignment.

```text
Minimise f1 = sum_i F[i] * y[i]
Minimise f2 = sum_i sum_j C[i][j] * x[i][j]

Every customer is assigned exactly once:  sum_i x[i][j] = 1
Assignments use open facilities only:    x[i][j] <= y[i]
Facility capacities are respected:       sum_j d[j] * x[i][j] <= S[i] * y[i]
```

`C[i][j]` already covers the customer's entire demand; do not multiply it by
`d[j]` again. Lower values are preferred for both objectives, which are not
combined into a weighted sum. One solution dominates another if it is no worse
in either objective and strictly better in at least one.

NSGA-II uses non-dominated rank and crowding distance. In the planned SPEA2 design,
strength counts dominated individuals, raw fitness sums dominators' strengths,
and density penalises crowded regions. The density neighbour index and distance
scaling remain to be fixed before experiments.

### Decoding and capacity repair

Decoding groups customers by their facility genes, identifies open facilities,
and sums assigned demands. Repair then applies:

```text
Choose the facility with the largest overload E
    -> find customers with at least one feasible destination
    -> if any has demand >= E, choose the smallest such demand
    -> otherwise choose the largest movable demand
    -> move to the destination with least remaining capacity after assignment
    -> update loads and repeat until no facility is overloaded
```

Unused facilities are eligible destinations. All ties use the lowest relevant
ID. The rule aims to limit gene changes, without guaranteeing a global minimum.
Destinations remain feasible, so each moved customer is relocated at most once.
Invalid encodings or a lack of feasible moves raise `ValueError`; caller-side
reconstruction and retry handling are not yet implemented.

### Example: cap61

The initial chromosome is:

```text
[2, 3, 3, 2, 3, 3, 2, 2, 3, 3,
 0, 3, 1, 3, 3, 3, 3, 2, 3, 3,
 0, 3, 3, 3, 3, 3, 1, 3, 3, 3,
 3, 3, 3, 0, 3, 0, 1, 2, 3, 3,
 0, 2, 3, 3, 2, 3, 3, 3, 2, 3]
```

Facility 0 carries **20,492**, exceeding its **15,000** capacity by **5,492**.
Customer 10 has demand **5,495**, and facility 1 has exactly **5,495** spare
capacity. Repair changes only `a[10]` from **0 to 1**.

| Facility | Open after repair | Customers after repair | Load before → after | Capacity |
| --- | ---: | --- | ---: | ---: |
| 0 | 1 | 20, 33, 35, 40 | 20,492 → 14,997 | 15,000 |
| 1 | 1 | 10, 12, 26, 36 | 9,505 → 15,000 | 15,000 |
| 2 | 1 | 0, 3, 6, 7, 17, 37, 41, 44, 48 | 14,993 → 14,993 | 15,000 |
| 3 | 1 | 1, 2, 4, 5, 8, 9, 11, 13, 14, 15, 16, 18, 19, 21, 22, 23, 24, 25, 27, 28, 29, 30, 31, 32, 34, 38, 39, 42, 43, 45, 46, 47, 49 | 13,278 → 13,278 | 15,000 |
| 4–15 | All 0 | None | All 0 | 15,000 each |

Every customer appears exactly once, and no facility exceeds capacity. Using the
original costs, **f1 = 4 × 7,500 = 30,000** and **f2 = 1,864,204.2125**.
This is a worked feasibility example, not a benchmark result or an optimality claim.

## 3. Instances and experiment parameters

| Category | Instances | Facilities × customers | Detailed comparison |
| --- | --- | --- | --- |
| Small | cap61, cap62 | 16 × 50 | cap61 |
| Medium | cap101, cap102 | 25 × 50 | cap101 |
| Large | cap121, cap122 | 50 × 50 | cap121 |

The original [OR-Library](https://people.brunel.ac.uk/~mastjjb/jeb/orlib/capinfo.html)
files are bundled in `data/or_library`; see [data details](data/README.md).
Costs, capacities, and demands remain unchanged. All six instances are included
in experiments; the three focus instances are selected for detailed discussion.

| Configuration | Parameter set | Population | Evaluation budget | Crossover per pair | Mutation per gene |
| --- | --- | ---: | ---: | ---: | ---: |
| A | smaller_population | 50 | 10,000 | 0.9 | 0.02 |
| B | reference | 100 | 10,000 | 0.9 | 0.02 |
| C | larger_population | 200 | 10,000 | 0.9 | 0.02 |

[configs/experiments.json](configs/experiments.json) contains the proposed settings.
Both algorithms use seeds **0–9**, giving **2 algorithms × 6 instances × 3
configurations × 10 independent runs = 360 runs**. SPEA2 archive capacities are
provisionally **50, 100, and 200**, respectively.

Each evaluation produces both objective values and counts once against the
budget, including initialization; objective caching is disabled in the proposed
configuration. The full loops must handle the remaining budget without
overshooting. Population size varies while crossover, mutation, and evaluation
budget remain fixed. For SPEA2, archive size changes with population size, so
those two effects cannot be separated by this design.

Hardware/software, timing boundaries, initialization details, and handling of
failed offspring: **[Pending]**. The configuration still contains initialization
and repair integration placeholders; it is not an executable experiment runner.

## 4. Results and evaluation

**No formal runs have been completed.** Dashes below mean pending results, not
zero values. Complete this table for each of the six instances: **36 rows in
total**, with each row summarising 10 independent runs.

Instance: **[Pending]**

| Config | MOEA | HV mean | HV SD | HV best | HV worst | ND mean | Time mean (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | NSGA-II | — | — | — | — | — | — |
| A | SPEA2 | — | — | — | — | — | — |
| B | NSGA-II | — | — | — | — | — | — |
| B | SPEA2 | — | — | — | — | — | — |
| C | NSGA-II | — | — | — | — | — | — |
| C | SPEA2 | — | — | — | — | — | — |

- **Quality:** compare hypervolume (HV); higher is better. Report mean, sample
  standard deviation, best, and worst across independent runs.
- **Comparability:** use common normalization bounds and one fixed HV reference
  point per instance across both algorithms and all configurations. Numerical
  bounds, reference points, and HV implementation: **[Pending]**.
- **Diversity:** report the number of distinct non-dominated objective vectors
  (ND). Duplicate objective vectors count once; a larger ND alone does not prove
  better solution quality.
- **Efficiency:** compare mean runtime alongside solution quality. Hardware and
  timing scope: **[Pending]**.
- **Statistical comparison:** test, pairing rationale, significance level,
  multiple-comparison handling, and effect sizes: **[Pending]**.

| Output | Purpose | Result |
| --- | --- | --- |
| Summary and runtime tables | Compare all 36 algorithm/instance/configuration combinations | [Pending] |
| Per-run records | Retain seeds, parameters, objectives, HV, ND, and runtime | [Pending] |
| Small-instance Pareto plot | Compare NSGA-II and SPEA2 on cap61 | [Pending] |
| Medium-instance Pareto plot | Compare NSGA-II and SPEA2 on cap101 | [Pending] |
| Large-instance Pareto plot | Compare NSGA-II and SPEA2 on cap121 | [Pending] |

Pareto plots will use `f1` on the horizontal axis and `f2` on the vertical axis.
The configuration and run-selection or pooling rule must accompany each plot.

**Discussion and conclusions:** [Pending experimental evidence on solution
quality, diversity, runtime, and the effects of configuration and instance size.]

## 5. Reproduce the project

Use Python 3.10 or newer. Current code uses only the standard library. From the
repository root:

```bash
python3 -m unittest discover -s tests -v
python3 learn_workflow.py
python3 -m cflp --plan
```

These commands run existing tests, a learning walkthrough, and a configuration
preview. **The full 360-run reproduction command is pending.**

The main components are `representation.py` (encoding), `evaluation.py`
(objectives), `operators.py` (variation), `repair.py` (capacity repair), and
`nsga2.py` / `spea2.py` (algorithm logic), under `cflp/`. Further learning notes
are in [docs/learning.md](docs/learning.md).
