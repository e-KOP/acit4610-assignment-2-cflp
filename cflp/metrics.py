"""Exact two-objective HV with instance-based, algorithm-independent scaling."""

from math import isfinite
from .pareto import nondominated_indices


def unique_front(objective_vectors):
    vectors = sorted(set(map(tuple, objective_vectors)))
    return [vectors[i] for i in nondominated_indices(vectors)]


def normalization_spec(instance):
    """All feasible costs lie in [0, upper]; zero-cost axes use scale one.

    Opening cost cannot exceed all facility costs. Allocation cost cannot
    exceed the sum of each customer's most expensive allocation. These
    conservative bounds are fixed before running either algorithm.
    """
    upper = [sum(instance.fixed_costs), sum(
        max(row[j] for row in instance.allocation_costs)
        for j in range(instance.n_customers)
    )]
    return {"method": "instance_cost_upper_bounds", "lower": [0.0, 0.0],
            "scale": [value if value > 0 else 1.0 for value in upper],
            "reference_point": [1.1, 1.1]}


def hypervolume_2d(objective_vectors, reference_point):
    """Area of dominated rectangle union for minimization; duplicates count once."""
    rx, ry = reference_point
    if not all(isfinite(v) for v in (rx, ry)):
        raise ValueError("Reference point must be finite.")
    front = unique_front(objective_vectors)
    if any(x >= rx or y >= ry for x, y in front):
        raise ValueError("Reference point must be strictly worse than every front point.")
    area, previous_y = 0.0, ry
    for x, y in front:
        area += (rx - x) * (previous_y - y)
        previous_y = y
    return area


def calculate_metrics(instance, objective_vectors):
    spec = normalization_spec(instance)
    front = unique_front(objective_vectors)
    normalized = [[v / scale for v, scale in zip(point, spec["scale"])] for point in front]
    if any(v < 0 or v > 1 + 1e-12 for point in normalized for v in point):
        raise ValueError("Objective values exceed the instance normalization bounds.")
    return {"hv": hypervolume_2d(normalized, spec["reference_point"]),
            "nd": len(front), "normalization": spec}
