# %% 1. An individual is a complete 50-customer assignment; a population contains several individuals.
from random import Random

from cflp.data import load_instance
from cflp.evaluation import evaluate
from cflp.pareto import dominates, nondominated_sort
from cflp.representation import opened_facilities

instance = load_instance("cap101")
population_size = 8
seed = 42
rng = Random(seed)

# This teaching initialization requires every facility to hold total demand. Do not use it for cap121.
if min(instance.capacities) < sum(instance.demands):
    raise ValueError("This teaching initialization requires each facility to hold total demand.")

# %% 2. Generate 8 random assignments. Rerunning this cell resets the seed for reproducibility.
rng = Random(seed)
population = []
for individual in range(population_size):
    # Choose a facility subset first so individuals can use different numbers of facilities.
    pool_size = rng.randint(1, instance.n_facilities)
    facility_pool = rng.sample(range(instance.n_facilities), pool_size)
    print(individual, facility_pool)
    assignment = []
    for customer in range(instance.n_customers):
        assignment.append(rng.choice(facility_pool))
    # Some facilities in the subset may remain unused; only those serving customers are opened.
    population.append(assignment)

print("Number of individuals:", len(population))

print("Customers per individual:", len(population[0]))

print("Complete assignment for each individual:")
for i, assignment in enumerate(population):
    print(f"Individual {i}: {assignment}")

# %% 3. Check feasibility before computing both costs for each solution.
objectives = []
for assignment in population:
    objectives.append(evaluate(instance, assignment))

print("\nIndividual  Open facilities      f1            f2")
for i, assignment in enumerate(population):
    f1, f2 = objectives[i]
    count = len(opened_facilities(instance, assignment))
    print(f"{i:4} {count:10} {f1:12.2f} {f2:14.2f}")
print("Evaluations in this cell:", len(objectives))

# %% 4. Dominance: no higher cost in either objective, and a strictly lower cost in at least one.
print("\nDominance relationships:")
for a in range(population_size):
    for b in range(population_size):
        if dominates(objectives[a], objectives[b]):
            print(f"Individual {a} dominates individual {b}")

# %% 5. Find the non-dominated front, remove it, and repeat to identify subsequent fronts.
fronts = nondominated_sort(objectives)
for rank, front in enumerate(fronts, start=1):
    print(f"Front {rank}: individual IDs {front}")

# %% 6. Assign each individual's rank for the selection step.
ranks = [0] * population_size
for rank, front in enumerate(fronts, start=1):
    for i in front:
        ranks[i] = rank

print("\nIndividual   Rank      f1            f2")
for i, (f1, f2) in enumerate(objectives):
    print(f"{i:4} {ranks[i]:6} {f1:12.2f} {f2:14.2f}")
assert sorted(i for front in fronts for i in front) == list(range(population_size))
print("The first front is non-dominated among these 8 solutions, not necessarily globally Pareto-optimal.")
print("No crossover, mutation, or evolution has run yet. Next: within-front crowding and parent selection.")
