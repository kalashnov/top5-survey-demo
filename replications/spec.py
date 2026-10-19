"""A published regression column, and the check that re-estimates it."""
from dataclasses import dataclass, field

import pandas as pd
import pyfixest as pf


@dataclass(frozen=True)
class Spec:
    formula: str                 # pyfixest formula, e.g. "y ~ treat*female + age | village"
    vcov: str | dict             # "hetero" or {"CRV1": "village"}
    targets: dict[str, float]    # published coefficients, typed by hand
    n: int | None                # published N; None when the table prints none
    tol: float                   # half a unit of the last printed digit
    sample: str | None = None    # row filter for pandas .query(), e.g. "wave == 2"
    feols: dict = field(default_factory=dict)  # extra pf.feols arguments, e.g. {"fixef_rm": "none"}
    note: str = ""


@dataclass
class Row:
    term: str
    published: float
    ours: float | None
    ok: bool


def check(df: pd.DataFrame, spec: Spec) -> list[Row]:
    """One row per target coefficient, plus one for N."""
    if spec.sample:
        df = df.query(spec.sample)
    fit = pf.feols(spec.formula, data=df, vcov=spec.vcov, **spec.feols)
    coef = fit.coef()
    rows = [Row(t, v, coef.get(t), t in coef and abs(coef[t] - v) <= spec.tol)
            for t, v in spec.targets.items()]
    if spec.n is not None:
        rows.append(Row("N", spec.n, fit._N, fit._N == spec.n))
    return rows
