# %% 1. Load the real cap101 instance without changing its original values.
# Terminal: cd /home/xue/ACIT4610/CFLP, then python3 learn_cap101.py
from math import isclose

from cflp.data import load_instance, verify_data
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility, necessary_feasibility_issues
from cflp.representation import opened_facilities

verify_data()
instance = load_instance("cap101")
m = instance.n_facilities
n = instance.n_customers
print("Facilities m:", m, "Customers n:", n)
print("Total demand:", sum(instance.demands))
print("Capacity of each facility:", instance.capacities[0])
assert not necessary_feasibility_issues(instance)

# %% 2. Build a simple solution: assign every customer to facility 0.
# assignment[j] = i means customer j is served by facility i. IDs are zero-based.
assignment = [0] * n
print("Solution A assignments:", assignment)
print("Open facilities:", opened_facilities(instance, assignment))

# %% 3. Check unique assignments, assignment to open facilities, and capacity.
# Open facilities are inferred from usage, so valid encoding ensures the first two constraints.
loads = check_feasibility(instance, assignment)
print("Facility 0 load:", loads[0])
print("Facility 0 capacity:", instance.capacities[0])
print("Loads of the other facilities:", loads[1:])
assert loads[0] == sum(instance.demands) == instance.capacities[0]

# %% 4. Expand both objective sums and compare with the shared evaluator.
f1 = 0.0
for facility in opened_facilities(instance, assignment):
    f1 += instance.fixed_costs[facility]

f2 = 0.0
for customer, facility in enumerate(assignment):
    cost = instance.allocation_costs[facility][customer]
    f2 += cost  # C[i][j] already includes all demand; do not multiply by demands[j].
    if customer < 3:
        print(f"Customer {customer} -> facility {facility}: allocation cost {cost}")

evaluated_f1, evaluated_f2 = evaluate(instance, assignment)
# Repeated addition and sum may round slightly differently; compare with isclose.
assert isclose(f1, evaluated_f1) and isclose(f2, evaluated_f2)
print(f"Solution A: f1={f1:.2f}, f2={f2:.2f}")

# %% 5. Solution B: assign every customer to the facility with the lowest opening cost.
cheapest_facility = min(range(m), key=lambda i: instance.fixed_costs[i])
assignment_b = [cheapest_facility] * n
objectives_b = evaluate(instance, assignment_b)
print("Cheapest facility ID:", cheapest_facility)
print("Its opening cost:", instance.fixed_costs[cheapest_facility])
print(f"Solution B: f1={objectives_b[0]:.2f}, f2={objectives_b[1]:.2f}")
print("The zero opening cost is in the official data; it is not missing and must not be replaced.")

# %% 6. Solution C: each customer independently chooses the lowest allocation cost.
assignment_c = []
for customer in range(n):
    best_facility = min(
        range(m),
        key=lambda i: instance.allocation_costs[i][customer],
    )
    assignment_c.append(best_facility)

objectives_c = evaluate(instance, assignment_c)
print("Number of open facilities in solution C:", len(opened_facilities(instance, assignment_c)))
print(f"Solution C: f1={objectives_c[0]:.2f}, f2={objectives_c[1]:.2f}")
print("Every cap101 facility can hold total demand, so independent assignments cannot overload it.")
print("Do not assume this is feasible for instances with smaller facility capacities.")

# %% 7. Compare three real solutions; this is neither a MOEA run nor a complete Pareto front.
print("\nSolution   Opening cost f1   Allocation cost f2")
for label, candidate in (("A", assignment), ("B", assignment_b), ("C", assignment_c)):
    opening, allocation = evaluate(instance, candidate)
    print(f"{label:4} {opening:16.2f} {allocation:16.2f}")

assert isclose(f1, 7500) and isclose(f2, 1935118)
assert isclose(objectives_b[0], 0) and isclose(objectives_b[1], 1248142.9)
assert isclose(objectives_c[0], 180000) and isclose(objectives_c[1], 652291.15)
print("B has lower costs than A in both objectives: B dominates A.")
print("B has a lower opening cost; C has a lower allocation cost. Neither dominates the other.")
print("Comparing three solutions does not establish the complete true Pareto front.")
print("Next: generate a seeded population, evaluate it, and perform non-dominated sorting.")
