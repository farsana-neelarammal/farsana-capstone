"""SQLite storage helpers for the pipeline run history."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .settings import RunSummary


def create_runs_table(conn: sqlite3.Connection) -> None:
    """Ensure the `runs` table exists for persisted summaries."""
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
    conn.commit()


def save_run_summary(summary: RunSummary, db_path: str | Path) -> None:
    """Persist one run summary row to the SQLite database."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        create_runs_table(conn)
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


def list_run_summaries(db_path: str | Path) -> list[RunSummary]:
    """Read all saved runs, newest first."""
    path = Path(db_path)
    if not path.exists():
        return []

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """
            SELECT
                started_at,
                elapsed_seconds,
                n_questions,
                n_succeeded,
                n_retries_total,
                total_cost_usd,
                fail_rate,
                use_fake
            FROM runs
            ORDER BY started_at DESC
            """
        ).fetchall()

    return [
        RunSummary(
            started_at=row[0],
            elapsed_seconds=row[1],
            n_questions=row[2],
            n_succeeded=row[3],
            n_retries_total=row[4],
            total_cost_usd=row[5],
            fail_rate=row[6],
            use_fake=bool(row[7]),
        )
        for row in rows
    ]
