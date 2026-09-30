"""Shared assignment operators; capacity must be checked after variation."""

from numbers import Integral


def validate_probability(probability):
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")


def crossover(parent_a, parent_b, probability, rng):
    """Single-point crossover, with probability per pair; return independent lists.

    A cut between customers exchanges the tails, preserving one facility ID per
    customer. This preserves encoding validity, not general capacity feasibility.
    """
    validate_probability(probability)
    if len(parent_a) != len(parent_b) or not parent_a:
        raise ValueError("Parents must have the same positive length.")
    child_a, child_b = list(parent_a), list(parent_b)
    if len(parent_a) < 2 or rng.random() >= probability:
        return child_a, child_b
    cut = rng.randrange(1, len(parent_a))
    return child_a[:cut] + child_b[cut:], child_b[:cut] + child_a[cut:]


def mutate(assignment, n_facilities, probability, rng):
    """Independently reassign each customer with the given per-gene probability.

    When mutation occurs, uniformly choose a different facility. With only one
    facility, return a copy unchanged. Never modify the original assignment.
    """
    validate_probability(probability)
    if isinstance(n_facilities, bool) or not isinstance(n_facilities, Integral) or n_facilities < 1:
        raise ValueError("The number of facilities must be a positive integer.")
    if any(isinstance(i, bool) or not isinstance(i, Integral) or not 0 <= i < n_facilities
           for i in assignment):
        raise ValueError("Assignment contains an invalid facility ID.")
    child = list(assignment)
    if n_facilities == 1:
        return child
    for customer, current_facility in enumerate(child):
        if rng.random() < probability:
            # Draw from m-1 options and skip the current facility's ID.
            replacement = rng.randrange(n_facilities - 1)
            if replacement >= current_facility:
                replacement += 1
            child[customer] = replacement
    return child
