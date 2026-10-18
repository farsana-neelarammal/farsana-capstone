"""Query the persisted pipeline runs from SQLite."""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from src.pipeline.settings import PROJECT_ROOT
from src.pipeline.store import list_run_summaries


def main() -> None:
    db_path = PROJECT_ROOT / "results.db"
    runs = list_run_summaries(db_path)
    if not runs:
        print(f"No runs found in {db_path}")
        return

    print(f"Found {len(runs)} saved runs in {db_path}")
    for i, run in enumerate(runs, start=1):
        print(
            f"{i}. started_at={run.started_at:.3f}, "
            f"elapsed_seconds={run.elapsed_seconds:.3f}, "
            f"n_questions={run.n_questions}, "
            f"n_succeeded={run.n_succeeded}, "
            f"fail_rate={run.fail_rate}, "
            f"use_fake={run.use_fake}"
        )


if __name__ == "__main__":
    main()
