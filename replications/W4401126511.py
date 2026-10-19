"""Indirect Effects of Access to Finance (AER 2024): Tables 4 and 5, from the article PDF."""
from functools import cache

import pandas as pd

from replications.spec import Spec

DATA = "datasets/W4401126511/Data and Do-file/loanmain.dta"


@cache
def load() -> pd.DataFrame:
    """Firm x round panel, as shipped."""
    df = pd.read_stata(DATA, convert_categoricals=False)
    df["untype"] = 1.0 - df["type"]  # loan_main.do l.446
    return df


def table4(outcome: str, targets: dict, n: int) -> Spec:
    """`xtreg y post interpost inter4post, fe`; type and the treated share are absorbed by firm."""
    return Spec(f"{outcome} ~ post + type:post + treatratio_comp:post | firmid",
                vcov={"CRV1": "survey_town"}, targets=targets, n=n, tol=5e-4,
                feols={"fixef_rm": "none"})  # Stata keeps singleton firms


def table5(outcome: str, targets: dict, n: int) -> Spec:
    """The indirect effect split by the firm's own treatment status."""
    return Spec(f"{outcome} ~ post + type:post + type:post:treatratio_comp"
                f" + untype:post:treatratio_comp | firmid",
                vcov={"CRV1": "survey_town"}, targets=targets, n=n, tol=5e-4,
                feols={"fixef_rm": "none"})


SPECS = {
    "t4_sales": (load, table4("lnpart5revenue", {"type:post": 0.099, "treatratio_comp:post": -0.086}, 8612)),
    "t4_wage": (load, table4("lnwage_cost", {"type:post": 0.101, "treatratio_comp:post": -0.069}, 8602)),
    "t5_sales": (load, table5("lnpart5revenue", {"type:post": 0.070,
                                                  "type:post:treatratio_comp": -0.049,
                                                  "untype:post:treatratio_comp": -0.094}, 8612)),
}
