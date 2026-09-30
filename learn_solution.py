# %% Teaching example only: this is not an OR-Library benchmark or formal experiment.
from cflp.data import Instance
from cflp.evaluation import evaluate
from cflp.feasibility import facility_loads
from cflp.representation import opened_facilities
from itertools import product

instance = Instance(
    name="teaching_example",
    capacities=(12, 7, 5),
    fixed_costs=(100, 60, 70),
    demands=(4, 3, 5),
    allocation_costs=((24, 18, 30), (8, 6, 40), (30, 24, 10)),
)

# %% A=0, B=1, C=2. Each position represents one customer.
assignment = [1, 1, 2]  # [B, B, C]
print("Customer assignments:", assignment)
print("Open facilities:", opened_facilities(instance, assignment))
print("Facility loads:", facility_loads(instance, assignment))

# %% Check feasibility before computing f1 and f2.
f1, f2 = evaluate(instance, assignment)
print("Opening cost f1 =", f1)
print("Allocation cost f2 =", f2)
assert (f1, f2) == (130, 24)

# %% Assigning every customer to B overloads it; this is not a feasible solution.
try:
    evaluate(instance, [1, 1, 1])
except ValueError as error:
    print("Expected infeasibility error:", error)

# %% Exercise: calculate these two solutions by hand, then run the code to check your answers.
print(evaluate(instance, [0, 0, 0]))
print(evaluate(instance, [0, 1, 2]))
# Next: enumerate 3**3 assignments with itertools.product and keep the feasible ones.
# %% Enumerate all assignments and keep feasible solutions.

feasible_solutions = []
total_count = 0

for assignment in product(
    range(instance.n_facilities),
    repeat=instance.n_customers,
):
    total_count += 1

    try:
        f1, f2 = evaluate(instance, assignment)
    except ValueError:
        # evaluate rejected an infeasible solution; skip this iteration.
        continue

    feasible_solutions.append((assignment, f1, f2))

print("Total assignments:", total_count)
print("Feasible assignments:", len(feasible_solutions))
print("Infeasible assignments:", total_count - len(feasible_solutions))

for assignment, f1, f2 in feasible_solutions:
    print(f"Assignment={assignment}, opening cost={f1}, allocation cost={f2}")
