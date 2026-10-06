"""Export pooled Pareto and HV mean/SD figures from the full comparison."""
import argparse
import json
import sys
from statistics import mean, stdev
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cflp.metrics import unique_front
from cflp.protocol import validate_records

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--results', type=Path, default=Path('results/comparison'))
parser.add_argument('--output', type=Path, default=Path('results/comparison/figures'))
args = parser.parse_args()
ROOT = args.results
OUTPUT = args.output
OUTPUT.mkdir(parents=True, exist_ok=True)
RECORDS = [json.loads(p.read_text()) for p in sorted((ROOT / 'runs').glob('*.json'))]
CONFIGS = [('A', 'smaller_population', 50), ('B', 'reference', 100), ('C', 'larger_population', 200)]
ALGORITHMS = [('nsga2', 'NSGA-II', '#2563eb', 'o'), ('spea2', 'SPEA2', '#e87916', '^')]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.titleweight': 'medium'})
validate_records(RECORDS)

def runs(instance, config, algorithm):
    group = sorted([r for r in RECORDS if r['instance'] == instance and r['configuration'] == config and r['algorithm'] == algorithm], key=lambda r: r['seed'])
    if [r['seed'] for r in group] != list(range(10)):
        raise ValueError(f'{instance}/{config}/{algorithm}: expected seeds 0–9 exactly once.')
    if any(r['status'] != 'completed' or r.get('evaluations') != 10000 for r in group):
        raise ValueError(f'{instance}/{config}/{algorithm}: expected completed 10,000-evaluation runs.')
    expected_population = next(size for _, name, size in CONFIGS if name == config)
    if any(r['parameters']['population_size'] != expected_population for r in group):
        raise ValueError(f'{instance}/{config}/{algorithm}: population size differs from the panel label.')
    return group

def style(ax):
    ax.grid(alpha=.15, zorder=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=9)

def export(fig, name):
    for ext in ('png', 'pdf', 'svg'):
        fig.savefig(OUTPUT / f'{name}.{ext}', dpi=160, facecolor='white')
    plt.close(fig)

def plot_pareto(ax, groups):
    counts = []
    for (algorithm, label, color, marker), group in zip(ALGORITHMS, groups):
        front = unique_front([p for r in group for p in r['objectives']])
        counts.append(f'{label}: {len(front)} points')
        ax.scatter([p[0]/1000 for p in front], [p[1]/1e6 for p in front],
                   s=65 if algorithm == 'nsga2' else 92, marker=marker,
                   facecolors=color if algorithm == 'nsga2' else 'none',
                   edgecolors=color, linewidths=1.6, alpha=.9, zorder=3)
    ax.set_xlabel('Facility opening cost, f1 (thousands)')
    ax.margins(x=.12, y=.16)
    style(ax)
    return '  /  '.join(counts)


def plot_hv(ax, groups):
    values = [[r['metrics']['hv'] for r in group] for group in groups]
    for index, (_, _, color, marker) in enumerate(ALGORITHMS):
        ax.errorbar(index, mean(values[index]), yerr=stdev(values[index]),
                    fmt=marker, color=color, markersize=9, capsize=9,
                    capthick=2, elinewidth=2, linestyle='none', zorder=3)
    ax.set_xticks([0, 1], ['NSGA-II', 'SPEA2'])
    ax.set_xlim(-.4, 1.4)
    ax.ticklabel_format(axis='y', style='plain', useOffset=False)
    ax.margins(y=.18)
    style(ax)
    return mean(values[0]) - mean(values[1])


def draw(category, instance):
    # Share axes within each metric row, never between unlike metrics.
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex='row', sharey='row')
    for col, (letter, config, population) in enumerate(CONFIGS):
        groups = [runs(instance, config, algorithm) for algorithm, _, _, _ in ALGORITHMS]
        counts = plot_pareto(axes[0, col], groups)
        axes[0, col].set_title(f'Configuration {letter} · population {population}\n{counts}', fontsize=10, pad=10)
        delta = plot_hv(axes[1, col], groups)
        axes[1, col].set_title(f'Configuration {letter} · HV mean ± SD\nMean ΔHV (NSGA-II − SPEA2): {delta:+.5f}', fontsize=10, pad=10)
    axes[0, 0].set_ylabel('Allocation cost, f2 (millions)')
    axes[1, 0].set_ylabel('Normalized hypervolume (HV) ↑')
    fig.suptitle(f'{instance} | {category} instance | Pareto and HV comparison',
                 x=.065, ha='left', y=.98, fontsize=18, weight='bold')
    handles = [Line2D([], [], linestyle='none', marker=marker,
                      markerfacecolor=color if algorithm == 'nsga2' else 'none',
                      markeredgecolor=color, markeredgewidth=1.6, markersize=8, label=label)
               for algorithm, label, color, marker in ALGORITHMS]
    fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(.98, .93), frameon=False, ncol=2)
    fig.text(.065, .91, 'Top: pooled non-dominated points; lower and left are better.\nBottom: mean HV ± one sample SD across 10 runs; higher is better.',
             color='#475569', fontsize=10, linespacing=1.6)
    fig.text(.065, .025, 'Seeds 0–9 · 10,000 evaluations per run · Axes are shared across A/B/C within each row; HV axes are zoomed\nPareto points are pooled separately per algorithm, not a typical run. HV error bars show run-to-run variation, not confidence intervals.',
             color='#475569', fontsize=10, linespacing=1.6)
    fig.subplots_adjust(left=.065, right=.98, top=.81, bottom=.14, wspace=.13, hspace=.48)
    export(fig, f'{instance}_comparison')


for category, instances in [('Small', ['cap61', 'cap62']), ('Medium', ['cap101', 'cap102']), ('Large', ['cap121', 'cap122'])]:
    for instance in instances:
        draw(category, instance)
print(f'Exported six figures as PNG/PDF/SVG to {OUTPUT}')
