# %% 1. Reproduce the eight-individual cap101 population with the same random process as before.
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility
from cflp.nsga2 import rank_and_crowding, tournament_winner
from cflp.operators import crossover, mutate

instance = load_instance("cap101")
population_size = 8
rng = Random(42)
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires capacity >= total demand.")
population = []
for individual in range(population_size):
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    population.append([rng.choice(facility_pool) for customer in range(instance.n_customers)])
objectives = [evaluate(instance, assignment) for assignment in population]
fronts, ranks, distances = rank_and_crowding(objectives)

# %% 2. Select parents from existing individuals; this does not create new assignments.
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    parent_indices.append(tournament_winner(a, b, ranks, distances, selection_rng))
parents = [population[i].copy() for i in parent_indices]
print("Parent indices:", parent_indices)

# %% 3. Set probabilities and pair parents. Mutation probability 0.02 applies to each customer gene.
crossover_probability = 0.9
mutation_probability = 0.02
variation_rng = Random(21)  # A separate seed makes this lesson reproducible.
offspring = []
before_population = [assignment.copy() for assignment in population]
for start in range(0, population_size, 2):
    print(f"\nParent pair: {parent_indices[start]} and {parent_indices[start + 1]}")
    parent_a, parent_b = parents[start], parents[start + 1]

    # Single-point crossover: choose a random cut and exchange the parents' tails.
    # See cflp/operators.py for the cut; without crossover, return independent parent copies.
    crossed_a, crossed_b = crossover(parent_a, parent_b, crossover_probability, variation_rng)
    for parent, crossed in ((parent_a, crossed_a), (parent_b, crossed_b)):
        changed = [j for j in range(instance.n_customers) if crossed[j] != parent[j]]
        print("Customer IDs changed by crossover relative to the corresponding parent:", changed)

    # Per-customer mutation replaces a facility ID with a different valid facility ID.
    for crossed in (crossed_a, crossed_b):
        child = mutate(crossed, instance.n_facilities, mutation_probability, variation_rng)
        changes = [(j, crossed[j], child[j]) for j in range(instance.n_customers)
                   if crossed[j] != child[j]]
        print("Mutations (customer ID, previous facility, replacement facility):", changes)
        # Each cap101 facility holds total demand, so repair is unnecessary here; still check capacity.
        check_feasibility(instance, child)
        offspring.append(child)

# %% 4. Evaluate each of the eight offspring once, after checking feasibility.
offspring_objectives = [evaluate(instance, child) for child in offspring]
print("\nOffspring ID   Opening cost f1   Allocation cost f2")
for i, (f1, f2) in enumerate(offspring_objectives):
    print(f"{i:8} {f1:13.2f} {f2:15.2f}")
print("Objective evaluations: 8 initial + 8 offspring =", len(objectives) + len(offspring_objectives))
assert len(offspring) == population_size
assert population == before_population
assert parents == [population[i] for i in parent_indices]
assert len({id(child) for child in offspring}) == population_size

# %% 5. Offspring are not guaranteed to improve on or differ from their parents.
print("\nCosts may improve or worsen. Crossover and mutation do not guarantee improvement.")
print("There are still 8 original individuals plus 8 offspring; environmental selection has not run yet.")
print("Next: merge all 16 individuals, recompute ranks and crowding, and keep 8 for the next generation.")
