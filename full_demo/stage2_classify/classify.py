"""Stage 2: classify each paper in papers.json with Haiku; writes verdicts/<wid>.json."""
import asyncio
import json
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

MODEL = "claude-haiku-5-5"
WORKERS = 4  # papers in flight at once
PROMPTS = Path(__file__).parent
SCHEMA = json.loads((PROMPTS / "json_schema.json").read_text())

# No tools, settings or plugins: Claude Code's own context would otherwise ride along.
OPTIONS = ClaudeAgentOptions(
    model=MODEL,
    system_prompt=(PROMPTS / "system_prompt.md").read_text(),
    output_format={"type": "json_schema", "schema": SCHEMA},
    tools=[],
    allowed_tools=[],
    setting_sources=[],
    mcp_servers={},
    strict_mcp_config=True,
    skills=[],
    agents={},
    plugins=[],
)


async def classify(p: dict, slots: asyncio.Semaphore) -> None:
    wid = p["wid"]
    body = Path(f"txt/{wid}.txt").read_text(errors="replace")
    prompt = (f"## {wid}\n"
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
    verdict = r.structured_output
    if verdict is None:
        raise RuntimeError(f"{wid}: no verdict ({r.subtype})")

    record = {"wid": wid, "model": MODEL, "usage": r.usage, **verdict}
    out = Path(f"verdicts/{wid}.json")
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False))
    print(wid, [v["log_dv_likely"] for v in verdict["verdicts"]], flush=True)


async def main() -> None:
    papers = json.loads(Path("papers.json").read_text())
    slots = asyncio.Semaphore(WORKERS)
    await asyncio.gather(*(classify(p, slots) for p in papers))


Path("verdicts").mkdir(exist_ok=True)
asyncio.run(main())
