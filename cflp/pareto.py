"""Two-objective minimization, with explicit pairwise nondominated sorting."""

from math import isfinite


def dominates(objectives_a, objectives_b):
    """True iff A is no worse in both objectives and strictly better in one."""
    a1, a2 = objectives_a
    b1, b2 = objectives_b
    if not all(isfinite(value) for value in (a1, a2, b1, b2)):
        raise ValueError("Objective values must be finite.")
    no_worse = a1 <= b1 and a2 <= b2
    strictly_better = a1 < b1 or a2 < b2
    return no_worse and strictly_better


def nondominated_indices(objective_vectors):
    """Return first-front indices; equal objective vectors retain all individuals."""
    fronts = nondominated_sort(objective_vectors)
    return fronts[0] if fronts else []


def nondominated_sort(objective_vectors):
    """Return fronts of original indices in O(N**2) time and space.

    Equal vectors do not dominate each other. Keep them for population selection;
    unique-objective counts for reporting should deduplicate separately.
    """
    size = len(objective_vectors)
    dominated_by_count = [0] * size
    dominates_list = [[] for _ in range(size)]
    for vector in objective_vectors:
        dominates(vector, vector)  # Validate even when there is only one point.

    for a in range(size):
        for b in range(a + 1, size):
            if dominates(objective_vectors[a], objective_vectors[b]):
                dominates_list[a].append(b)
                dominated_by_count[b] += 1
            elif dominates(objective_vectors[b], objective_vectors[a]):
                dominates_list[b].append(a)
                dominated_by_count[a] += 1

    current_front = [i for i in range(size) if dominated_by_count[i] == 0]
    fronts = []
    while current_front:
        fronts.append(current_front)
        next_front = []
        for a in current_front:
            # Removing this front removes its dominance of the remaining points.
            for b in dominates_list[a]:
                dominated_by_count[b] -= 1
                if dominated_by_count[b] == 0:
                    next_front.append(b)
        current_front = sorted(next_front)
    return fronts
