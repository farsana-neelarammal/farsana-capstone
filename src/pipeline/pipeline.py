"""pipeline.py — Week 2 hands-on starter.

We'll fill in the TODOs together during the live session. The pieces:

    Step 2 — async def ask_llm                 (one call)
    Step 3 — ask_llm_with_retry                (exponential backoff)
    Step 4 — run_batch with asyncio.gather     (parallel fan-out)
    Step 5 — JSON-formatted structured logging

For the live demo we call ``fake_ask_llm`` from ``fake_llm.py`` —
no API quota, no network flakiness, and a ``fail_rate`` knob so retries
fire on demand. In the lab you'll swap to the real ``AsyncOpenAI`` client
(same ``Question``/``Answer`` shape — only one import changes).

Run it (after the TODOs are filled):
    python pipeline.py           # fail_rate = 0.0  (clean parallel run)
    python pipeline.py 0.4       # fail_rate = 0.4  (forces retries)
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# When this file is executed directly, Python sets sys.path[0] to src/pipeline,
# so the project root is not on the import path. Add it explicitly.
if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

# Live-session stand-in. Same Pydantic shape as the real call.
from fake_llm import Question, Answer, fake_ask_llm, FakeLLMError


# ---------- Step 2: one async call ----------
async def ask_llm(q: Question, fail_rate: float = 0.0) -> Answer:
    """One call. Live demo: fake. Lab: real AsyncOpenAI (same signature)."""
    ans = await fake_ask_llm(q, fail_rate=fail_rate)
    log.info(f"asked: {q.text[:40]}")
    return ans


# ---------- Step 3: retry with exponential backoff ----------
async def ask_llm_with_retry(
    q: Question, tries: int = 3, fail_rate: float = 0.0
) -> Answer:
    """Retry up to ``tries`` times. Wait 1 s, 2 s, 4 s between attempts."""
    for attempt in range(tries):
        try:
            ans = await ask_llm(q, fail_rate=fail_rate)
            ans.retries = attempt
            return ans
        except Exception:
            if attempt == tries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"ask_llm_with_retry failed for {q.text!r} after {tries} attempts")


# ---------- Step 4: gather it all together ----------
async def run_batch(
    questions: list[Question], fail_rate: float = 0.0
) -> list[Answer]:
    """Fire all questions in parallel via ``asyncio.gather``."""
    tasks = [ask_llm_with_retry(q, fail_rate=fail_rate) for q in questions]
    return await asyncio.gather(*tasks)


# ---------- Step 5: structured (JSON) logging ----------
class JsonFormatter(logging.Formatter):
    """Emit one JSON record per log event."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        return json.dumps(payload)


log = logging.getLogger("pipeline")
log.setLevel(logging.INFO)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    log.addHandler(handler)


# ---------- main ----------
if __name__ == "__main__":
    import sys

    fail_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    sample = [
        Question(text="What is RAG in one sentence?"),
        Question(text="Name three uses of vector databases."),
        Question(text="Why might an LLM hallucinate?"),
    ]
    started = time.time()
    answers = asyncio.run(run_batch(sample, fail_rate=fail_rate))
    elapsed = time.time() - started
    print(f"\n{len(answers)} answers in {elapsed:.2f}s\n")
    for a in answers:
        print(f"- {a.text[:80]}")
