You are an expert in empirical economics. Read the paper and classify its methodology.

Answer each question with "yes", "no" or "unclear". Say "yes" only when the paper's text shows it; if you are inferring, say "unclear".

- `empirical`: Does the paper estimate regressions on real data? Pure theory, a method with no application, or simulations only: "no".
- `experimental`: Is the treatment randomly assigned (field or lab experiment, RCT, lottery)?
- `heterogeneity`: Does the paper analyze how the treatment effect differs across subjects (subgroup estimates, treatment × covariate interactions, causal forests)? Comparing treatment arms with each other is not heterogeneity.
- `costly_intervention`: Does the treatment cost real money, time or resources per subject treated (a cash transfer, a hired worker, a subsidy)? A letter or a nudge is not costly.
- `lots_of_controls`: Do the main regressions rely on a rich set of covariates, beyond the treatment and a few fixed effects?

If `empirical` is "no", every other answer is "no".

Reply with only this JSON object, no other text:

{"empirical": "...", "experimental": "...", "heterogeneity": "...", "costly_intervention": "...", "lots_of_controls": "..."}
