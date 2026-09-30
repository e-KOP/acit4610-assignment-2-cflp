"""Combined learning walkthrough: run # %% cells in order, complete one generation, then study capacity.

Terminal: python3 /home/xue/ACIT4610/CFLP/learn_workflow.py
Reuses cflp implementations without importing other lessons; no full multi-generation experiment.
"""

# %% 1. Imports and real data: identify the four input quantities in cap61.
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
print("\n[1] Read the real cap61 data")
print("Facilities and customers:", small_instance.n_facilities, small_instance.n_customers)
print("Facility 0: capacity S[0] =", small_instance.capacities[0],
      "opening cost F[0] =", small_instance.fixed_costs[0])
print("Customer 0: demand d[0] =", small_instance.demands[0],
      "allocation cost C[0][0] =", small_instance.allocation_costs[0][0])
print("C[i][j] already includes the entire customer demand; do not multiply by d[j] again.")

# %% 2. Review encoding, capacity, and objectives using teaching data, not experimental benchmarks.
toy = Instance(
    "teaching_example", (12, 7, 5), (100, 60, 70), (4, 3, 5),
    ((24, 18, 30), (8, 6, 40), (30, 24, 10)),
)
toy_assignment = [1, 1, 2]  # Positions are customers; values are facilities: B, B, C.
print("\n[2] Review the small teaching example")
print("Assignment:", toy_assignment, "Loads:", check_feasibility(toy, toy_assignment))
print("Objectives:", evaluate(toy, toy_assignment))
assert evaluate(toy, toy_assignment) == (130, 24)

# %% 3. Switch to cap101: compare three intuitive solutions before population search.
# Every cap101 facility holds total demand, simplifying the introduction to evolution.
# Random assignments below depend on this property; do not simply change the instance to cap61.
instance = load_instance("cap101")
m, n = instance.n_facilities, instance.n_customers
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires every facility to hold total demand.")
single_facility = [0] * n
cheapest = min(range(m), key=lambda i: instance.fixed_costs[i])
low_opening = [cheapest] * n
low_allocation = [
    min(range(m), key=lambda i: instance.allocation_costs[i][j])
    for j in range(n)
]
print("\n[3] Three cap101 solutions (not the complete Pareto front)")
example_objectives = {}
for label, assignment in (("A", single_facility), ("B", low_opening), ("C", low_allocation)):
    example_objectives[label] = evaluate(instance, assignment)
    print(label, "Open facilities:", len(opened_facilities(instance, assignment)),
          "(f1, f2):", example_objectives[label])
print("Does B dominate A?", dominates(example_objectives["B"], example_objectives["A"]))
print("B and C offer different trade-offs; the zero opening cost is from the official data.")

# %% 4. Initialize 8 individuals, each containing a complete assignment of 50 customers.
# Use the same seeds as the separate lessons so results can be compared directly.
population_size = 8
initialization_rng = Random(42)
population = []
for individual in range(population_size):
    pool_size = initialization_rng.randint(1, m)
    facility_pool = initialization_rng.sample(range(m), pool_size)
    assignment = [initialization_rng.choice(facility_pool) for _ in range(n)]
    population.append(assignment)

objectives = [evaluate(instance, assignment) for assignment in population]
# Count only evaluations in this evolution demonstration, excluding earlier teaching examples.
evolution_evaluations = len(objectives)
print("\n[4] Initial population (zero-based IDs)")
print("Individual  Open facilities       f1             f2")
for i, (f1, f2) in enumerate(objectives):
    count = len(opened_facilities(instance, population[i]))
    print(f"{i:4} {count:10} {f1:12.2f} {f2:14.2f}")
print("Complete assignment for individual 0:", population[0])

# %% 5. Non-dominated sorting and crowding: compare rank first, then spacing within a front.
fronts, ranks, distances = rank_and_crowding(objectives)
print("\n[5] Fronts and crowding distances")
for rank, front in enumerate(fronts, start=1):
    print(f"Front {rank}:", front)
for i in range(population_size):
    print(f"Individual {i}: rank={ranks[i]}, crowding={distances[i]:.4f}")
print("inf protects boundary points; crowding does not take priority over a better rank.")
# These teaching objective vectors support hand calculations; they do not replace benchmark data.
teaching_points = [(1, 10), (2, 7), (5, 4), (9, 1)]
print("Hand-calculated crowding example:", crowding_distance(teaching_points, [0, 1, 2, 3]))

# %% 6. Binary tournament: draw two individuals, select one parent, and repeat 8 times.
selection_rng = Random(7)
parent_indices = []
print("\n[6] Parent selection")
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    parent_indices.append(winner)
    print(f"Sampled {a}, {b} -> selected {winner}")
parents = [population[i].copy() for i in parent_indices]
print("Parent indices:", parent_indices)
print("An individual can be selected as a parent more than once; no offspring exist yet.")

