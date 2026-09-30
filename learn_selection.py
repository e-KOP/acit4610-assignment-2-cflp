# %% 1. Reproduce the cap101 population without importing lesson scripts and triggering their output.
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.nsga2 import crowding_distance, rank_and_crowding, tournament_winner

instance = load_instance("cap101")
population_size = 8
rng = Random(42)
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires capacity >= total demand.")
population = []
for individual in range(population_size):
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    assignment = [rng.choice(facility_pool) for customer in range(instance.n_customers)]
    population.append(assignment)
objectives = [evaluate(instance, assignment) for assignment in population]

# %% 2. Compute crowding within each front; it describes objective-space density, not geography.
fronts, ranks, distances = rank_and_crowding(objectives)
print("Fronts:", fronts)
print("Individual  Rank  Crowding      f1           f2")
for i, (f1, f2) in enumerate(objectives):
    print(f"{i:4} {ranks[i]:5} {distances[i]:9.4f} {f1:11.2f} {f2:13.2f}")
print("inf protects boundary points; it is not infinite cost and never takes priority over a better rank.")

# %% 3. Expand the real second front's distance calculation without changing any source data.
front = fronts[1]
print("\nSecond front in detail:", front)
for objective in range(2):
    ordered = sorted(front, key=lambda i: (objectives[i][objective], i))
    minimum = objectives[ordered[0]][objective]
    maximum = objectives[ordered[-1]][objective]
    print(f"Sorted by f{objective + 1}: {ordered}; range {minimum:.2f} to {maximum:.2f}")
    if maximum == minimum:
        print("This objective has zero range; skip it to avoid division by zero.")
        continue
    print(f"Boundary individuals {ordered[0]} and {ordered[-1]} receive infinite crowding distance.")
    for position in range(1, len(ordered) - 1):
        i = ordered[position]
        previous_value = objectives[ordered[position - 1]][objective]
        next_value = objectives[ordered[position + 1]][objective]
        contribution = (next_value - previous_value) / (maximum - minimum)
        print(f"Individual {i}, contribution from f{objective + 1} = {contribution:.4f}")

# %% 4. Four non-dominated teaching points illustrate different distances for interior points.
# These points explain crowding only; they are not cap101 data or experimental results.
teaching_points = [(1, 10), (2, 7), (5, 4), (9, 1)]
print("\nCrowding distances for the hand-calculated example:", crowding_distance(teaching_points, [0, 1, 2, 3]))
# Individual 1: (5-1)/(9-1) + (10-4)/(10-1) = 1.166666...
# Individual 2: (9-2)/(9-1) + (7-1)/(10-1) = 1.541666...

# %% 5. Compare rank first, then crowding distance within the same rank.
selection_rng = Random(7)
for a, b in ((6, 7), (3, 4), (5, 6)):
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    print(f"Individual {a} vs {b}: winner {winner}")
print("Prefer lower rank, then larger crowding distance; break complete ties randomly.")

# %% 6. Sample two individuals and select one parent; repeat independently 8 times.
# No duplicate within a tournament; individuals can be sampled and selected again across tournaments.
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    winner = tournament_winner(a, b, ranks, distances, selection_rng)
    parent_indices.append(winner)
    print(f"Draw {draw + 1}: sampled {a}, {b} -> selected {winner}")
parents = [population[i].copy() for i in parent_indices]
print("Parent indices:", parent_indices)
assert all(parent == population[i] and parent is not population[i]
           for parent, i in zip(parents, parent_indices))
print("Only parent selection and copying have occurred; no new assignments or population replacement yet.")
print("Next: pair parents, create offspring through crossover and mutation, then evaluate offspring.")
