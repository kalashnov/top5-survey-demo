"""Backend-neutral core of Stage 3: what the model sees, what it returns, what gets written.

The two Stage-3 classifiers differ only in which model they call, so that a
Qwen-vs-Claude comparison measures the models. This module owns everything
around the call; `backend/backend_ollama.py` and `backend/backend_claude.py`
own the calls.

    subset ─┐
            ├─> judge.load_body()  ─> body + provenance ─┐
    wid ────┘                                            │
                                                         ├─> Backend.judge_one()
    judge.SYSTEM_PROMPT + JSON_SCHEMA + render_prompt() ─┘        │
                                                                  v
                                                            JudgeResult
                                                                  │
                                            judge.envelope() <────┘
                                                     │
                                          judge.write_atomic()

What the model is asked lives here: SYSTEM_PROMPT (instructions plus the
few-shot block) and JSON_SCHEMA (output shape), both read at import from
`judging/prompts/`, their hashes, the body loader, the user-message template
and the atomic verdict writer. It imports no model client, so
`adhoc/benchmark_ollama.py` can reach the prompt without one.

A backend implements one method. It touches no disk, reads no subset, decides
no skip and builds no envelope.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

_SURVEY_ROOT = Path(__file__).resolve().parents[1]

# Every prompt input is tracked in git and read at import, so a fresh checkout
# reproduces the exact prompt and a missing file raises rather than quietly
# building an example-less one. JUDGE_PROMPTS names a sibling prompt dir
# (e.g. `prompts_rct`); it is read at import, so set it before launching.
PROMPTS = Path(__file__).resolve().parent / os.environ.get("JUDGE_PROMPTS", "prompts")
GROUNDTRUTH = PROMPTS / "groundtruth"

_SYSTEM_PROMPT_BASE = (PROMPTS / "system_prompt.md").read_text(encoding="utf-8")

JSON_SCHEMA = json.loads((PROMPTS / "json_schema.json").read_text(encoding="utf-8"))


def _build_few_shot_block() -> str:
    """Compose few-shot examples (paragraph + audited verdict JSON) from
    prompts/paragraphs.json + prompts/groundtruth/.
    The pair list is canonical on disk so prompts and ground-truth stay
    in sync. Both live under judging/prompts/ (tracked in git) rather than
    data/output/ (gitignored), so a fresh checkout reproduces the exact
    prompt; `run_llm_judgement.py --out-dir judging/prompts/groundtruth`
    regenerates them.
    Raises if either is missing — a silently example-less prompt is a
    much worse failure than a loud one."""
    fs_path = PROMPTS / "paragraphs.json"
    verdict_dir = GROUNDTRUTH
    if not fs_path.exists():
        raise FileNotFoundError(
            f"Few-shot inputs missing: expected {fs_path} and {verdict_dir}. "
            f"Regenerate the exemplar verdicts with "
            f"`python -m survey.judging.run_llm_judgement --backend claude --out-dir "
            f"survey/judging/prompts/groundtruth ...`."
        )
    paras = json.loads(fs_path.read_text())["papers"]
    if not paras:
        return ""
    parts: list[str] = [
        "",
        "",
        "## EXAMPLES",
        "",
        "The following 6 papers have been carefully audited. Each paragraph "
        "summarizes the paper's relevant methodology, including details that "
        "could mislead a careless reader (logs on the RHS, multi-arm RCT "
        "design, theoretical log-linearization, descriptive stratification). "
        "The JSON shows the correct classification. Study how each paragraph "
        "maps to the verdict.",
        "",
    ]
    # Projected onto the schema's fields in the schema's order, so an example
    # teaches the model the intended chain-of-thought sequence. Keys outside
    # the schema (the ground-truth files' audit keys) are dropped.
    schema_props = JSON_SCHEMA["properties"]["verdicts"]["items"]["properties"]
    schema_order = list(schema_props.keys())

    def _project(v_raw: dict) -> dict:
        return {k: v_raw[k] for k in schema_order if k in v_raw}

    for p in paras:
        vfile = verdict_dir / f"verdict_{p['wid']}.json"
        if not vfile.exists():
            raise FileNotFoundError(
                f"Few-shot paragraph {p['slot']} ({p['wid']}) has no verdict at "
                f"{vfile}. paragraphs.json and groundtruth/ must stay in sync."
            )
        v_raw = json.loads(vfile.read_text())["structured_output"]["verdicts"][0]
        v = _project(v_raw)
        parts.append(f"### Example {p['slot']} — {p['role']}")
        parts.append("")
        parts.append("Paper:")
        parts.append(p["paragraph"])
        parts.append("")
        parts.append("Correct verdict:")
        parts.append(json.dumps(v, indent=2, ensure_ascii=False))
        parts.append("")
    return "\n".join(parts)


# After JSON_SCHEMA is loaded: the few-shot block projects onto its properties.
SYSTEM_PROMPT = _SYSTEM_PROMPT_BASE + _build_few_shot_block()

# Stamped into every verdict envelope, so a verdict can be traced to the
# prompt and schema that produced it. `sort_keys` keeps the schema hash
# insensitive to dict ordering.
SYSTEM_PROMPT_SHA256 = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()
JSON_SCHEMA_SHA256 = hashlib.sha256(
    json.dumps(JSON_SCHEMA, sort_keys=True, ensure_ascii=False).encode("utf-8")
).hexdigest()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# Body loading + user-message rendering + atomic write
# ---------------------------------------------------------------------------

def write_atomic(path: Path, env: dict) -> None:
    """Write a verdict envelope so it is never observed half-written.

    Dump to ``{path}.tmp``, then ``rename()`` into place — an atomic operation
    on a POSIX filesystem, so ``verdict_{wid}.json`` either exists complete or
    does not exist at all. Never a truncated file.

    That matters because the classifiers **skip papers whose verdict already
    exists**. A half-written file killed mid-dump (Ctrl-C, OOM, the Claude quota
    exit, a reboot) would be skipped forever on every later run — a permanently
    broken paper, silently missing from the corpus. It also means a reader
    globbing the output dir (``summarize_verdicts.py``) can never catch a file
    mid-write, which is routine while ``sonnet_loop.sh`` is running.

    A kill mid-write leaves a stray ``.tmp``, which nothing reads and the next
    run overwrites.
    """
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(env, indent=2, ensure_ascii=False))
    tmp.rename(path)


def load_body(wid: str, pdftxt_dir: Path) -> tuple[str, dict] | None:
    """Read a paper's extracted text. Returns ``(body, provenance)``.

    The single body loader for every classifier. Returns ``None`` in two cases,
    and the caller then reports the paper as ``miss``:

      - no ``{wid}.txt`` in ``pdftxt_dir``, or
      - the file is empty or whitespace-only.

    ``miss`` is not sticky, so the paper is picked up once Stage 2 produces
    text. A near-empty body is not a miss: a tiny extract is what Stage 2's
    always-include-1 rule correctly returns for a theory paper.

    Nothing is truncated here. ``condense_topk --max-chars`` owns the excerpt
    budget, so pointing ``--pdftxt-dir`` at raw ``data/output/pdftxt/`` sends
    those files in full -- expensive on Claude, and silently cut by the server
    on Ollama past ``--num-ctx``.

    ``provenance`` records what the model was shown, so a verdict is auditable
    without storing the body:

      - ``source_path`` / ``source_chars`` / ``source_sha256`` -- the file on
        disk
      - ``body_chars`` / ``body_sha256`` -- what went into the prompt

    The hashes tell a later reader whether the ``.txt`` on disk is still the
    text the model saw.
    """
    p = pdftxt_dir / f"{wid}.txt"
    if not p.exists():
        return None
    body = p.read_text(errors="replace")
    if not body.strip():
        return None

    try:
        src_path_disp = str(p.relative_to(_SURVEY_ROOT.parent))
    except ValueError:
        src_path_disp = str(p)

    provenance = {
        "source_path":   src_path_disp,
        "source_chars":  len(body),
        "source_sha256": _sha256(body),
        "body_chars":    len(body),
        "body_sha256":   _sha256(body),
    }
    return body, provenance


# The subset file must carry these per record; a missing one renders empty.
HEADER_FIELDS = ("title", "authors", "journal_code", "publication_year")


def render_prompt(wid: str, meta: dict, body: str) -> str:
    """Render the user message: a metadata header, then the paper body.

    The single template for every classifier: both backends call this, so a
    disagreement between two models on one paper is a difference in the model.

    `meta` is the paper's own record from the `--subset` file (see
    `utils._load_subset_records`) — the census that defines a run also carries
    the header for it, so nothing is joined against `metadata.json` at judge time.

    The `Authors` line is emitted even when empty: "we have no author list" is
    itself informative to the classifier, and a blank line says so. Volume and
    issue are deliberately absent — they carry no signal about whether a paper
    logs its dependent variable.
    """
    title   = (meta.get("title") or "").strip()
    authors = (meta.get("authors") or "").strip()
    journal = (meta.get("journal_code") or "")
    year    = (meta.get("publication_year") or "")
    header = [
        f"## {wid}",
        f"- **Title**: {title}",
        f"- **Authors**: {authors}",
        f"- **Journal**: {journal} {year}".rstrip(),
        "- **Full extracted text (top-10K-token excerpt from condenser)**:",
    ]
    return (
        "\n".join(header) + "\n\n"
        f"--- BEGIN PAPER ---\n{body}\n--- END PAPER ---\n"
    )


# ---------------------------------------------------------------------------
# The backend contract
# ---------------------------------------------------------------------------

class FatalBackendError(RuntimeError):
    """The backend cannot make progress on ANY paper — stop the whole run.

    Distinct from an ordinary per-paper exception (which is counted as ``fail``
    and the loop moves on). Raised by ``ClaudeBackend`` when the subscription
    quota is exhausted: every subsequent call would fail too, so burning through
    the backlog on doomed calls is pure waste. Callers exit ``rc=2`` — which
    ``sonnet_loop.sh`` relies on, since it re-invokes the script every 5 minutes
    forever and would otherwise churn.
    """


@dataclass
class JudgeResult:
    """Everything one model call produced. The only thing a backend returns.

    ``user_msg`` is the *actual* rendered user turn the backend sent, not a
    reconstruction — ``envelope()`` hashes these bytes, so the recorded
    ``user_msg_sha256`` is a fingerprint of what the model really saw.

    ``usage`` is deliberately NOT normalized across backends. Ollama meters
    ``prompt_eval_count`` / ``eval_count`` / nanosecond durations; Claude meters
    ``input_tokens`` / ``cache_read_input_tokens`` / ``output_tokens``. Forcing
    one shape would mean inventing numbers that don't exist on the other side
    (Ollama has no cache-read; Claude has no prefill milliseconds). The envelope
    stores whichever dict the backend hands over, verbatim.

    ``extras`` are backend-specific top-level envelope keys — ``raw_response`` /
    ``first_chunk_s`` / ``thinking`` for Ollama, ``cost_estimate_usd`` /
    ``subtype`` for Claude. They may not collide with the core keys; ``envelope()``
    raises if they do.
    """
    verdicts: list[dict]
    usage: dict
    elapsed_s: float
    user_msg: str
    parse_ok: bool = True
    extras: dict[str, Any] = field(default_factory=dict)


class Backend(Protocol):
    """One method: judge one paper.

    ``log`` is supplied by the caller and is safe to call from worker threads
    (the run loop serializes it behind a lock), so a backend can stream progress
    without interleaving its output with another paper's.
    """
    source: str   # -> envelope["source"], e.g. "fulltext_ollama"
    model: str    # -> envelope["model"]

    def judge_one(self, wid: str, meta: dict, body: str, provenance: dict,
                  log: Callable[[str], None]) -> JudgeResult:
        ...


# Keys envelope() owns. A backend's `extras` may not overwrite these.
_CORE_KEYS = frozenset({
    "wid", "wids", "model", "source", "ts", "elapsed_s",
    "system_prompt_sha256", "json_schema_sha256",
    "input", "usage", "parse_ok", "structured_output",
})


def envelope(wid: str, meta: dict, provenance: dict,
             backend: Backend, result: JudgeResult) -> dict:
    """Build the verdict file's contents. The single writer of the envelope.

    Every verdict, from every backend, records the same core facts:

      - **identity**: ``wid`` (and legacy ``wids: [wid]``), ``model``, ``source``, ``ts``
      - **the exact input**: ``system_prompt_sha256`` + ``json_schema_sha256`` +
        ``input`` (body provenance from ``load_body()``, the header fields as sent,
        and ``user_msg_sha256`` over the whole rendered user turn). Together these
        pin down everything the model saw.
      - **the output**: ``structured_output.verdicts``, ``parse_ok``, ``usage``, ``elapsed_s``

    **We stamp the id here.** ``id`` is not in ``JSON_SCHEMA`` — the model is never
    asked for it and cannot get it wrong. This is the last stop before disk, so
    stamping here makes "every verdict file on disk carries the wid we asked
    about" an invariant no backend can bypass. The verdicts are copied rather
    than mutated, so the backend's own list is left as the model returned it.
    """
    verdicts = [{**v, "id": wid} for v in result.verdicts]

    input_block = dict(provenance)          # source_*, body_*, truncated
    input_block.update({
        "title":           meta.get("title"),
        "authors":         meta.get("authors"),
        "journal_code":    meta.get("journal_code"),
        "year":            meta.get("publication_year"),
        "user_msg_chars":  len(result.user_msg),
        "user_msg_sha256": _sha256(result.user_msg),
    })

    env = {
        "wid":                  wid,
        # Alias kept for analysis scripts that reach for the list form.
        "wids":                 [wid],
        "model":                backend.model,
        "source":               backend.source,
        "ts":                   _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "elapsed_s":            round(result.elapsed_s, 2),
        "system_prompt_sha256": SYSTEM_PROMPT_SHA256,
        "json_schema_sha256":   JSON_SCHEMA_SHA256,
        "input":                input_block,
        "usage":                result.usage,
        "parse_ok":             result.parse_ok,
        "structured_output":    {"verdicts": verdicts},
    }

    clash = _CORE_KEYS & set(result.extras)
    if clash:
        raise ValueError(
            f"{backend.source} backend tried to overwrite core envelope key(s) "
            f"via extras: {sorted(clash)}. Core keys are owned by envelope() so "
            f"every verdict records the same facts about how it was produced."
        )
    env.update(result.extras)
    return env
