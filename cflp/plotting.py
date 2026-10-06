"""Pareto plots: standard-library SVG summaries and optional Matplotlib figures."""

from html import escape
import json
from pathlib import Path

from .metrics import unique_front
from .protocol import validate_records


def pareto_svg(series, title):
    """Plot labelled sets on shared raw-cost axes; callers define the pooling rule."""
    points = [p for values in series.values() for p in values]
    if not points:
        raise ValueError("Cannot plot an empty approximation set.")
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    dx, dy = max(xmax - xmin, 1), max(ymax - ymin, 1)
    xmin, xmax = xmin - .05 * dx, xmax + .05 * dx
    ymin, ymax = ymin - .05 * dy, ymax + .05 * dy
    sx = lambda x: 100 + 620 * (x - xmin) / (xmax - xmin)
    sy = lambda y: 430 - 340 * (y - ymin) / (ymax - ymin)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="560" viewBox="0 0 800 560">',
             '<rect width="800" height="560" fill="white"/>',
             '<g font-family="sans-serif" font-size="12" fill="#222">',
             f'<text x="400" y="28" text-anchor="middle">{escape(title)}</text>']
    for k in range(6):
        x, y = xmin + k * (xmax-xmin)/5, ymin + k*(ymax-ymin)/5
        parts += [f'<path d="M {sx(x)} 90 V 430 M 100 {sy(y)} H 720" stroke="#ddd"/>',
                  f'<text x="{sx(x)}" y="450" text-anchor="middle">{x:.4g}</text>',
                  f'<text x="90" y="{sy(y)+4}" text-anchor="end">{y:.4g}</text>']
    parts += ['<text x="400" y="480" text-anchor="middle">Facility opening cost (f1)</text>',
              '<text transform="translate(20 260) rotate(-90)" text-anchor="middle">Customer allocation cost (f2)</text>']
    for index, (label, values) in enumerate(series.items()):
        color = ['#2563eb', '#dc2626', '#15803d', '#9333ea'][index % 4]
        for x,y in values:
            parts.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="4" fill="{color}" fill-opacity="0.7"/>')
        parts.append(f'<text x="{100+index*180}" y="515" fill="{color}">{escape(label)}</text>')
    return ''.join(parts) + '</g></svg>'


CONFIGURATIONS = [("A", "smaller_population", 50),
                  ("B", "reference", 100),
                  ("C", "larger_population", 200)]
ALGORITHMS = {"nsga2": ("NSGA-II", "#2563eb", "o"),
              "spea2": ("SPEA2", "#dc2626", "^")}


def plot_instance(records, instance, output):
    """Export per-seed A/B/C panels; load Matplotlib only when requested."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError as error:
        raise ImportError(
            "Figure export requires: python3 -m pip install -r requirements-plotting.txt"
        ) from error
    output = Path(output)
    validate_records(records)
    selected = [r for r in records if r["instance"] == instance and r["status"] == "completed"]
    if not selected:
        raise ValueError(f"No completed runs for {instance}.")
    points = [p for r in selected for p in r["objectives"]]
    seeds = sorted({r["seed"] for r in selected})
    colors = {seed: plt.get_cmap("tab10")(index % 10) for index, seed in enumerate(seeds)}
    limits = []
    for axis, scale in [(0, 1000), (1, 1000000)]:
        low, high = min(p[axis] for p in points)/scale, max(p[axis] for p in points)/scale
        pad = max((high-low)*.09, .01)
        limits.append((max(0, low-pad), high+pad))
    fig, axes = plt.subplots(1, 3, figsize=(16, 6.8), sharex=True, sharey=True)
    present = set()
    for ax, (letter, config, population) in zip(axes, CONFIGURATIONS):
        counts = []
        for algorithm, (label, color, marker) in ALGORITHMS.items():
            runs = [r for r in selected if r["configuration"] == config and r["algorithm"] == algorithm]
            if not runs:
                continue
            if len({r['seed'] for r in runs}) != len(runs):
                raise ValueError("Duplicate seeds in a plot group.")
            if any(r['parameters']['population_size'] != population for r in runs):
                raise ValueError("Population size differs from the panel label.")
            for run in sorted(runs, key=lambda r: r["seed"]):
                individual_front = unique_front(run["objectives"])
                ax.plot([p[0]/1000 for p in individual_front],
                        [p[1]/1000000 for p in individual_front],
                        color=colors[run["seed"]], alpha=.48, lw=1,
                        marker=marker, ms=3.5,
                        linestyle="-" if algorithm == "nsga2" else "--", zorder=2)
            present.add(algorithm)
            counts.append(f"{label}: {len(runs)} independent fronts")
        pending = [label + ": pending" for algorithm, (label, _, _) in ALGORITHMS.items()
                   if not any(r['configuration'] == config and r['algorithm'] == algorithm for r in selected)]
        ax.set_title(f"Configuration {letter} | population {population}", fontsize=11, pad=12)
        ax.text(.96, .96, '\n'.join(counts + pending), transform=ax.transAxes,
                va="top", ha="right", fontsize=8.5, color="#475569",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.8))
        ax.set_xlim(*limits[0]); ax.set_ylim(*limits[1])
        ax.set_xlabel("Facility opening cost, f1 (thousands)", fontsize=10)
        ax.grid(alpha=.18, zorder=0)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel("Customer allocation cost, f2 (millions)", fontsize=10)
    category = {"cap61": "Small", "cap101": "Medium", "cap121": "Large"}.get(instance, "Benchmark")
    fig.suptitle(f"{instance} | {category} instance | Pareto approximation sets", fontsize=16, x=.06, ha="left", y=.98)
    handles = [Line2D([], [], color=colors[seed], marker="o", alpha=.6,
                      linewidth=1, markersize=4, label=f"Seed {seed}") for seed in seeds]
    for algorithm, (label, _, marker) in ALGORITHMS.items():
        if algorithm in present:
            handles.append(Line2D([], [], color="#334155", marker=marker,
                linestyle="-" if algorithm == "nsga2" else "--", label=label))
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.53, .92),
               ncol=6, frameon=False, fontsize=9)
    budgets = sorted({r['evaluations'] for r in selected})
    budget_text = f"{budgets[0]:,} evaluations per run" if len(budgets) == 1 else "Mixed evaluation budgets"
    caption = (f"Colored lines: individual final fronts, one per seed. {budget_text}.\n"
               "Lines only guide the eye; intermediate locations are not necessarily feasible. Axes are shared across configurations."
               + (" SPEA2: pending." if "spea2" not in present else ""))
    fig.text(.06, .035, caption, fontsize=9, color="#475569", linespacing=1.6)
    fig.subplots_adjust(left=.06, right=.98, top=.73, bottom=.18, wspace=.10)
    output.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(output / f"{instance}_pareto.{extension}", dpi=200, facecolor="white")
    plt.close(fig)



def plot_directory(result_dir, instances=None):
    """Read persisted runs and export focus-instance figures without rerunning search."""
    result_dir = Path(result_dir)
    records = [json.loads(path.read_text())
               for path in sorted((result_dir / "runs").glob("*.json"))]
    if not records:
        raise ValueError(f"No saved run records in {result_dir / 'runs'}.")
    output = result_dir / "figures"
    for instance in instances or ("cap61", "cap101", "cap121"):
        plot_instance(records, instance, output)
    return output
