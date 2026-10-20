# Demo: survey and replication of papers in Economics

This is a tutorial on a mass survey and replication of papers using an LLM. It shows how to:

| | |
|---|---|
| **Run, manage and schedule dozens of subagents** | with the API · simply in chat |
| **Save on costs** | local models · tight prompts · context control · prompt caching · batch processing |

In this toy example, we will:

1. **Survey.** Survey the methodology of 50 papers from AER, QJE, JPE, ECMA and REStud, 2021–2025, listed in `papers.json`.
2. **Replicate.** Ask the agents to replicate the empirical papers in the sample in an organized way.
3. **Extend.** The next step is bounded only by imagination.

> [!NOTE]
> **ChatGPT and other providers.** The whole tutorial is written with Claude in mind, but a large part of it is not specific to Claude. Some of the steps can run with any agent; others may require rewriting some of the repo's code, which shouldn't be a big pain. Ask your agent for help here!

The repo is small enough not to eat any sensible part of your quota on a 20 USD subscription.

## Setup

### Install Claude app and get a subscription

Everything below runs through an agent, so you need one first. I personally prefer running Claude in VSCode extension, others prefer Claude Code command line interface, but for a newcomer I suggest to use an app:

1. **Get a subscription.** Sign up at [claude.ai](https://claude.ai) and pick a plan on the [pricing page](https://claude.com/pricing). **Pro** (20 USD a month) is enough for this tutorial
2. **Install the Claude app.** Download the desktop app from [claude.ai/download](https://claude.ai/download) (macOS and Windows) and sign in. Its **Code** tab runs Claude Code on a folder on your computer: open this repository there and chat with the agent.

Both, Gemini and ChatGPT have their respective analog of app/extension/cli. Any of these will do the job as well

### Python environment

> [!TIP]
> Just ask your agent to do it: "Set up a Python environment for this repo and install requirements.txt."


Create a Python environment (Python 3.11 or newer) and install the requirements, from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

All commands below assume the environment is active and you are in the repository root.

## Stages

The tutorial is organized in stages. If you want to skip the explanations and just execute the code, go to the **What to do** paragraph. Also, if you are not interested in some stages, you may ask your agent to do that stage for you.

1. **Collect papers.** List the journals' articles, draw the sample, download the PDFs, extract the text.
2. **Classify.** Ask each paper a fixed set of questions about its methodology, collect the answers as structured data.
3. **Download replication data.** Find each paper's replication package, download it, add it to the project.
4. **Replicate the published regressions.** Prepare the data, register each published regression, check it against the paper.

## Stage 1: Collect papers

*Covers: code extraction first, then subagents*

The first thing is to collect any public URLs for each paper. To save time, the repo already contains URLs for each paper, but generally a good approach is to ask your agent to write a script that systematically reviews the following sources:

1. OpenAlex
2. Semantic Scholar
3. NBER
4. arXiv

Here is a suggested prompt: [`stage1_collect_papers/collect_urls.md`](stage1_collect_papers/collect_urls.md).

The result will contain mistakes: some links will lead to other papers, and some will lead to supplementary material instead. Some papers will have no link, even though the paper is public on the author's website. A good approach is to run a number of **Haiku subagents** each tasked with a couple of papers to check for the mistakes and/or search the web for the correct versions. This is more expensive than scraping the APIs of the sources above with code, but by then we have already narrowed down the task before handing it to LLMs.

> [!NOTE]
> For this exercise I made sure none of the papers in this sample link to a wrong PDF, so we skip the data cleaning part here and will learn about subagents on a more exciting example.

**What to do.** To download the PDFs from my list, run (this will take a few minutes):

```bash
python stage1_collect_papers/fetch_pdfs.py
```

Then extract the plain text from the PDFs:

```bash
python stage1_collect_papers/extract_text.py
```


## Stage 2: Classifying the methodology of papers

*Covers: subagents at scale, verbose prompts, few-shot examples, prompt caching, structured output, batch processing*

Now we arrive at the fun part: running an army of subagents. The idea of this stage is as follows. Let the agents read the paper and answer a few questions: Do they run an experiment? Do they run difference-in-differences? What is the source of the data?

Our virtues and our vices:

- **Virtue:** We ask a set of simple questions about a given input. No exploration or problem solving is needed.
- **Vice:** We need to classify thousands of papers.
- **Vice:** We need structured output, so that it is ready to load into Stata and explore.

Therefore, we will heavily optimize the cost per paper. Here are a few ways to do it:

1. **Pre-screen with a local model.** We can run a local model to pre-screen paper texts and throw away anything not related to methodology. UCSD's Slurm cluster can run a local model large enough for this task. I do not cover this in detail, because it requires more involvement. Less input text means lower costs.
2. **A long prompt with examples.** We use a very verbose, clear prompt with a bunch of examples, and we validate this prompt with a few experiments/iterations. The prompt for this task is in [`stage2_classify/system_prompt.md`](stage2_classify/system_prompt.md). A really good prompt lets us use smaller models.
3. **Prompt caching.** One may worry that a larger prompt means more input, and therefore higher costs. But the prompt doesn't change from request to request, and if everything is designed correctly, it is cached and billed at a 10% rate. The larger part of the input is the paper anyway.
4. **Structured output.** Finally, we use a feature called "structured output". It constrains the model to output valid JSON, which we can then use to construct our final dataset. The schema for this application is in [`stage2_classify/json_schema.json`](stage2_classify/json_schema.json).
5. **Batch processing.** The other way to save is batch processing, which we do not use here. Most providers let you submit a job as a "batch" instead of "on demand". They guarantee a response within 24 hours, but are not obliged to answer right away, and they give significant discounts. However, it also involves tradeoffs, e.g. it might be harder to manage the prompt cache (which expires). For Claude, it also doesn't work with a subscription. At my scale I found that a 100 USD subscription, though it adds some inconvenience, is the most cost-effective option, so I do not rely on batch processing.

**What to do.**

For this stage you need to make sure that you are authenticated in the Claude Code command line interface:

```bash
claude -p "Reply with OK"
```

> [!NOTE]
> **ChatGPT and other providers.** If you use ChatGPT, you will need to ask your agent to adapt the code to your provider.

To run the classification, just execute (this already implements all of the recommendations above):

```bash
python stage2_classify/classify.py          # writes verdicts/<wid>.json
```

This will output one JSON file per paper with the answers to the questions we asked.

## Stage 3: Download replication data

*Covers: browser agents*

For downloading datasets we follow the same approach as for PDFs. We first need to collect a list of URLs (already collected for this example). Ask the agent to write code that systematically scrapes the following sources:

1. DataCite
2. Harvard Dataverse
3. Zenodo
4. ScholeXplorer (OpenAIRE)
5. Crossref
6. World Bank Microdata Library
7. Econometric Society
8. The paper's own text for direct links

Here is a suggested prompt: [`stage3_replication_data/collect_data_urls.md`](stage3_replication_data/collect_data_urls.md).

Once you have the links, downloading is more of a problem than for PDFs, because it usually requires you to consent to something and/or leave your contact details. Some repositories (e.g. Harvard Dataverse and Zenodo) have an API. You can ask your agent to figure out the API and run code to download the datasets. Either way, you need to babysit it.

For some repositories, downloading cannot be efficiently automated. Here are the options:

1. **Open the links, download by hand.** Ask [Claude in Chrome](https://claude.com/claude-in-chrome) to open each of the links in a new tab, and go over them manually.
2. **Let Claude download.** Ask Claude in Chrome to download them itself: this spends a lot of tokens, is very slow and quite unreliable, but might save your own time.

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

*Covers: context management, orchestrating subagents from chat, testing*

We will once again use subagents heavily. However, this time the task requires the agents to explore and use whatever tools they need. Still, we need to **add some structure to their search**.

A good way to add structure is to recognize that our unit of analysis is a regression. A regression is more or less determined by its right-hand side and left-hand side. So we need the subagent to provide us with

1. a prepared dataset,
2. the right-hand side, the left-hand side and other details of the specification (e.g. the standard errors variant),
3. the published coefficients.

This is where we fix the [`Spec` interface](stage4_replicate/replications/spec.py). It is a format in which the agent registers the specification it wants to fit and its reference values. After that, the code that we fixed in advance runs the regression, checks the published coefficients against the result and reports back whether the paper replicates or not.

This way we

1. have a guardrail that the agent did indeed check the coefficients against the published ones,
2. have the replication results in a structured format as well (a set of `Spec`s), which can later be collected into a dataset of their own.

You will find that papers fail to replicate for various reasons: the package doesn't contain the required data, the version of the PDF we have is not the published version, or the authors indeed made a mistake. But in most cases they replicate well.

> [!NOTE]
> Why do we use a *sub*agent, and why do we ask it to process one paper at a time? For both quality and cost. We do not want our main chat to carry context from processing other papers, for two reasons: 1) longer contexts are expensive, and 2) longer contexts may deteriorate quality.


**What to do.**

The prompt for this stage is in [`stage4_replicate/replicate.md`](stage4_replicate/replicate.md). The prompt asks a subagent to take a specific paper and replicate tables from it. You can either write scheduling code in the spirit of Stage 2, or just ask in chat something like this:

```
Run 1 sonnet subagent for each paper with a dataset (2 in parallel),
prompt them with replicate.md and ask them to replicate the paper. Report back with the results.
```

The chat will spawn subagents and talk to them on your behalf.

The output of the agents should be data preparation scripts and registered regressions, which they either could or could not replicate.

Check that the registered tables replicate:

```bash
pytest stage4_replicate            # one test per published column
```

To get all registered specs as one dataset, with the published and replicated coefficients side by side, run:

```bash
python stage4_replicate/collect_specs.py   # writes specs.csv: one row per published number
```

## Stage 5: new analysis

Suppose that, instead of just replicating the authors' analysis, we want to extend it. There are two useful approaches. 

The first example requires a decision for each separate paper from scratch. Say we want the agents to systematically run interaction tables. Then we can write `ISpec`, which will formalize interaction tables, and write a prompt that will ask an agent to 

Then, we can register another version of `Spec`, e.g. `ISpec` (`I` for interaction) and ask the subagents to come up with sensible interaction regressions. Of course, we should also come up with some automated way to validate/aggregate the agents' output.

In another example, we can test what happens if we replace all left-hand sides with `exp`: we can do it with the shared code we wrote in advance. There is no need to spawn a new subagent for each paper from scratch.

## Take-home lessons

1. **Narrow the task with code first.** Scripts collect links, download files and extract text for free. LLMs only get what code cannot do, such as fixing wrong links.
2. **Keep the prompt fixed.** A prompt that does not change is cached and billed at a fraction of the price; the paper is the bulk of the input. Anything that changes from agent to agent should go after the initial prompt.
3. **Fix the output format by any means.** It can be strictly enforced structured output, or it can be the same testing procedure on the agent's output.
4. **One subagent per paper for a long task.** A short context is cheaper and gives better answers.

## More tips

- **Worktrees.** When you start a chat (or a subagent), ask it to `work in a worktree`. This gives the agent its own folder, where it can do whatever it wants.
- **Pull requests.** Having dozens of subagents, each working on its own paper, makes it hard to review their results in detail. Ask them to submit a pull request to the GitHub repo after they are done in their worktree. This way you can see what they have done before it reaches the main project folder. Generally, using git is a requirement here, to always be able to roll back their changes.
- **Questions document.** Subagents may want you to make some decisions they hesitate to make on their own. Make a document and ask them to collect their questions in it. You can answer in the document and then just instruct them to read the answer from there. There are numerous ways to improve this: require a certain structure for the document, provide tags to filter/classify questions, and even have small subagents you can ask follow-up questions about the decisions to make.

## Related work

- The idea of Specs is taken from a [replication package](https://github.com/jiafengkevinchen/logs-public) for **Chen and Roth (2024), "Logs with Zeros? Some Problems and Solutions", QJE.** 
- **Peter Hull** also undertakes a large replication effort in the context of two-way fixed effects. The writeup is ["Two-Way Fixed Effects and Modern Difference-in-Differences: An Empirical Comparison"](https://www.dropbox.com/scl/fi/ago5vsi89l2ns388rwhgz/did_reanalysis.pdf?rlkey=zxv893g3j5j8dpqkwxsy48o6q), and the repository [peterdhull/twfe-replication](https://github.com/peterdhull/twfe-replication) reproduces its figures.
- Some PDF collection ideas are taken from **Paul Goldsmith-Pinkham** who built [Economics Literature Search](https://paulgp.com/econlit-pipeline/), a full-text search for 15,000 papers (code: [paulgp/econlit-pipeline](https://github.com/paulgp/econlit-pipeline)). Some results can be explored on the [dashboard](https://paulgp.com/econlit-pipeline/dashboard.html). This repo suggests another step: indexing the corpus by classifying methods with LLMs rather than just text search.
