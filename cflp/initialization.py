"""Shared feasible population initialization for NSGA-II and SPEA2."""

from numbers import Integral

from .feasibility import (
    check_feasibility,
    necessary_feasibility_issues,
)


# ===========================
# Individual initialization
# ===========================


def create_individual(instance, rng):
    """
    Create one feasible customer assignment.

    Customers are assigned from greatest demand to smallest demand.
    For each customer, randomly select one facility with enough
    remaining capacity.

    Larger customers are assigned first because they are harder
    to place later when facility capacities have already been used.
    """

    assignment = [-1] * instance.n_customers
    remaining_capacity = list(instance.capacities)

    # Random values are used to randomize customers with equal demand
    random_ties = [
        rng.random()
        for _ in range(instance.n_customers)
    ]

    customer_order = sorted(
        range(instance.n_customers),
        key=lambda customer: (
            -instance.demands[customer],
            random_ties[customer],
        ),
    )

    for customer in customer_order:

        demand = instance.demands[customer]

        feasible_facilities = [
            facility
            for facility in range(instance.n_facilities)
            if remaining_capacity[facility] >= demand
        ]

        # This construction attempt cannot continue, caller can retry with another randomized construction.
        if not feasible_facilities:
            raise ValueError(
                "No facility has enough remaining capacity "
                f"for customer {customer}."
            )

        # Prefer facilities that leave less unused capacity, best fit heuristic which reduces fragmented capacity
        # Randomize equal-capacity ties before stable best-fit sorting.
        rng.shuffle(feasible_facilities)
        feasible_facilities = sorted(
            feasible_facilities,
            key=lambda facility:
                remaining_capacity[facility] - demand,
        )

        # Randomly choose among the best few feasible facilities, keeps the population diverse
        number_of_choices = min(
            3,
            len(feasible_facilities),
        )

        facility = rng.choice(
            feasible_facilities[:number_of_choices]
        )

        assignment[customer] = facility
        remaining_capacity[facility] -= demand

    # Always verify the final chromosome before returning it
    check_feasibility(
        instance,
        assignment,
    )

    return assignment


# ==========================
# Population initialization
# ==========================

def initialize_population(
    instance,
    population_size,
    rng,
    max_attempts_per_individual=100,
):
    """
    Create a population of feasible customer assignments.

    The same initialization method is used by NSGA-II and SPEA2.
    Construction uses the supplied random generator so the same
    seed produces the same population.

    If one construction attempt fails, another randomized attempt
    is made. The number of retries is limited to avoid an infinite
    loop.
    """

    if (
        isinstance(population_size, bool)
        or not isinstance(population_size, Integral)
        or population_size <= 0
    ):
        raise ValueError(
            "Population size must be a positive integer."
        )

    if (
        isinstance(max_attempts_per_individual, bool)
        or not isinstance(max_attempts_per_individual, Integral)
        or max_attempts_per_individual <= 0
    ):
        raise ValueError(
            "Maximum attempts must be a positive integer."
        )

    # Check conditions that can prove an instance is infeasible before trying to construct the population
    issues = necessary_feasibility_issues(instance)

    if issues:
        raise ValueError(
            "Instance fails necessary feasibility checks: "
            + " ".join(issues)
        )

    population = []

    for _ in range(population_size):

        individual = None

        for _ in range(max_attempts_per_individual):

            try:
                individual = create_individual(
                    instance,
                    rng,
                )
                break

            except ValueError:
                # Try another randomized construction
                continue

        if individual is None:
            raise ValueError(
                "Could not create a feasible individual "
                f"after {max_attempts_per_individual} attempts."
            )

        population.append(individual)

    return population
