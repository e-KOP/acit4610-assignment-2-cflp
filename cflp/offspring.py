"""Shared variation, bounded repair retries, and feasible objective evaluation."""

from .operators import crossover, mutate, validate_probability
from .repair import repair_assignment
from .evaluation import evaluate
from .configuration import positive_integer


def generate_offspring(
    instance,
    parents,
    crossover_probability,
    mutation_probability,
    rng,
    number_of_offspring=None,
    max_attempts_per_child=50,
):
    """
    Generate feasible offspring from selected parents.

    Parents are paired in order. Each pair may undergo single-point
    crossover, followed by per-gene mutation. Every child is repaired
    before evaluation so only feasible offspring are returned.

    If repair fails for a candidate, variation is attempted again.
    Each parent-pair visit allows at most max_attempts_per_child variation
    attempts, with up to two repairs per attempt. Move to the next pair once
    at least one child succeeds. Exhaustion raises an error; never silently
    replace a failed candidate with a parent or evaluate an infeasible child.

    If number_of_offspring is given, generation stops after producing
    that many children.
    """

    if not parents:
        raise ValueError("At least one parent is required.")
    positive_integer(max_attempts_per_child, "Maximum offspring attempts")
    if number_of_offspring is not None:
        positive_integer(number_of_offspring, "Offspring count")
    validate_probability(crossover_probability)
    validate_probability(mutation_probability)
    offspring = []
    objective_vectors = []

    if number_of_offspring is None:
        number_of_offspring = len(parents)

    parent_index = 0

    while len(offspring) < number_of_offspring:

        parent_a = parents[parent_index % len(parents)]
        parent_b = parents[(parent_index + 1) % len(parents)]

        children_added = 0

        for _ in range(max_attempts_per_child):

            child_a, child_b = crossover(
                parent_a,
                parent_b,
                crossover_probability,
                rng,
            )

            children = [child_a, child_b]

            for child in children:

                if len(offspring) >= number_of_offspring:
                    break

                child = mutate(
                    child,
                    instance.n_facilities,
                    mutation_probability,
                    rng,
                )

                try:
                    child = repair_assignment(
                        instance,
                        child,
                        rng,
                    )

                except ValueError:
                    # This candidate could not be repaired.
                    # Try another variation of the parent pair.
                    continue

                objectives = evaluate(
                    instance,
                    child,
                )

                offspring.append(child)
                objective_vectors.append(objectives)
                children_added += 1

            if children_added > 0:
                break

        if children_added == 0:
            raise ValueError(
                "Could not generate a feasible offspring "
                f"after {max_attempts_per_child} attempts."
            )

        parent_index += 2

    return offspring, objective_vectors

