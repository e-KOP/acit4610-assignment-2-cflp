"""Check capacity before evaluating a candidate solution."""

from .representation import validate_assignment


def necessary_feasibility_issues(instance):
    """Return proofs of infeasibility for indivisible customer assignments.

    An empty result only means these necessary conditions pass; it does not
    prove that all customers can be packed into the available facilities.
    """
    issues = []
    if sum(instance.demands) > sum(instance.capacities):
        issues.append("Total demand exceeds total facility capacity.")
    maximum_capacity = max(instance.capacities)
    for customer, demand in enumerate(instance.demands):
        if demand > maximum_capacity:
            issues.append(
                f"Customer {customer} (zero-based) demand {demand:g} exceeds "
                f"every facility's capacity (maximum {maximum_capacity:g})."
            )
    return tuple(issues)


def facility_loads(instance, assignment):
    validate_assignment(instance, assignment)
    loads = [0.0] * instance.n_facilities
    for customer, facility in enumerate(assignment):
        loads[facility] += instance.demands[customer]
    return tuple(loads)


def check_feasibility(instance, assignment):
    """Raise ValueError for an invalid solution; return loads for a valid one."""
    loads = facility_loads(instance, assignment)
    for facility, (load, capacity) in enumerate(zip(loads, instance.capacities)):
        if load > capacity:
            raise ValueError(f"Facility {facility} is overloaded: {load:g} > {capacity:g}.")
    return loads
