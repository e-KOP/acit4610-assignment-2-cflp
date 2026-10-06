"""Validate comparable saved runs before aggregation, plotting, or inference."""

import json


def validate_records(records):
    """Require shared protocols across algorithms, while permitting partial batches.

    Algorithm-specific archive settings are checked within each algorithm. Paired
    initial populations must match when both records carry their fingerprint.
    Complete seed coverage is checked separately before statistical inference.
    """
    common, specific, identities, initial = {}, {}, set(), {}
    for record in records:
        if record['status'] != 'completed':
            continue
        group = (record['instance'], record['configuration'])
        identity = (*group, record['algorithm'], record['seed'])
        if identity in identities:
            raise ValueError('Duplicate run identity.')
        identities.add(identity)
        parameters = record['parameters']
        if record['evaluations'] != parameters['max_objective_evaluations']:
            raise ValueError('Saved evaluation count differs from its budget.')
        shared = {k: v for k, v in parameters.items() if k != 'archive_size_rule'}
        signature = json.dumps([shared, record['source_sha256'], record['data_sha256'],
                                record['metrics']['normalization'], record['environment']], sort_keys=True)
        if group in common and common[group] != signature:
            raise ValueError(f'Incomparable protocols across runs or algorithms: {group}.')
        common[group] = signature
        algorithm_key = (*group, record['algorithm'])
        algorithm_signature = json.dumps(parameters, sort_keys=True)
        if algorithm_key in specific and specific[algorithm_key] != algorithm_signature:
            raise ValueError(f'Inconsistent algorithm settings: {algorithm_key}.')
        specific[algorithm_key] = algorithm_signature
        pair = (*group, record['seed'])
        fingerprint = record.get('initial_population_sha256')
        if fingerprint is not None:
            if pair in initial and initial[pair] != fingerprint:
                raise ValueError(f'Paired initial populations differ: {pair}.')
            initial[pair] = fingerprint
