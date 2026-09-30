# %% 1. Load an updated small instance, preserving all original demands, capacities, and costs.
from cflp.data import load_instance, verify_data
from cflp.evaluation import evaluate
from cflp.feasibility import check_feasibility, necessary_feasibility_issues

verify_data()
instance = load_instance("cap61")  # You can also use cap62.
print("Instance:", instance.name)
print("Facilities:", instance.n_facilities, "Customers:", instance.n_customers)
print("Total capacity:", sum(instance.capacities), "Total demand:", sum(instance.demands))
print("Maximum facility capacity:", max(instance.capacities), "Maximum customer demand:", max(instance.demands))

# %% 2. Passing necessary conditions does not validate every assignment; construct and check one.
issues = necessary_feasibility_issues(instance)
if issues:
    raise ValueError("; ".join(issues))
print("Necessary conditions pass. Now try to construct a complete assignment.")

# %% 3. Teaching construction: largest demand first; choose the tightest remaining capacity that fits.
# This is a deterministic greedy demonstration, not a complete MOEA or general repair procedure.
remaining = list(instance.capacities)
assignment = [-1] * instance.n_customers
customer_order = sorted(range(instance.n_customers), key=lambda j: (-instance.demands[j], j))

for customer in customer_order:
    demand = instance.demands[customer]
    candidates = [i for i in range(instance.n_facilities) if remaining[i] >= demand]
    if not candidates:
        raise RuntimeError("This greedy construction failed; that does not prove the instance infeasible.")
    facility = min(candidates, key=lambda i: (remaining[i] - demand, i))
    assignment[customer] = facility
    remaining[facility] -= demand

# %% 4. Recheck every assignment and facility capacity before evaluating both objectives.
loads = check_feasibility(instance, assignment)
print("Complete assignment of all 50 customers:", assignment)
for facility in sorted(set(assignment)):
    print(f"Facility {facility}: load {loads[facility]:g} / capacity {instance.capacities[facility]:g}")
print("Objectives (opening cost, allocation cost):", evaluate(instance, assignment))
print("This demonstrates feasibility, not optimal cost.")

# %% 5. Two customers may each fit individually but exceed capacity when assigned together.
largest, second_largest = customer_order[:2]
combined_demand = instance.demands[largest] + instance.demands[second_largest]
print(f"Combined demand of customers {largest} and {second_largest}: {combined_demand:g}")
bad_assignment = assignment.copy()
bad_assignment[second_largest] = bad_assignment[largest]
try:
    evaluate(instance, bad_assignment)
except ValueError as error:
    print("Expected capacity error:", error)
else:
    raise AssertionError("The capacity check should reject this teaching candidate.")

# %% 6. Shared feasibility handling is still needed after replacing the benchmark instances.
print("Check candidates after initialization, crossover, and mutation; repair or regenerate using shared rules.")
print("General initialization and repair remain to be implemented. Do not split demand, omit customers, or change data.")
