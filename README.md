# Top-5 survey demo

This is a tutorial on a mass survey and replication of papers using an LLM. The tutorial teaches:

1. How to run/manage/schedule a hundreds of subagents
2. How to save on costs
3. How to write prompts

In this toy example, we will survey methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`. The we will take the empirical papers in the sample and ask the agents to replicate them in an organized way. Then next step is bounded by imagination only.

The whole tutorial is written with Claude in mind, but a large part of it is not pivoted towards Claude specifically. Some of the steps can run with any agent, others may require to rewrite some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough to not eat any sensible part of your quota on a 20 USD subscription

## Setup

Note: if you wish, ask you agent to help you with this part.

This repository analyses paper pdfs and data, which are not in this repo. you can either fetch them yourself as a part of Stage 1, or you can skip it and use the pdfs I provide. For this, you will need 

```bash
pip install -r requirements.txt
dvc remote modify --local r2ro access_key_id <key ID>
dvc remote modify --local r2ro secret_access_key <secret>
dvc pull -r r2ro
```


## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Condense.** Score each chunk of a paper and keep the best ~10K characters (Haiku).
3. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
4. **Download replication data.** 6 of the 50 so far.
5. **Replicate the published regressions.** 4 of the 50 so far.

## Stage 1: Collect papers

The first thing is to collect any public urls for each paper. The repo already contains urls for each paper in order to save time, but generally, a good approach is to ask your agent to write a script that will systematically review the following sources:

1. OpenAlex
2. SemanticScholar
3. NBER
4. Arxiv

This will contain mistakes, some links will lead to other papers, some links will lead to supplementary material instead. Some papers will have no link, even though the paper is made public on the author's website. A good approach is to run a number of haiku subagents who will be tasked to correct the mistakes/search the web for correct versions. This is more expensive then searching API of above sources with the code, but we have already narrowed down the task before handing it to LLMs. For this excercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here, and will learn about subagents on a more exciting example.

## Run stage 3

Uses your Claude Code login; `ANTHROPIC_API_KEY` must be unset.

```bash
python classify.py          # writes verdicts/<wid>.json
```

## Run stage 5

```bash
pytest test_replications.py            # one test per published column
```

`prompts/replicate.md` asks an agent to add a paper: `replications/<wid>.py` with its data loader and `SPECS`.