# %% 7. Pair parents, cross over, and mutate to create 8 offspring; check each one's capacity.
crossover_probability = 0.9  # Probability per parent pair.
mutation_probability = 0.02  # Probability per customer gene.
variation_rng = Random(21)
offspring = []
population_before_variation = [assignment.copy() for assignment in population]
print("\n[7] Generate offspring")
for start in range(0, population_size, 2):
    print("Parent pair:", parent_indices[start:start + 2])
    children = crossover(parents[start], parents[start + 1], crossover_probability, variation_rng)
    for crossed in children:
        child = mutate(crossed, m, mutation_probability, variation_rng)
        changes = [(j, crossed[j], child[j]) for j in range(n) if crossed[j] != child[j]]
        print("Mutations (customer, previous facility, replacement facility):", changes)
        check_feasibility(instance, child)
        offspring.append(child)
assert population == population_before_variation
assert parents == [population[i] for i in parent_indices]

# %% 8. Evaluate feasible offspring; duplicate individuals still count as separate evaluations.
offspring_objectives = [evaluate(instance, child) for child in offspring]
evolution_evaluations += len(offspring_objectives)
print("\n[8] Offspring objectives")
for i, values in enumerate(offspring_objectives):
    print(f"C{i}:", values)
print("Evaluations in this evolution demonstration:", evolution_evaluations)

# %% 9. Merge the whole original population with offspring, not just the selected mating parents.
combined = population + offspring
combined_objectives = objectives + offspring_objectives
labels = [f"P{i}" for i in range(population_size)] + [f"C{i}" for i in range(len(offspring))]
combined_fronts, combined_ranks, combined_distances = rank_and_crowding(combined_objectives)
print("\n[9] Merge and rerank 16 individuals: P = original population, C = offspring")
for rank, front in enumerate(combined_fronts, start=1):
    print(f"Front {rank}:", [labels[i] for i in front])

# %% 10. Environmental selection: keep complete fronts, then truncate the next by crowding distance.
environment_rng = Random(11)
survivors = environmental_selection(combined_objectives, population_size, environment_rng)
next_population = [combined[i].copy() for i in survivors]
next_objectives = [combined_objectives[i] for i in survivors]
print("\n[10] Next generation")
print("Selected sources:", [labels[i] for i in survivors])
for i, values in enumerate(next_objectives):
    print(f"New individual {i}:", values)
for assignment in next_population:
    check_feasibility(instance, assignment)
assert len(next_population) == population_size
assert evolution_evaluations == 16
print("Evaluations remain 16; environmental selection reuses the computed objectives.")
print("One generation update is complete. Continue from next_population without resetting seeds each generation.")

# %% 11. Back to cap61: total demand exceeds one facility's capacity, so check remaining capacity.
# This is a separate feasible construction example, not an evolutionary run on cap61.
if necessary_feasibility_issues(small_instance):
    raise ValueError("cap61 failed the necessary feasibility checks.")
remaining = list(small_instance.capacities)
capacity_assignment = [-1] * small_instance.n_customers
customer_order = sorted(
    range(small_instance.n_customers), key=lambda j: (-small_instance.demands[j], j)
)
for customer in customer_order:
    demand = small_instance.demands[customer]
    candidates = [i for i in range(small_instance.n_facilities) if remaining[i] >= demand]
    if not candidates:
        raise RuntimeError("This greedy construction failed; that does not prove the instance infeasible.")
    facility = min(candidates, key=lambda i: (remaining[i] - demand, i))
    capacity_assignment[customer] = facility
    remaining[facility] -= demand

capacity_loads = check_feasibility(small_instance, capacity_assignment)
print("\n[11] Feasible cap61 assignment: largest demands first")
for facility in sorted(set(capacity_assignment)):
    print(f"Facility {facility}: {capacity_loads[facility]:g} / {small_instance.capacities[facility]:g}")
print("Objectives:", evaluate(small_instance, capacity_assignment))

# %% 12. A feasible instance can have infeasible candidates: put both large customers in one facility.
largest, second_largest = customer_order[:2]
bad_assignment = capacity_assignment.copy()
bad_assignment[second_largest] = bad_assignment[largest]
print("\n[12] Infeasible candidate demonstration")
try:
    evaluate(small_instance, bad_assignment)
except ValueError as error:
    print("The capacity check rejected this candidate:", error)
else:
    raise AssertionError("This candidate should overload a facility.")
print("Do not split demand, omit customers, or alter data. General shared initialization and repair remain unfinished.")
print("Learning path: data -> evaluation -> population -> sorting -> parents -> offspring -> next generation -> capacity.")
print("This demonstrates one NSGA-II generation. Multi-generation runs, SPEA2, and formal experiments come later.")
