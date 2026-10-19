Write a Python script, collect_urls.py, that finds a public PDF link for every paper
in papers.json (fields: wid, doi, title, authors, journal_code, publication_year).

Sources, tried in this order until one gives a link that passes the checks below:
1. OpenAlex: the record for the paper's DOI (best_oa_location, then the other locations)
2. Semantic Scholar: lookup by DOI, then search by title
3. NBER: search by title for the working paper
4. arXiv: search by title

API keys:
- Read OPENALEX_API_KEY and SEMANTIC_SCHOLAR_API_KEY from the environment if they are set;
  work without them otherwise.
- Before you start, tell me that both keys are free and optional: without them the script
  still works, just slower (Semantic Scholar allows about 1 request per second), and they
  help at the scale of thousands of papers. I can get them later and rerun.

Rules:
- Never request a publisher's site (aeaweb.org, academic.oup.com, journals.uchicago.edu,
  econometricsociety.org, wiley.com).
- Identify the script with a plain User-Agent; do not send any email address.
- Respect rate limits: Semantic Scholar allows 1 request per second without a key,
  arXiv asks for about 3 seconds between requests.
- A title search only counts as a match if the title is nearly the same and at least
  one author's surname matches.

Check every candidate link before accepting it:
- Download it; it must start with %PDF and be over 10 KB (not an HTML landing page).
- Extract the first page's text; the paper's title must appear in it. This catches links
  that lead to a different paper.

Output:
- Add a pdf_url field to each paper in papers.json; null if nothing passed.
- Write url_log.jsonl: one line per paper, with every source and URL tried and why it
  was rejected.
- Print a summary: found / not found, by source and by journal.

Make it safe to rerun: skip papers that already have a pdf_url.
Test it on 5 papers first and show me the log before running all of them.
