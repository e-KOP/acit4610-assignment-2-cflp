"""Read the original OR-Library files without changing their numeric values."""

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "or_library"
INSTANCE_SIZES = {
    "cap61": (16, 50), "cap62": (16, 50),
    "cap101": (25, 50), "cap102": (25, 50),
    "cap121": (50, 50), "cap122": (50, 50),
}


@dataclass(frozen=True)
class Instance:
    """Costs use [facility][customer]; Python IDs start at zero."""

    name: str
    capacities: tuple[float, ...]
    fixed_costs: tuple[float, ...]
    demands: tuple[float, ...]
    allocation_costs: tuple[tuple[float, ...], ...]

    @property
    def n_facilities(self):
        return len(self.capacities)

    @property
    def n_customers(self):
        return len(self.demands)

    def __post_init__(self):
        m, n = self.n_facilities, self.n_customers
        if not m or not n or len(self.fixed_costs) != m:
            raise ValueError("Invalid facility/customer dimensions.")
        if len(self.allocation_costs) != m or any(
            len(row) != n for row in self.allocation_costs
        ):
            raise ValueError("Allocation costs must have shape (facilities, customers).")
        for values in (self.capacities, self.fixed_costs, self.demands, *self.allocation_costs):
            if any(not isfinite(value) or value < 0 for value in values):
                raise ValueError("Instance values must be finite and nonnegative.")


def parse_instance(text, name="custom"):
    """Read whitespace tokens, since a customer's costs can span several lines.

    File order: m n; then m (capacity, fixed cost) pairs;
    then n (demand, m allocation costs) records.
    """
    tokens = text.split()
    if len(tokens) < 2:
        raise ValueError("Missing instance dimensions.")
    try:
        m, n = int(tokens[0]), int(tokens[1])
    except ValueError as error:
        raise ValueError("Instance dimensions must be integers.") from error
    if m <= 0 or n <= 0:
        raise ValueError("Instance dimensions must be positive.")
    expected = 2 + 2 * m + n * (m + 1)
    if len(tokens) != expected:
        raise ValueError(f"Expected {expected} tokens, found {len(tokens)}.")
    try:
        values = list(map(float, tokens[2:]))
    except ValueError as error:
        raise ValueError("Instance contains a nonnumeric value.") from error

    capacities = tuple(values[2 * i] for i in range(m))
    fixed_costs = tuple(values[2 * i + 1] for i in range(m))
    demands = []
    costs = [[0.0] * n for _ in range(m)]
    cursor = 2 * m
    for customer in range(n):
        demands.append(values[cursor])
        cursor += 1
        for facility in range(m):
            # The source groups costs by customer; the model stores C[i][j].
            costs[facility][customer] = values[cursor]
            cursor += 1
    return Instance(name, capacities, fixed_costs, tuple(demands), tuple(map(tuple, costs)))


def load_instance(name, data_dir=DATA_DIR):
    """Load one of the six assignment instances, with expected dimensions."""
    if name not in INSTANCE_SIZES:
        raise ValueError(f"Unknown instance {name!r}; choose from {', '.join(INSTANCE_SIZES)}.")
    path = Path(data_dir) / f"{name}.txt"
    instance = parse_instance(path.read_text(encoding="ascii"), name)
    if (instance.n_facilities, instance.n_customers) != INSTANCE_SIZES[name]:
        raise ValueError(f"Unexpected benchmark dimensions in {path}.")
    return instance


def verify_data():
    """Check every bundled file against its recorded SHA-256 and parse it."""
    manifest = json.loads((PROJECT_ROOT / "data" / "checksums.json").read_text())
    verified = []
    for name in INSTANCE_SIZES:
        record = manifest["instances"][name]
        path = PROJECT_ROOT / "data" / record["path"]
        content = path.read_bytes()
        if len(content) != record["bytes"] or sha256(content).hexdigest() != record["sha256"]:
            raise ValueError(f"Data integrity check failed: {name}.")
        load_instance(name)
        verified.append(name)
    return verified
