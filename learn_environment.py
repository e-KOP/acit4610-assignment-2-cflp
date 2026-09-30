# %% 1. Reproduce the earlier cap101 population using the same initialization rules.
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility
from cflp.nsga2 import environmental_selection, rank_and_crowding, tournament_winner
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

# %% 2. Reproduce parent selection, crossover, and mutation; generate and evaluate eight offspring.
selection_rng = Random(7)
parent_indices = []
for draw in range(population_size):
    a, b = selection_rng.sample(range(population_size), 2)
    parent_indices.append(tournament_winner(a, b, ranks, distances, selection_rng))
variation_rng = Random(21)
offspring = []
for start in range(0, population_size, 2):
    parent_a = population[parent_indices[start]]
    parent_b = population[parent_indices[start + 1]]
    children = crossover(parent_a, parent_b, 0.9, variation_rng)
    for child in children:
        offspring.append(mutate(child, instance.n_facilities, 0.02, variation_rng))
offspring_objectives = [evaluate(instance, child) for child in offspring]

# %% 3. Merge the entire original population with offspring, not just the selected mating parents.
combined = population + offspring
combined_objectives = objectives + offspring_objectives
labels = [f"P{i}" for i in range(population_size)] + [f"C{i}" for i in range(len(offspring))]
print("P = original population, C = offspring; all IDs are zero-based.")
print("Combined population size:", len(combined))
print("Combined indices 0..7 represent P0..P7; 8..15 represent C0..C7.")

# %% 4. Recompute ranks and crowding for the combined set; do not reuse the original values.
combined_fronts, combined_ranks, combined_distances = rank_and_crowding(combined_objectives)
for rank, front in enumerate(combined_fronts, start=1):
    print(f"Front {rank}:", [labels[i] for i in front])

# %% 5. Keep complete fronts that fit; use crowding only to truncate the first front that does not.
remaining = population_size
for rank, front in enumerate(combined_fronts, start=1):
    if remaining == 0:
        break
    print(f"{remaining} places remain; front {rank} contains {len(front)} individuals.")
    if len(front) <= remaining:
        print("Keep all:", [labels[i] for i in front])
        remaining -= len(front)
    else:
        print("This front does not fit. Prefer larger crowding distances and break equal distances randomly:")
        for i in front:
            print(f"  {labels[i]}: {combined_distances[i]:.4f}")
        break

# %% 6. Environmental selection returns indices into the combined population.
environment_rng = Random(11)
survivors = environmental_selection(combined_objectives, population_size, environment_rng)
print("\nSelected combined indices:", survivors)
print("Selected source labels:", [labels[i] for i in survivors])
print("Discarded source labels:", [labels[i] for i in range(len(combined)) if i not in survivors])

# %% 7. Build the next generation, reusing objectives without additional evaluations.
next_population = [combined[i].copy() for i in survivors]
next_objectives = [combined_objectives[i] for i in survivors]
print("\nNew ID  Source    f1            f2")
for new_index, old_index in enumerate(survivors):
    f1, f2 = next_objectives[new_index]
    print(f"{new_index:6} {labels[old_index]:5} {f1:12.2f} {f2:14.2f}")
assert len(next_population) == population_size
assert len(set(survivors)) == population_size
for assignment in next_population:
    check_feasibility(instance, assignment)
print("Evaluations remain 16: 8 initial + 8 offspring. Sorting and survival selection do not reevaluate.")
print("One generation update is complete. Continue from next_population, not the original population.")
print("Seeds are initialized once in this file. Do not reset them each generation in a multi-generation loop.")
print("Next: add an evaluation budget and a multi-generation loop. This is not yet a full experiment.")
