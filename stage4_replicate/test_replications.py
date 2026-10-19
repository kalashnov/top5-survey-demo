"""One test per registered spec: `pytest stage4_replicate`, or add `-k <wid>` for one paper."""
import importlib
from pathlib import Path

import pytest

from replications.spec import check

CASES = {}
for path in sorted((Path(__file__).parent / "replications").glob("W*.py")):
    paper = importlib.import_module(f"replications.{path.stem}")
    for name, (load, spec) in paper.SPECS.items():
        CASES[f"{path.stem}/{name}"] = (load, spec)


@pytest.mark.parametrize("case", CASES)
def test_replicates(case):
    load, spec = CASES[case]
    misses = [r for r in check(load(), spec) if not r.ok]
    assert not misses, "\n".join(f"{r.term}: published {r.published}, ours {r.ours}" for r in misses)
