"""Deterministic capacity repair that prioritises fewer gene changes."""

from .feasibility import check_feasibility, facility_loads


def _select_move(instance, assignment, loads, source):
    """Prefer one-move relief, then largest demand; use best-fit destinations."""
    excess = loads[source] - instance.capacities[source]
    best = None
    for customer, facility in enumerate(assignment):
        demand = instance.demands[customer]
        if facility != source or demand == 0:
            continue
        for destination, capacity in enumerate(instance.capacities):
            remaining = capacity - (loads[destination] + demand)
            if destination == source or remaining < 0:
                continue
            # Customer ID breaks demand ties before comparing destinations.
            priority = (0, demand) if demand >= excess else (1, -demand)
            candidate = (*priority, customer, remaining, destination)
            if best is None or candidate < best:
                best = candidate
    return None if best is None else (best[2], best[4])


def repair_assignment(instance, assignment, rng=None):
    """Return a feasible copy using at most one relocation per customer.

    Select the largest overload (lowest facility ID on ties). Among customers
    with a feasible destination, prefer the smallest demand that eliminates
    the overload; otherwise choose the largest demand. Choose the destination
    with the least remaining capacity, including unused facilities. Customer
    and destination ties use their lowest IDs. This heuristic does not promise
    a globally minimum number of changed genes or minimum objective values.

    Invalid encodings or a lack of feasible relocations raise ValueError;
    relocation failure is not proof that the instance itself is infeasible.
    Neither the input assignment nor the instance is modified. The optional
    rng is retained for the shared operator interface but is not consumed.
    """
    repaired = list(assignment)
    loads = list(facility_loads(instance, repaired))
    for _ in range(instance.n_customers):
        source = min(
            (i for i, load in enumerate(loads) if load > instance.capacities[i]),
            key=lambda i: (instance.capacities[i] - loads[i], i),
            default=None,
        )
        if source is None:
            break
        move = _select_move(instance, repaired, loads, source)
        if move is None:
            raise ValueError(
                f"Capacity repair stalled at facility {source}: "
                "no customer has a feasible destination."
            )
        customer, destination = move
        repaired[customer] = destination
        loads = list(facility_loads(instance, repaired))
        # Receivers remain feasible, so a relocated customer never moves again.

    check_feasibility(instance, repaired)
    return repaired
