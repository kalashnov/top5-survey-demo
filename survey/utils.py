"""Small helpers shared by stages that have nothing else in common.

What is left here is only what **more than one stage** needs and no single stage
owns. It has **no heavy dependencies** (no Claude SDK, no Ollama), so any stage
can import it:

  - `_short` — last segment of an OpenAlex id, used everywhere ids are handled
  - the wid blacklist (`BLACKLIST_PATH`, `_load_blacklist`) — Stage 1
    (`chunking/condense_paper.py`), Stage 2 (`chunking/condense_topk.py`) and Stage 3
    (`judging/run_llm_judgement.py`) all subtract it
  - the subset loaders (`_load_subset_records`, `_load_subset`) — the one parser
    for a sample .json, whatever shape it is on disk

Everything the classifier needs and nobody else does — the system prompt, the
output schema, their hashes, the body loader, the user-message template, the
atomic verdict writer, the Claude cost table — lives in `judging/` (mostly in
`judging/judge.py`). The prompt assets themselves are `judging/prompts/`.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUTPUT = DATA / "output"
# Prompt inputs (system prompt, schema, few-shot examples, blacklist). They are
# Stage-3's, so they live next to it — only the blacklist is read from outside.
PROMPTS = ROOT / "judging" / "prompts"


def _short(s: str) -> str:
    """Last path segment of an OpenAlex id/URL (…/W123 → W123)."""
    return (s or "").rsplit("/", 1)[-1]


# OpenAlex `type` values that count as a paper in the census. `preprint` and
# `report` are in here because OpenAlex assigns them whenever the OA copy it
# indexed is a working-paper version — 95 of the 99 so-typed records in
# top5_since_2020 still carry a journal DOI, volume and page range. Excluded:
# paratext, erratum, editorial.
PAPER_TYPES = frozenset({"article", "preprint", "report"})


def is_paper(rec: dict) -> bool:
    """True if a census record is a paper the pipeline should process."""
    return rec.get("type") in PAPER_TYPES


# Wids dropped from every stage (issue front matter, wrong-PDF stubs). The
# sample source is per-stage; this exclusion list is fixed by design.
BLACKLIST_PATH = PROMPTS / "blacklist_wids.json"


def _load_blacklist(path: Path = BLACKLIST_PATH) -> set[str]:
    """Load the hardcoded wid blacklist. Missing file → empty set (no-op).

    Accepts a ``{"wids": [...]}`` object (the shipped shape) or a bare list.
    """
    if not path.exists():
        return set()
    raw = json.loads(path.read_text())
    wids = raw.get("wids", []) if isinstance(raw, dict) else raw
    return {_short(str(w)) for w in wids if w}


def _load_subset_records(path: Path) -> dict[str, dict]:
    """Resolve a sample .json to an ordered ``{wid: record}`` map.

    The subset file is the single source of BOTH the wid list and the
    per-paper header fields (title / authors / journal_code /
    publication_year / abstract) that the classifiers prepend to the prompt —
    so the census that defines the run also carries the metadata for it, and
    nothing has to be joined against ``data/output/metadata.json`` at judge
    time.

    Accepts three shapes:
      * a census file — a list of records each carrying ``openalex_id``
        (e.g. ``data/sample/top5_since_2020.json``) or ``wid``
        (``metadata.json``); the record *is* the header source;
      * a plain list of wid strings — records come back empty, so prompt
        headers degrade to the bare wid;
      * a dict with a ``"papers"`` list of ``{"wid": ..., ...}`` entries
        (the stratified-sample and few-shot files); any extra keys on those
        entries are kept and used as header fields.

    Duplicate wids keep their first record. Callers subtract
    ``_load_blacklist()`` from the result.

    Stays here rather than in ``judging/`` because ``_load_subset`` (below) is
    the same parser without the headers, and Stage 1 needs it.
    """
    raw = json.loads(path.read_text())
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and isinstance(raw.get("papers"), list):
        items = raw["papers"]
    else:
        raise ValueError(f"Unrecognized subset shape: {path}")

    out: dict[str, dict] = {}
    for x in items:
        if isinstance(x, str):
            wid, rec = _short(x), {}
        elif isinstance(x, dict):
            # census record (openalex_id URL) or metadata record (bare wid)
            wid, rec = (x.get("wid") or _short(x.get("openalex_id", ""))), x
        else:
            continue
        if wid:
            out.setdefault(wid, rec)
    return out


def _load_subset(path: Path) -> list[str]:
    """Ordered wid list from a sample .json. Wrapper over
    ``_load_subset_records`` for stages that need no header fields."""
    return list(_load_subset_records(path))
