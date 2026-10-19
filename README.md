# Top-5 survey demo

REFER TO PAUL GOLDSMITH, HULL, CR

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

The tutorial is organized in sections. Each section have some writing, explaining best practices. However, if you just want to skip it and execute code, skip to **what to do** paragraph. Also, if you are not interested in some stages, you may ask your subagent to do this specific stage for you

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
2. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
3. **Download replication data.** 6 of the 50 so far.
4. **Replicate the published regressions.** 5 of the 50 so far.

## Stage 1: Collect papers

The first thing is to collect any public urls for each paper. The repo already contains urls for each paper in order to save time, but generally, a good approach is to ask your agent to write a script that will systematically review the following sources:

1. OpenAlex
2. SemanticScholar
3. NBER
4. Arxiv

This will contain mistakes, some links will lead to other papers, some links will lead to supplementary material instead. Some papers will have no link, even though the paper is made public on the author's website. A good approach is to run a number of haiku subagents who will be tasked to correct the mistakes/search the web for correct versions. This is more expensive then searching API of above sources with the code, but we have already narrowed down the task before handing it to LLMs. For this excercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here, and will learn about subagents on a more exciting example.

**What to do.** To download the PDFs from my list, run (this will take a few minutes):

```bash
python fetch_pdfs.py
```

Then extract the plan text from pdf:

```bash
python extract_text.py
```


## Stage 2: classifying the methodology of papers

Now we arrive to fun part: running an army of subagents. The idea of this stage is as follows. Let the agent's read the paper and answer a few question: do they run an experiment? do they run difference-in-differences? What is the source of data?

Our virtues and our vices:

Virtue: We ask a set of simple questions on a given input. No exploration or problem solving needed
Vice: We need to classify thousands of papers.
Vice: We need structured output for it to be ready to load in STATA and explore.

Therefore, we will heavily optimize the cost per paper. Here are a few important choices:

1. We can run a local model to pre-screen paper texts to throw away anything not related to methodology. UCSD's slurm cluster can run local model of the size enough to do this task. I do not cover this in detail, because it requires more involvement. Less text to input -> less costs.
2. We run a very verbose, clear prompt with a lot of examples. And we validate this prompt with a few experiments/iterations. The prompt for this task is given in [`prompts/system_prompt.md`](prompts/system_prompt.md). A really good prompt can allow us to use smaller models.
3. One can worry that a larger prompt means more input, therefore more costs. But, the prompt doesn't change from request to request, and if everything is designed correctly, it is cached, and is billed at a 10% rate. The larger part of the input is the paper anyway.
4. Finally, we use a feature called "structured output". It constrains the model to output a valid json, which we can then use to construct our final dataset. The schema for this application is in [`prompts/json_schema.json`](prompts/json_schema.json).

**What to do.** To run the classification analysis, just execute:

```bash
python classify.py          # writes verdicts/<wid>.json
```

This will output one json per paper with the answers to the questions we asked

## Stage 3: Download replication data

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

Sometimes the packages doesn't contain the data itself, but provide instructions how to fetch this data from another source. Agents are quite good at doing that most of the times, just ask them to follow author's instructions.

**What to do.** For this tutorial I suggest to manually download a few replication packages, e.g. these. After they are downloaded just ask Claude to go into your downloads folder and copy them into the project

| Paper | Size | Repository | Package |
|---|---|---|---|
| W4401126511, AER 2024 | 4 MB | openICPSR | https://doi.org/10.3886/E197302V1 |
| W4405354213, REStud 2024 | 16 MB | Zenodo | https://doi.org/10.5281/zenodo.10783446 |
| W4387449673, JPE 2023 | 20 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/NYSNOT |
| W3174918233, AER 2021 | 33 MB | openICPSR | https://doi.org/10.3886/E121941V1 |
| W4407240810, QJE 2025 | 214 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/PDFDKR |
| W3186531035, AER 2024 | 1.2 GB | openICPSR | https://doi.org/10.3886/E198004V1 |

## Stage 4: replication

This is another stage, where we will heavily used subagents. However, this time the task is not clear cut, and we will need the agents to explore and use whatever tools they need. We however need to add structure to their search.

A good way to structure is to understand that our unit of analysis is a regression. Regression is more or less decided by right hand side and left hand side. So, we need the subagent to provide us with 1) prepared dataset 2) right hand side 3) left hand side 4) published coefficients. Then the code, that we fixed in advance will run the regression and check the published coefficient against the result, reporting back, if the paper replicates or not. 

You will find that papers do not replicate for various reasons: the package doesn't contain required data, the version of the PDF we have is not the published version, the authors indeed made a mistake. But in most of the cases they do replicate well.

**What to do.** Check that the registered tables replicate:

```bash
pytest test_replications.py            # one test per published column
```

`prompts/replicate.md` asks an agent to add a paper: `replications/<wid>.py` with its data loader and `SPECS`.


## Stage 5: new analysis


## Take home lessons:
