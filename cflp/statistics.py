"""Descriptive run summaries; never treat pooled fronts as independent runs."""

from collections import defaultdict
from statistics import mean, stdev


def summarize_runs(records):
    groups = defaultdict(list)
    for record in records:
        if record["status"] == "completed":
            groups[(record["instance"], record["configuration"], record["algorithm"])].append(record)
    rows = []
    for (instance, configuration, algorithm), runs in sorted(groups.items()):
        hv = [r["metrics"]["hv"] for r in runs]
        rows.append({"instance": instance, "configuration": configuration,
                     "algorithm": algorithm, "runs": len(runs),
                     "hv_mean": mean(hv), "hv_sd": stdev(hv) if len(hv) > 1 else None,
                     "hv_best": max(hv), "hv_worst": min(hv),
                     "nd_mean": mean(r["metrics"]["nd"] for r in runs),
                     "time_mean_seconds": mean(r["runtime_seconds"] for r in runs)})
    return rows


def paired_permutation_test(first, second):
    """Exact two-sided sign-flip test of the paired mean difference, first-second.

    Enumerate every within-pair label swap. The null requires exchangeability
    within independent pairs (symmetric paired differences). Seeds alone do not
    establish pairing; the caller must verify identical initial populations.
    """
    from itertools import product
    from math import fsum, isfinite
    if len(first) != len(second) or not 1 <= len(first) <= 20:
        raise ValueError('Exact paired test requires 1-20 equally sized pairs.')
    differences = [a-b for a,b in zip(first, second)]
    if not all(isfinite(v) for v in differences):
        raise ValueError('Statistical inputs must be finite.')
    observed = abs(fsum(differences))
    tolerance = 1e-12 * max(1.0, observed)
    extreme = sum(abs(fsum(sign*d for sign,d in zip(signs,differences))) >= observed-tolerance
                  for signs in product((-1,1), repeat=len(differences)))
    return extreme / 2**len(differences)


def holm_adjust(p_values):
    """Holm family-wise adjustment, retaining input order."""
    if any(not 0 <= p <= 1 for p in p_values):
        raise ValueError('P-values must lie between zero and one.')
    adjusted = [0.0]*len(p_values)
    previous = 0.0
    for rank, index in enumerate(sorted(range(len(p_values)), key=p_values.__getitem__)):
        previous = max(previous, min(1.0, (len(p_values)-rank)*p_values[index]))
        adjusted[index] = previous
    return adjusted


def compare_algorithms(records, plan):
    """Infer only after the entire predeclared HV family has complete paired runs."""
    from .protocol import validate_records
    validate_records(records)
    if any(r['status'] != 'completed' for r in records):
        return [], {'status': 'incomplete', 'reason': 'Failed runs are present.'}
    expected_seeds = set(plan['seeds'])
    if not 10 <= len(expected_seeds) <= 20:
        raise ValueError('Comparison requires 10-20 independent seed pairs.')
    groups = defaultdict(dict)
    for record in records:
        groups[(record['instance'],record['configuration'],record['algorithm'])][record['seed']] = record
    pairs = []
    for instance in plan['instances']:
        for configuration, overrides in plan['configurations'].items():
            a = groups[(instance,configuration,'nsga2')]
            b = groups[(instance,configuration,'spea2')]
            if set(a) != expected_seeds or set(b) != expected_seeds:
                return [], {'status':'incomplete','reason':f'Missing or unexpected seed coverage: {instance}/{configuration}.'}
            for seed in sorted(expected_seeds):
                for run in (a[seed],b[seed]):
                    expected = {**plan['common'],**overrides}
                    if any(run['parameters'].get(k) != v for k,v in expected.items()):
                        raise ValueError('Saved runs do not match the declared experiment plan.')
                if not a[seed].get('initial_population_sha256') or a[seed]['initial_population_sha256'] != b[seed].get('initial_population_sha256'):
                    raise ValueError('Paired inference requires matching initial-population fingerprints.')
            pairs.append((instance,configuration,a,b))
    rows = []
    for instance,configuration,a,b in pairs:
        first = [a[s]['metrics']['hv'] for s in sorted(expected_seeds)]
        second = [b[s]['metrics']['hv'] for s in sorted(expected_seeds)]
        differences = [x-y for x,y in zip(first,second)]
        rows.append({'instance':instance,'configuration':configuration,'metric':'hv',
                     'pairs':len(first),'nsga2_mean':mean(first),'spea2_mean':mean(second),
                     'mean_difference_nsga2_minus_spea2':mean(differences),
                     'paired_win_fraction_nsga2':mean(1.0 if d>0 else 0.5 if d==0 else 0.0 for d in differences),
                     'p_raw':paired_permutation_test(first,second)})
    for row,p in zip(rows,holm_adjust([r['p_raw'] for r in rows])):
        row.update(p_holm=p,reject_at_0_05=p<=.05)
    return rows, {'status':'complete','test':'exact_two_sided_paired_mean_permutation',
                  'metric':'hv','alpha':.05,'correction':'Holm', 'family_size':len(rows),
                  'pairing':'Same instance, configuration, seed and verified identical initial population.',
                  'null_assumption':'Exchangeable algorithm labels within independent initialization pairs.',
                  'effect_sizes':'Mean HV difference and paired win fraction (ties count as half).',
                  'secondary_metrics':'ND and runtime are descriptive; no significance claims.'}
