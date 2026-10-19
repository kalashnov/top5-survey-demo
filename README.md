# Top-5 survey demo

This is a tutorial on a mass survey and replication of papers using an LLM. The tutorial teaches:

1. How to run/manage/schedule hundreds of subagents
  1.   With API
  2.   Simply in chat
4. How to save on costs
   1. With local models
   2. With ...
6. How to write prompts

In this toy example, we will:
1. survey methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`.
2. Ask the agents to replicate the empirical papers for the sample in an organized way.
3. Next step is bounded by imagination.

The whole tutorial is written with Claude in mind, but a large part of it is not pivoted towards Claude specifically. Some of the steps can run with any agent, others may require to rewrite some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough to not eat any sensible part of your quota on a 20 USD subscription

## Navigating the tutorial

## Setup

Note: if you wish, ask you agent to help you with this part.

This repository analyses paper pdfs and data, which are not in this repo. you can either fetch them yourself as a part of Stage 1, or you can skip it and use the pdfs I provide. For this, you will need 

```bash
pip install -r requirements.txt
dvc remote modify --local r2ro access_key_id <key ID>
dvc remote modify --local r2ro secret_access_key <secret>
dvc pull -r r2ro
```

The agents run on your Claude account. With a Claude subscription, create a token once (needs Claude Code installed) and export it in the shell you run the code from:

```bash
claude setup-token                       # log in in the browser; it prints a long-lived token
export CLAUDE_CODE_OAUTH_TOKEN=<token>
```

With an API key instead, `export ANTHROPIC_API_KEY=<key>`: the same code, billed per token. Set only one of the two.

## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Condense.** Score each chunk of a paper and keep the best ~10K characters (Haiku).
3. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
4. **Download replication data.** 6 of the 50 so far.
5. **Replicate the published regressions.** 5 of the 50 so far.

## Stage 1: Collect papers

The first thing is to collect any public urls for each paper. The repo already contains urls for each paper in order to save time, but generally, a good approach is to ask your agent to write a script that will systematically review the following sources:

1. OpenAlex
2. SemanticScholar
3. NBER
4. Arxiv

This will contain mistakes, some links will lead to other papers, some links will lead to supplementary material instead. Some papers will have no link, even though the paper is made public on the author's website. A good approach is to run a number of haiku subagents who will be tasked to correct the mistakes/search the web for correct versions. This is more expensive then searching API of above sources with the code, but we have already narrowed down the task before handing it to LLMs. For this excercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here, and will learn about subagents on a more exciting example.

To download the PDFs from my list, run (this will take a few minutes):

```bash
python fetch_pdfs.py
```

Then extract the plan text from pdf:

```bash
python extract_text.py
```


## Run stage 3

Now we arrive to fun part: running an army of subagents

```bash
python classify.py          # writes verdicts/<wid>.json
```

## Stage 4: Download replication data

For dataset downloading we follow the same approach as for pdfs. We first need to collect a list of urls (which are already collected for this example). Ask the agent to write code that systematically searches the following sources:

1. DataCite
2. Harvard Dataverse
3. Zenodo
4. ScholeXplorer (OpenAIRE)
5. Crossref
6. World Bank Microdata Library
7. Econometric Society
8. The paper's own text for direct links

When you have the links, downloading them is more of a problem, compared to PDFs, because it usually requires you to consent to something and/or to leave your contacts. Some repositories (e.g. Harvard Dataverse and Zenodo) have api. You can ask your agent to figure the API out and run code to download datasets. Anyway, you need to babysit it.

For some repos downloading cannot be efficiently automated. Here are the options:

1. Ask Claude for Chrome to open each of the links in the new tab and go over them manually
2. Ask Claude for Chrome to download themselves: this spends a lot of tokens, is very slow, quite unreliable, but might save your own time.

For this tutorial I suggest to manually download a few replication packages, e.g. these. After they are downloaded just ask Claude to go into your downloads folder and copy them into the project

| Paper | Size | Repository | Package |
|---|---|---|---|
| W4401126511, AER 2024 | 4 MB | openICPSR | https://doi.org/10.3886/E197302V1 |
| W4405354213, REStud 2024 | 16 MB | Zenodo | https://doi.org/10.5281/zenodo.10783446 |
| W4387449673, JPE 2023 | 20 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/NYSNOT |
| W3174918233, AER 2021 | 33 MB | openICPSR | https://doi.org/10.3886/E121941V1 |
| W4407240810, QJE 2025 | 214 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/PDFDKR |
| W3186531035, AER 2024 | 1.2 GB | openICPSR | https://doi.org/10.3886/E198004V1 |

## Run stage 5

```bash
pytest test_replications.py            # one test per published column
```

`prompts/replicate.md` asks an agent to add a paper: `replications/<wid>.py` with its data loader and `SPECS`.
