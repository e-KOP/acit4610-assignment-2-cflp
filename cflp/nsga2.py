"""NSGA-II selection building blocks; the evolution loop remains a learning task.

Order: nondominated sorting -> crowding distance -> tournament selection ->
shared variation/repair/evaluation -> elitist selection from parents + offspring.
"""

from math import inf
from numbers import Integral

from .pareto import dominates, nondominated_sort


def crowding_distance(objective_vectors, front):
    """Return {individual_index: distance}, calculated within one front.

    Normalize each objective by its range in this front. Skip constant
    objectives to avoid dividing by zero. For fronts of size <= 2, assign inf.
    Equal objective values use original index order as a deterministic tie-break.
    With >= 3 identical vectors all distances are zero, so selection is random.
    """
    if len(set(front)) != len(front):
        raise ValueError("A front must contain unique individual indices.")
    for i in front:
        if not 0 <= i < len(objective_vectors):
            raise ValueError("Front index is outside the population.")
        dominates(objective_vectors[i], objective_vectors[i])
    distances = {i: 0.0 for i in front}
    if len(front) <= 2:
        return {i: inf for i in front}

    for objective in range(2):
        ordered = sorted(front, key=lambda i: (objective_vectors[i][objective], i))
        minimum = objective_vectors[ordered[0]][objective]
        maximum = objective_vectors[ordered[-1]][objective]
        span = maximum - minimum
        if span == 0:
            continue
        distances[ordered[0]] = inf
        distances[ordered[-1]] = inf
        for position in range(1, len(ordered) - 1):
            previous_value = objective_vectors[ordered[position - 1]][objective]
            next_value = objective_vectors[ordered[position + 1]][objective]
            distances[ordered[position]] += (next_value - previous_value) / span
    return distances


def rank_and_crowding(objective_vectors):
    """Return fronts, one-based ranks, and distances aligned with the population."""
    fronts = nondominated_sort(objective_vectors)
    ranks = [0] * len(objective_vectors)
    distances = [0.0] * len(objective_vectors)
    for rank, front in enumerate(fronts, start=1):
        front_distances = crowding_distance(objective_vectors, front)
        for i in front:
            ranks[i] = rank
            distances[i] = front_distances[i]
    return fronts, ranks, distances


def tournament_winner(a, b, ranks, distances, rng):
    """Given two sampled indices, prefer lower rank, then greater crowding.

    Break complete ties with the caller's seeded random generator. Return an
    index only: selection does not mutate individuals or create offspring.
    """
    if ranks[a] != ranks[b]:
        return a if ranks[a] < ranks[b] else b
    if distances[a] != distances[b]:
        return a if distances[a] > distances[b] else b
    return rng.choice((a, b))


def environmental_selection(objective_vectors, population_size, rng):
    """Select original indices from the combined parent/offspring population.

    Accept complete fronts in rank order. If a front does not fit, take its
    greatest crowding distances, breaking equal distances randomly. Preserve
    separate individuals even when their objective vectors are equal.
    """
    if (isinstance(population_size, bool) or not isinstance(population_size, Integral)
            or not 0 <= population_size <= len(objective_vectors)):
        raise ValueError("Survivor count must be an integer between zero and candidate count.")
    fronts, ranks, distances = rank_and_crowding(objective_vectors)
    selected = []
    for front in fronts:
        remaining = population_size - len(selected)
        if remaining == 0:
            break
        if len(front) <= remaining:
            selected.extend(front)
        else:
            candidates = list(front)
            # Stable sorting after shuffling randomizes only equal-distance ties.
            rng.shuffle(candidates)
            candidates.sort(key=lambda i: distances[i], reverse=True)
            selected.extend(candidates[:remaining])
            break
    return selected


def run(instance, config, seed):
    """Return final feasible solutions and run metadata within the evaluation budget."""
    raise NotImplementedError("NSGA-II is a learning placeholder, not a working optimizer yet.")
