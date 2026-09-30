"""Customer assignment encoding: assignment[j] is the serving facility ID."""

from numbers import Integral


def validate_assignment(instance, assignment):
    """Each customer needs exactly one valid integer facility ID."""
    if len(assignment) != instance.n_customers:
        raise ValueError("Assignment length must equal the number of customers.")
    if any(
        isinstance(i, bool) or not isinstance(i, Integral)
        or not 0 <= i < instance.n_facilities for i in assignment
    ):
        raise ValueError("Facility IDs must be integers from 0 to m - 1.")


def opened_facilities(instance, assignment):
    """Used facilities are open; unused facilities are closed in this encoding."""
    validate_assignment(instance, assignment)
    return tuple(sorted(set(assignment)))
