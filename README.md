# Top-5 survey demo

REFER TO PAUL GOLDSMITH, HULL, CR

This is a tutorial on a mass survey and replication of papers using an LLM. The tutorial teaches:

1. How to run/manage/schedule hundreds of subagents
    1.   With API
    2.   Simply in chat
2. How to save on costs
    1. With local models
    2. With ...
3. How to write prompts

In this toy example, we will:
1. **Survey.** Survey the methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`.
2. **Replicate.** Ask the agents to replicate the empirical papers in the sample in an organized way.
3. **Extend.** The next step is bounded only by imagination.

The whole tutorial is written with Claude in mind, but a large part of it is not specific to Claude. Some of the steps can run with any agent; others may require rewriting some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough not to eat any sensible part of your quota on a 20 USD subscription.

## Navigating the tutorial

The tutorial is organized in sections. Each section has some writing explaining best practices. However, if you just want to skip it and execute the code, skip to the **What to do** paragraph. Also, if you are not interested in some stages, you may ask your agent to do that stage for you.


## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
3. **Download replication data.** 6 of the 50 so far.
4. **Replicate the published regressions.** 5 of the 50 so far.

## Stage 1: Collect papers

The first thing is to collect any public URLs for each paper. To save time, the repo already contains URLs for each paper, but generally a good approach is to ask your agent to write a script that systematically reviews the following sources:

1. OpenAlex
2. Semantic Scholar
3. NBER
4. arXiv

The result will contain mistakes: some links will lead to other papers, and some will lead to supplementary material instead. Some papers will have no link, even though the paper is public on the author's website. A good approach is to run a number of Haiku subagents tasked with correcting the mistakes and searching the web for the correct versions. This is more expensive than searching the APIs of the sources above with code, but by then we have already narrowed down the task before handing it to LLMs. For this exercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here and will learn about subagents on a more exciting example.

**What to do.** To download the PDFs from my list, run (this will take a few minutes):

```bash
python fetch_pdfs.py
```

Then extract the plain text from the PDFs:

```bash
python extract_text.py
```


## Stage 2: Classifying the methodology of papers

Now we arrive at the fun part: running an army of subagents. The idea of this stage is as follows. Let the agents read the paper and answer a few questions: Do they run an experiment? Do they run difference-in-differences? What is the source of the data?

Our virtues and our vices:

Virtue: We ask a set of simple questions about a given input. No exploration or problem solving is needed.
Vice: We need to classify thousands of papers.
Vice: We need structured output, so that it is ready to load into Stata and explore.

Therefore, we will heavily optimize the cost per paper. Here are a few important choices:

1. **Pre-screen with a local model.** We can run a local model to pre-screen paper texts and throw away anything not related to methodology. UCSD's Slurm cluster can run a local model large enough for this task. I do not cover this in detail, because it requires more involvement. Less input text means lower costs.
2. **A long prompt with examples.** We use a very verbose, clear prompt with a lot of examples, and we validate this prompt with a few experiments/iterations. The prompt for this task is in [`prompts/system_prompt.md`](prompts/system_prompt.md). A really good prompt lets us use smaller models.
3. **Prompt caching.** One may worry that a larger prompt means more input, and therefore higher costs. But the prompt doesn't change from request to request, and if everything is designed correctly, it is cached and billed at a 10% rate. The larger part of the input is the paper anyway.
4. **Structured output.** Finally, we use a feature called "structured output". It constrains the model to output valid JSON, which we can then use to construct our final dataset. The schema for this application is in [`prompts/json_schema.json`](prompts/json_schema.json).

**What to do.** 

For this stage you need to make sure that you are authenitificated in Claude Code command line interface:

```claude -p "Reply with OK"```

If you use ChatGPT, you will need to ask your agent to adapt the code to your provider

To run the classification, just execute:

```bash
python classify.py          # writes verdicts/<wid>.json
```

This will output one JSON file per paper with the answers to the questions we asked.

## Stage 3: Download replication data

For downloading datasets we follow the same approach as for PDFs. We first need to collect a list of URLs (already collected for this example). Ask the agent to write code that systematically searches the following sources:

1. DataCite
2. Harvard Dataverse
3. Zenodo
4. ScholeXplorer (OpenAIRE)
5. Crossref
6. World Bank Microdata Library
7. Econometric Society
8. The paper's own text for direct links

Once you have the links, downloading is more of a problem than for PDFs, because it usually requires you to consent to something and/or leave your contact details. Some repositories (e.g. Harvard Dataverse and Zenodo) have an API. You can ask your agent to figure out the API and run code to download the datasets. Either way, you need to babysit it.

For some repositories, downloading cannot be efficiently automated. Here are the options:

1. **Open the links, download by hand.** Ask Claude for Chrome to open each of the links in a new tab, and go over them manually.
2. **Let Claude download.** Ask Claude for Chrome to download them itself: this spends a lot of tokens, is very slow and quite unreliable, but might save your own time.

Sometimes a package doesn't contain the data itself, but provides instructions on how to fetch the data from another source. Agents are quite good at this most of the time; just ask them to follow the authors' instructions.

**What to do.** For this tutorial I suggest manually downloading a few replication packages, e.g. these. After they are downloaded, just ask Claude to go into your downloads folder and copy them into the project.

| Paper | Size | Repository | Package |
|---|---|---|---|
| W4401126511, AER 2024 | 4 MB | openICPSR | https://doi.org/10.3886/E197302V1 |
| W4405354213, REStud 2024 | 16 MB | Zenodo | https://doi.org/10.5281/zenodo.10783446 |
| W4387449673, JPE 2023 | 20 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/NYSNOT |
| W3174918233, AER 2021 | 33 MB | openICPSR | https://doi.org/10.3886/E121941V1 |
| W4407240810, QJE 2025 | 214 MB | Harvard Dataverse | https://doi.org/10.7910/DVN/PDFDKR |
| W3186531035, AER 2024 | 1.2 GB | openICPSR | https://doi.org/10.3886/E198004V1 |

## Stage 4: Replication

This is another stage where we will heavily use subagents. However, this time the task is not clear-cut, and we need the agents to explore and use whatever tools they need. Still, we need to add structure to their search.

A good way to add structure is to recognize that our unit of analysis is a regression. A regression is more or less determined by its right-hand side and left-hand side. So we need the subagent to provide us with 1) a prepared dataset, 2) the right-hand side, 3) the left-hand side and 4) the published coefficients. Then code that we fixed in advance runs the regression, checks the published coefficients against the result and reports back whether the paper replicates or not.

You will find that papers fail to replicate for various reasons: the package doesn't contain the required data, the version of the PDF we have is not the published version, or the authors indeed made a mistake. But in most cases they replicate well.


**What to do.**

The prompt for this stage is in [`prompts/replicate.md`](prompts/replicate.md). You can either write scheduling code in the spirit of Stage 2, or just ask in chat something like this:

```
Run 1 subagent for each paper with a dataset (2 in parallel),
prompt them with replicate.md and ask them to replicate the paper. Report back with the results.
```

The output of the agents should be data preparation scripts and registered regressions, which they either could or could not replicate.

Check that the registered tables replicate:

```bash
pytest test_replications.py            # one test per published column
```

## Stage 5: new analysis

Registering own spec...


## Take home lessons:


## More tips

Worktrees and Pull requests
...
