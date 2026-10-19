"""Stage-3 backend: Claude via the Claude Agent SDK.

Owns exactly one thing — the ``query()`` call, its cost accounting, and the
quota-exhaustion detection that must halt a whole run. Everything else (which
papers, what prompt, what to record, how to write it) belongs to
``judging/judge.py``, shared with ``backend_ollama.py``.

The token/USD accounting below is Claude's alone: Ollama runs on a local GPU and
costs nothing, and its usage counters are a different shape entirely (see
``JudgeResult.usage``), so there is nothing to share.

Used for the 6 audited few-shot exemplars (Opus) and for the full-corpus pass
(Sonnet, driven by ``sonnet_loop.sh``).
"""
from __future__ import annotations

import asyncio
import time
from typing import Callable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    ThinkingBlock,
    query,
)

from survey.judging.judge import (
    JSON_SCHEMA,
    SYSTEM_PROMPT,
    FatalBackendError,
    JudgeResult,
    render_prompt,
)

# Rate card per million tokens — used to estimate "what this would have cost
# on the pay-as-you-go API." Subscription billing doesn't expose USD.
PRICES_PER_M = {
    "claude-sonnet-5":            {"in": 2.0,  "cache_r": 0.20, "cache_w_5m":  2.50, "cache_w_1h":  4.0, "out": 10.0},
    "claude-sonnet-4-6":          {"in": 3.0,  "cache_r": 0.30, "cache_w_5m":  3.75, "cache_w_1h":  6.0, "out": 15.0},
    "claude-haiku-4-5-20251001":  {"in": 1.0,  "cache_r": 0.10, "cache_w_5m":  1.25, "cache_w_1h":  2.0, "out":  5.0},
    "claude-opus-4-7":            {"in": 15.0, "cache_r": 1.50, "cache_w_5m": 18.75, "cache_w_1h": 30.0, "out": 75.0},
}


def _usage_dict(usage_obj) -> dict:
    """Normalize an SDK usage object (or dict) to a plain token-count dict."""
    if usage_obj is None:
        return {}
    if isinstance(usage_obj, dict):
        return {
            "input_tokens":                usage_obj.get("input_tokens", 0) or 0,
            "cache_read_input_tokens":     usage_obj.get("cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": usage_obj.get("cache_creation_input_tokens", 0) or 0,
            "output_tokens":               usage_obj.get("output_tokens", 0) or 0,
        }
    return {
        "input_tokens":                getattr(usage_obj, "input_tokens", 0) or 0,
        "cache_read_input_tokens":     getattr(usage_obj, "cache_read_input_tokens", 0) or 0,
        "cache_creation_input_tokens": getattr(usage_obj, "cache_creation_input_tokens", 0) or 0,
        "output_tokens":               getattr(usage_obj, "output_tokens", 0) or 0,
    }


def _cost_for_usage(usage: dict, model: str) -> float | None:
    """Estimate USD cost using the 5-minute cache write rate (our default TTL)."""
    p = PRICES_PER_M.get(model)
    if not p:
        return None
    return (
        (usage.get("input_tokens", 0) or 0)                  * p["in"]
        + (usage.get("cache_read_input_tokens", 0) or 0)     * p["cache_r"]
        + (usage.get("cache_creation_input_tokens", 0) or 0) * p["cache_w_5m"]
        + (usage.get("output_tokens", 0) or 0)               * p["out"]
    ) / 1_000_000


class ClaudeBackend:
    """Judge one paper with a Claude model, under the same schema constraint.

    The SDK is async and the run loop is sync, so ``judge_one`` drives its own
    event loop per paper. That is behaviour-identical to the old single
    ``asyncio.run()`` spanning the whole loop: each ``query()`` was independent and
    awaited to completion before the next began.

    Sequential by default (``--workers 1``). API rate limits, not GPU slots, are
    the constraint here.
    """

    source = "claude_groundtruth_top10k"

    def __init__(self, model: str):
        self.model = model

    def judge_one(self, wid: str, meta: dict, body: str, provenance: dict,
                  log: Callable[[str], None] = print) -> JudgeResult:
        try:
            return asyncio.run(self._judge(wid, meta, body))
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            # The SDK stringifies a quota-exhausted result as "Claude Code
            # returned an error result: success" — an error whose subtype is
            # literally "success". Every later paper fails the same way until
            # the rolling window resets, so it stops the run.
            if ("returned an error result" in msg
                    or "rate_limit" in msg.lower()
                    or "quota" in msg.lower()):
                raise FatalBackendError(
                    f"Claude API quota / rate-limit exhaustion on {wid} "
                    f"({type(e).__name__}: {msg[:200]}). Wait for the rolling "
                    f"window to reset (~5h) before restarting."
                ) from e
            raise

    async def _judge(self, wid: str, meta: dict, body: str) -> JudgeResult:
        user_msg = render_prompt(wid, meta, body)
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=SYSTEM_PROMPT,
            # An empty environment: anything the SDK injects from the machine
            # would be an input the envelope's hashes do not record.
            allowed_tools=[],
            # Without this, Claude Code's built-in tool definitions ride along on
            # every call (~22k input tokens) though the model never needs them.
            tools=[],
            setting_sources=[],
            mcp_servers={},
            strict_mcp_config=True,
            skills=[],
            agents={},
            plugins=[],
            output_format={"type": "json_schema", "schema": JSON_SCHEMA},
        )

        usage: dict = {}
        structured = None
        subtype = None
        thinking_blocks: list[str] = []

        t0 = time.time()
        async for message in query(prompt=user_msg, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ThinkingBlock):
                        thinking_blocks.append(block.thinking)
            elif isinstance(message, ResultMessage):
                usage = _usage_dict(getattr(message, "usage", None))
                structured = getattr(message, "structured_output", None)
                subtype = getattr(message, "subtype", None)
        elapsed = time.time() - t0

        verdicts = structured.get("verdicts", []) or [] if isinstance(structured, dict) else []

        return JudgeResult(
            verdicts=verdicts,
            usage=usage,
            elapsed_s=elapsed,
            user_msg=user_msg,
            parse_ok=structured is not None,
            extras={
                "cost_estimate_usd": _cost_for_usage(usage, self.model),
                "subtype":           subtype,
                "thinking":          thinking_blocks,
            },
        )
