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
import sqlite3
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

if __package__ in (None, ""):
    from src.pipeline.settings import Settings, RunSummary
else:
    from .settings import Settings, RunSummary


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


def build_settings(fail_rate: float | None = None) -> Settings:
    """Create a validated settings object for this run."""
    settings = Settings()
    if fail_rate is not None:
        settings.fail_rate = fail_rate
    return settings


def summarize_run(
    started_at: float,
    elapsed_seconds: float,
    answers: list[Answer],
    fail_rate: float,
    use_fake: bool = True,
) -> RunSummary:
    """Convert the finished batch into a validated RunSummary row."""
    return RunSummary(
        started_at=started_at,
        elapsed_seconds=elapsed_seconds,
        n_questions=len(answers),
        n_succeeded=sum(1 for a in answers),
        n_retries_total=sum(a.retries for a in answers),
        total_cost_usd=sum(a.cost_usd for a in answers),
        fail_rate=fail_rate,
        use_fake=use_fake,
    )


def save_results_json(answers: list[Answer], path: Path) -> None:
    """Persist each answer as a JSON object in a single file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "question": a.question,
            "text": a.text,
            "cost_usd": a.cost_usd,
            "retries": a.retries,
        }
        for a in answers
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_run_summary_db(summary: RunSummary, db_path: Path) -> None:
    """Persist one row in the runs table."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                started_at REAL,
                elapsed_seconds REAL,
                n_questions INTEGER,
                n_succeeded INTEGER,
                n_retries_total INTEGER,
                total_cost_usd REAL,
                fail_rate REAL,
                use_fake INTEGER
            )
            """
        )
        conn.execute(
            """
            INSERT INTO runs (
                started_at,
                elapsed_seconds,
                n_questions,
                n_succeeded,
                n_retries_total,
                total_cost_usd,
                fail_rate,
                use_fake
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary.started_at,
                summary.elapsed_seconds,
                summary.n_questions,
                summary.n_succeeded,
                summary.n_retries_total,
                summary.total_cost_usd,
                summary.fail_rate,
                int(summary.use_fake),
            ),
        )
        conn.commit()


# ---------- main ----------
if __name__ == "__main__":
    fail_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    settings = build_settings(fail_rate=fail_rate)
    sample = [
        Question(text="What is RAG in one sentence?"),
        Question(text="Name three uses of vector databases."),
        Question(text="Why might an LLM hallucinate?"),
    ]
    started = time.time()
    answers = asyncio.run(run_batch(sample, fail_rate=settings.fail_rate))
    elapsed = time.time() - started
    summary = summarize_run(
        started_at=started,
        elapsed_seconds=elapsed,
        answers=answers,
        fail_rate=settings.fail_rate,
        use_fake=settings.use_fake,
    )

    save_results_json(answers, settings.results_json)
    save_run_summary_db(summary, settings.results_db)

    print(f"\n{len(answers)} answers in {elapsed:.2f}s\n")
    for a in answers:
        print(f"- {a.text[:80]}")
    print("\nSaved summary:")
    print(summary.model_dump())
