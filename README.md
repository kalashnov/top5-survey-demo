# Top-5 survey demo

REFER TO PAUL GOLDSMITH, HULL, CR

This is a tutorial on a mass survey and replication of papers using an LLM. The tutorial teaches:

1. How to run/manage/schedule hundreds of subagents
    1. With API
    2. Simply in chat
2. How to save on costs
    1. With local models
    2. With tight prompts
    3. With context control
    4. With prompt caching
    5. With batch processing

In this toy example, we will:

1. **Survey.** Survey the methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`.
2. **Replicate.** Ask the agents to replicate the empirical papers in the sample in an organized way.
3. **Extend.** The next step is bounded only by imagination.

> [!NOTE]
> **ChatGPT and other providers.** The whole tutorial is written with Claude in mind, but a large part of it is not specific to Claude. Some of the steps can run with any agent; others may require rewriting some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough not to eat any sensible part of your quota on a 20 USD subscription.

## Navigating the tutorial

The tutorial is organized in sections. Each section has some writing explaining best practices. However, if you just want to skip it and execute the code, skip to the **What to do** paragraph. Also, if you are not interested in some stages, you may ask your agent to do that stage for you.


## Stages

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Classify.** Does the paper use a log-transformed outcome (Haiku)?
3. **Download replication data.** 6 of the 50 so far.
4. **Replicate the published regressions.** 5 of the 50 so far.

## Stage 1: Collect papers

*Concepts: subagents*

The first thing is to collect any public URLs for each paper. To save time, the repo already contains URLs for each paper, but generally a good approach is to ask your agent to write a script that systematically reviews the following sources:

1. OpenAlex
2. Semantic Scholar
3. NBER
4. arXiv

Here is a suggested prompt: [`prompts/collect_urls.md`](prompts/collect_urls.md).

The result will contain mistakes: some links will lead to other papers, and some will lead to supplementary material instead. Some papers will have no link, even though the paper is public on the author's website. A good approach is to run a number of **Haiku subagents** tasked each with a couple of papers to check for the mistakes and/or search the web for the correct versions. This is more expensive than scraping the APIs of the sources above with code, but also, we have already narrowed down the task before handing it to LLMs.

> [!NOTE]
> For this exercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here and will learn about subagents on a more exciting example.

**What to do.** To download the PDFs from my list, run (this will take a few minutes):

```bash
python fetch_pdfs.py
```

Then extract the plain text from the PDFs:

```bash
python extract_text.py
```


## Stage 2: Classifying the methodology of papers

*Concepts: subagents at scale, small models, prompt caching, structured output, batch processing*

Now we arrive at the fun part: running an army of subagents. The idea of this stage is as follows. Let the agents read the paper and answer a few questions: Do they run an experiment? Do they run difference-in-differences? What is the source of the data?

Our virtues and our vices:

- **Virtue:** We ask a set of simple questions about a given input. No exploration or problem solving is needed.
- **Vice:** We need to classify thousands of papers.
- **Vice:** We need structured output, so that it is ready to load into Stata and explore.

Therefore, we will heavily optimize the cost per paper. Here are a few important choices:

1. **Pre-screen with a local model.** We can run a local model to pre-screen paper texts and throw away anything not related to methodology. UCSD's Slurm cluster can run a local model large enough for this task. I do not cover this in detail, because it requires more involvement. Less input text means lower costs.
2. **A long prompt with examples.** We use a very verbose, clear prompt with a lot of examples, and we validate this prompt with a few experiments/iterations. The prompt for this task is in [`prompts/system_prompt.md`](prompts/system_prompt.md). A really good prompt lets us use smaller models.
3. **Prompt caching.** One may worry that a larger prompt means more input, and therefore higher costs. But the prompt doesn't change from request to request, and if everything is designed correctly, it is cached and billed at a 10% rate. The larger part of the input is the paper anyway.
4. **Structured output.** Finally, we use a feature called "structured output". It constrains the model to output valid JSON, which we can then use to construct our final dataset. The schema for this application is in [`prompts/json_schema.json`](prompts/json_schema.json).
5. **Batch processing.** The other way to save is batch processing, which we do not use here. Most providers let you submit a job as a "batch" instead of "on demand". They guarantee a response within 24 hours, but are not obliged to answer right away, and they give significant discounts. However, it also involves tradeoffs, e.g. it might be harder to manage the prompt cache (which expires). For Claude, it also doesn't work with a subscription. At my scale I found that a 100 USD subscription, though it adds some inconvenience, is the most cost-effective option, so I do not rely on batch processing.

**What to do.**

For this stage you need to make sure that you are authenticated in the Claude Code command line interface:

```bash
claude -p "Reply with OK"
```

> [!NOTE]
> **ChatGPT and other providers.** If you use ChatGPT, you will need to ask your agent to adapt the code to your provider.

To run the classification, just execute:

```bash
python classify.py          # writes verdicts/<wid>.json
```

This will output one JSON file per paper with the answers to the questions we asked.

## Stage 3: Download replication data

*Concepts: browser agents*

For downloading datasets we follow the same approach as for PDFs. We first need to collect a list of URLs (already collected for this example). Ask the agent to write code that systematically scrapes the following sources:

1. DataCite
2. Harvard Dataverse
3. Zenodo
4. ScholeXplorer (OpenAIRE)
5. Crossref
6. World Bank Microdata Library
7. Econometric Society
8. The paper's own text for direct links

Here is a suggested prompt: [`prompts/collect_data_urls.md`](prompts/collect_data_urls.md).

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

*Concepts: one subagent per paper, a fixed interface for agents' output, automated verification, orchestrating subagents from chat*

This is another stage where we will heavily use subagents. However, this time the task is not clear-cut, and we need the agents to explore and use whatever tools they need. Still, we need to add some structure to their search.

A good way to add structure is to recognize that our unit of analysis is a regression. A regression is more or less determined by its right-hand side and left-hand side. So we need the subagent to provide us with

1. a prepared dataset,
2. the right-hand side, the left-hand side and other details of the specification (e.g. the standard errors variant),
3. the published coefficients.

This is where we fix the `Spec` interface. It registers the model specification the agent wants to fit and its reference values. After that, the code that we fixed in advance runs the regression, checks the published coefficients against the result and reports back whether the paper replicates or not.

This way we

1. have a guardrail that the agent did indeed check the coefficients against the published ones,
2. have the replication results in a structured format as well (a set of `Spec`s), which can later be collected into a dataset of their own.

You will find that papers fail to replicate for various reasons: the package doesn't contain the required data, the version of the PDF we have is not the published version, or the authors indeed made a mistake. But in most cases they replicate well.

> [!NOTE]
> Why do we use *sub*agent, and why do we ask to process one paper at a time? For both quality and cost. We do not want each our main chat to carry context from processing of other papers, for two reasons: 1) longer contexts are expensive, and 2) longer contexts may deteriorate quality.


**What to do.**

The prompt for this stage is in [`prompts/replicate.md`](prompts/replicate.md). The prompt asks a subagent to take a specific paper and replicate tables from it. You can either write scheduling code in the spirit of Stage 2, or just ask in chat something like this:

```
Run 1 sonnet subagent for each paper with a dataset (2 in parallel),
prompt them with replicate.md and ask them to replicate the paper. Report back with the results.
```

The chat will spawn subagents and talk to them on your behalf.

The output of the agents should be data preparation scripts and registered regressions, which they either could or could not replicate.

Check that the registered tables replicate:

```bash
pytest test_replications.py            # one test per published column
```

## Stage 5: new analysis

*Concepts: extending a fixed interface, reusing shared code across papers*

Suppose, instead of just replicating the analysis of the authors we want to extend it. Here there are two useful approaches. 

First example will require decision for each seperate paper from scratch: Just as an example, we want them to systematically run interaction tables. Then, we can write `ISpec`, that will formalize interaction tables and write a prompt that will ask an agent to 

Then, we can register another version of `Spec`, e.g. `ISpec` (`I` for interaction) and ask the subagents to come up with sensible interaction regressions. Of course, we should also come up with some automated way to validate/aggregate the agent's output.

Another example, we can try to test, what if we replace all left hand sides with `exp` -- we can do it from the shared code we wrote in advance. There is no need to spawn a new subagent for each paper from scratch

## Take home lessons:

1. **Narrow the task with code first.** Scripts collect links, download files and extract text for free. LLMs only get what code cannot do, such as fixing wrong links.
2. **Use the smallest model that does the job.** Answering fixed questions about a paper is a job for Haiku, given a long, clear prompt with examples.
3. **Keep the prompt fixed.** A prompt that does not change is cached and billed at a fraction of the price; the paper is the bulk of the input.
4. **Ask for structured output.** A JSON schema turns the answers into a dataset instead of text to read.
5. **One subagent per paper.** A short context is cheaper and gives better answers.
6. **Fix the interface in advance for open-ended tasks.** The agents explore freely, but report through a `Spec`, and our own code checks the result. That is the guardrail, and the results come out structured.
7. **Expect mistakes at every automated step.** Some links lead to the wrong paper, and some papers do not replicate. Check a sample by hand before trusting the rest.

## More tips

Worktrees and Pull requests, questions document
...
