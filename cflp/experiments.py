"""Preview experiment combinations; executing MOEAs is a later learning task."""

import json
from .data import PROJECT_ROOT


def load_experiment_config():
    return json.loads((PROJECT_ROOT / "configs" / "experiments.json").read_text())


def experiment_plan(config):
    """Generate settings only; do not claim that these runs have been executed."""
    for instance in config["instances"]:
        for algorithm in config["algorithms"]:
            for name, overrides in config["configurations"].items():
                for seed in config["seeds"]:
                    yield {
                        "instance": instance, "algorithm": algorithm,
                        "configuration": name, "seed": seed,
                        "parameters": {**config["common"], **overrides},
                    }
