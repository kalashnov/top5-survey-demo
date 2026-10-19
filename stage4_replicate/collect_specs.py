"""Re-estimate every registered spec and write specs.csv: one row per published number."""
from dataclasses import asdict

import pandas as pd

from replications import registry
from replications.spec import check

specs = pd.DataFrame([
    {"spec": key, "formula": spec.formula, "vcov": str(spec.vcov), "sample": spec.sample, **asdict(row)}
    for key, (load, spec) in registry().items()
    for row in check(load(), spec)
])
specs.to_csv("specs.csv", index=False)
print(f"specs.csv: {len(specs)} rows, {specs['ok'].sum()} match")
