from cflp.data import DATA_DIR, load_instance


instance = load_instance("cap101")
# %% Understand m and n: the numbers of candidate facilities and customers.
m = instance.n_facilities
n = instance.n_customers
print("Number of facilities m =", m)
print("Number of customers n =", n)

capacities = instance.capacities
fixed_costs = instance.fixed_costs
demands = instance.demands
costs = instance.allocation_costs

print("Facility 0 opening cost F[0] =", fixed_costs[0])
print("Facility 0 capacity S[0] =", capacities[0])

# %% d[j] and C[i][j]: customer demand and the cost of serving that entire demand.
print("Customer 0 demand d[0] =", demands[0])
print("Cost of serving customer 0 from facility 0, C[0][0] =", costs[0][0])
print("Do not multiply allocation costs by customer demand again.")

# %% Compare the cost of serving one customer from different facilities.
customer = 0
for facility in range(3):
    print(f"Facility {facility} -> customer {customer}: {costs[facility][customer]}")

# %% Check the raw file: m and n come first, followed by m capacity/opening-cost pairs.
# split() reads whitespace-separated tokens; a customer record may span multiple lines.
tokens = (DATA_DIR / f"{instance.name}.txt").read_text(encoding="ascii").split()
customer_start = 2 + 2 * m
print("First 6 raw tokens:", tokens[:6])
print("First customer's demand token:", tokens[customer_start])
print("First customer's first 3 allocation costs:", tokens[customer_start + 1:customer_start + 4])
assert float(tokens[customer_start]) == demands[0]
assert float(tokens[customer_start + 1]) == costs[0][0]

# %% Sufficient total capacity is necessary but does not guarantee indivisible assignments fit.
print("Total demand:", sum(demands))
print("Total capacity:", sum(capacities))
print("Data reading complete. Next, open cflp/data.py and study parse_instance step by step.")
