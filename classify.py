"""Stage 3: classify each paper in papers.json with Haiku; writes verdicts/<wid>.json.

Usage: python classify.py [N]   (N = stop after N papers; finished papers are skipped)
"""
import asyncio
import json
import sys
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

MODEL = "claude-haiku-5-5"
WORKERS = 4  # papers in flight at once
PROMPTS = Path("prompts")
SCHEMA = json.loads((PROMPTS / "json_schema.json").read_text())

# No tools, settings or plugins: Claude Code's own context would otherwise ride along.
OPTIONS = ClaudeAgentOptions(
    model=MODEL, system_prompt=(PROMPTS / "system_prompt.md").read_text(),
    tools=[], allowed_tools=[], setting_sources=[], mcp_servers={}, strict_mcp_config=True,
    skills=[], agents={}, plugins=[],
    output_format={"type": "json_schema", "schema": SCHEMA},
)


async def classify(p: dict, slots: asyncio.Semaphore) -> None:
    body = Path(f"txt/{p['wid']}.txt").read_text(errors="replace")
    prompt = (f"## {p['wid']}\n"
              f"- **Title**: {p['title'].strip()}\n"
              f"- **Authors**: {p['authors'].strip()}\n"
              f"- **Journal**: {p['journal_code']} {p['publication_year']}\n"
              "- **Full extracted text (top-10K-token excerpt from condenser)**:\n\n"
              f"--- BEGIN PAPER ---\n{body}\n--- END PAPER ---\n")
    async with slots:
        # Drain the stream: returning mid-iteration leaves the SDK's generator open.
        async for m in query(prompt=prompt, options=OPTIONS):
            if isinstance(m, ResultMessage):
                r = m
    if r.structured_output is None:
        raise RuntimeError(f"{p['wid']}: no verdict ({r.subtype})")
    Path(f"verdicts/{p['wid']}.json").write_text(json.dumps(
        {"wid": p["wid"], "model": MODEL, "usage": r.usage, **r.structured_output}, indent=1, ensure_ascii=False))
    print(p["wid"], [v["log_dv_likely"] for v in r.structured_output["verdicts"]], flush=True)


async def main() -> None:
    todo = [p for p in json.loads(Path("papers.json").read_text())
            if not Path(f"verdicts/{p['wid']}.json").exists() and Path(f"txt/{p['wid']}.txt").exists()]
    if len(sys.argv) > 1:
        todo = todo[:int(sys.argv[1])]
    slots = asyncio.Semaphore(WORKERS)
    await asyncio.gather(*(classify(p, slots) for p in todo))


Path("verdicts").mkdir(exist_ok=True)
asyncio.run(main())
