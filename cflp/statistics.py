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
