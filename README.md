# Top-5 survey demo

This is a tutorial on a mass survey and replication of papers using an LLM. The tutorial teaches:

1. How to run/manage/schedule a hundreds of subagents
2. How to save on costs
3. How to write prompts

In this toy example, we will survey methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`. Then we will take the empirical papers in the sample and ask the agents to replicate them in an organized way. Then next step is bounded by imagination only.

The whole tutorial is written with Claude in mind, but a large part of it is not pivoted towards Claude specifically. Some of the steps can run with any agent, others may require to rewrite some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

## Setup

Note: if you wish, ask you agent to help you with this part.


## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Condense.** Score each chunk of a paper and keep the best ~10K characters (Haiku).
3. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
4. **Download replication data.** 6 of the 50 so far.
5. **Replicate the published regressions.** 4 of the 50 so far.

## Run stage 3

Uses your Claude Code login; `ANTHROPIC_API_KEY` must be unset.

```bash
pip install -r requirements.txt
dvc pull -r r2ro txt.dvc
python classify.py          # writes verdicts/<wid>.json
```

## Run stage 5

```bash
dvc pull -r r2ro datasets/W4401126511.dvc
pytest test_replications.py            # one test per published column
```

`prompts/replicate.md` asks an agent to add a paper: `replications/<wid>.py` with its data loader and `SPECS`.
