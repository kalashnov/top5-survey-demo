"""One module per paper, `W<wid>.py`, each with a `SPECS` dict; `registry()` gathers them."""
import importlib
from functools import cache
from pathlib import Path


@cache
def registry() -> dict:
    """Every registered spec as `{"<wid>/<spec name>": (load, Spec)}`, found by scanning this folder."""
    specs = {}
    for path in sorted(Path(__file__).parent.glob("W*.py")):
        paper = importlib.import_module(f"{__name__}.{path.stem}")
        for name, entry in paper.SPECS.items():
            specs[f"{path.stem}/{name}"] = entry
    return specs
