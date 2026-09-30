"""The two objectives stay separate; allocation costs already include demand."""

from .feasibility import check_feasibility
from .representation import opened_facilities


def evaluate(instance, assignment):
    """Return (opening cost, allocation cost), only after checking feasibility."""
    check_feasibility(instance, assignment)
    opening_cost = sum(instance.fixed_costs[i] for i in opened_facilities(instance, assignment))
    allocation_cost = sum(
        instance.allocation_costs[facility][customer]
        for customer, facility in enumerate(assignment)
    )
    return opening_cost, allocation_cost
