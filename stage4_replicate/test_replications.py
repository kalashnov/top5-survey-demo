"""One test per registered spec: `pytest stage4_replicate`, or add `-k <wid>` for one paper."""
import pytest

from replications import registry
from replications.spec import check


@pytest.mark.parametrize("case", registry())
def test_replicates(case):
    load, spec = registry()[case]
    misses = [r for r in check(load(), spec) if not r.ok]
    assert not misses, "\n".join(f"{r.term}: published {r.published}, ours {r.ours}" for r in misses)
