import datetime
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS graph_candidates (
    candidate_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS student_unit_states (
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (student_id, course_id, unit_id)
);

CREATE TABLE IF NOT EXISTS student_case_states (
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (student_id, course_id, case_id)
);

CREATE TABLE IF NOT EXISTS process_events (
    event_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS graph_revisions (
    revision_id TEXT PRIMARY KEY,
    parent_revision_id TEXT,
    course_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    action TEXT NOT NULL,
    changed_entities TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class CourseStore:
    """SQLite-backed persistence for course graph candidates, student overlay, and review history.

    Pass path=None for an in-memory store (used by tests and demo mode).
    """

    def __init__(self, path: Optional[str] = None):
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        # In-memory fallbacks keep event idempotency and revision history
        # working in demo/test mode (no COURSE_STORE_PATH configured).
        self._memory_events: set[str] = set()
        self._memory_revisions: list[dict[str, Any]] = []
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.executescript(SCHEMA)
            self._conn.commit()
            logger.info(f"CourseStore opened at {path}")

    @property
    def persistent(self) -> bool:
        return self._conn is not None

    def _execute(self, sql: str, params: tuple = ()) -> None:
        if not self._conn:
            return
        with self._lock:
            self._conn.execute(sql, params)
            self._conn.commit()

    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        if not self._conn:
            return []
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    # --- candidates -------------------------------------------------------

    def upsert_candidate(self, candidate_id: str, course_id: str, data: dict[str, Any]) -> None:
        self._execute(
            "INSERT INTO graph_candidates (candidate_id, course_id, data) VALUES (?, ?, ?) "
            "ON CONFLICT(candidate_id) DO UPDATE SET data = excluded.data, course_id = excluded.course_id",
            (candidate_id, course_id, json.dumps(data, ensure_ascii=False)),
        )

    def load_candidates(self, course_id: Optional[str] = None) -> list[dict[str, Any]]:
        if course_id:
            rows = self._query(
                "SELECT data FROM graph_candidates WHERE course_id = ?", (course_id,)
            )
        else:
            rows = self._query("SELECT data FROM graph_candidates")
        return [json.loads(r[0]) for r in rows]

    # --- student overlay --------------------------------------------------

    def upsert_unit_state(self, student_id: str, course_id: str, unit_id: str, data: dict[str, Any]) -> None:
        self._execute(
            "INSERT INTO student_unit_states (student_id, course_id, unit_id, data) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(student_id, course_id, unit_id) DO UPDATE SET data = excluded.data",
            (student_id, course_id, unit_id, json.dumps(data, ensure_ascii=False)),
        )

    def load_unit_states(self, course_id: Optional[str] = None) -> list[dict[str, Any]]:
        if course_id:
            rows = self._query(
                "SELECT data FROM student_unit_states WHERE course_id = ?", (course_id,)
            )
        else:
            rows = self._query("SELECT data FROM student_unit_states")
        return [json.loads(r[0]) for r in rows]

    def upsert_case_state(self, student_id: str, course_id: str, case_id: str, data: dict[str, Any]) -> None:
        self._execute(
            "INSERT INTO student_case_states (student_id, course_id, case_id, data) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(student_id, course_id, case_id) DO UPDATE SET data = excluded.data",
            (student_id, course_id, case_id, json.dumps(data, ensure_ascii=False)),
        )

    def load_case_states(self, course_id: Optional[str] = None) -> list[dict[str, Any]]:
        if course_id:
            rows = self._query(
                "SELECT data FROM student_case_states WHERE course_id = ?", (course_id,)
            )
        else:
            rows = self._query("SELECT data FROM student_case_states")
        return [json.loads(r[0]) for r in rows]

    # --- process events (append-only) --------------------------------------

    def event_exists(self, event_id: str) -> bool:
        if not self._conn:
            return event_id in self._memory_events
        return bool(self._query(
            "SELECT 1 FROM process_events WHERE event_id = ?", (event_id,)
        ))

    def append_event(
        self,
        event_id: str,
        student_id: str,
        course_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if not self._conn:
            self._memory_events.add(event_id)
            return
        self._execute(
            "INSERT OR IGNORE INTO process_events (event_id, student_id, course_id, event_type, payload) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_id, student_id, course_id, event_type, json.dumps(payload, ensure_ascii=False)),
        )

    # --- graph revisions ----------------------------------------------------

    def append_revision(
        self,
        revision_id: str,
        parent_revision_id: Optional[str],
        course_id: str,
        candidate_id: str,
        action: str,
        changed_entities: dict[str, Any],
        reviewer_id: str,
        reason: str = "",
    ) -> None:
        record = {
            "revision_id": revision_id,
            "parent_revision_id": parent_revision_id,
            "course_id": course_id,
            "candidate_id": candidate_id,
            "action": action,
            "changed_entities": changed_entities,
            "reviewer_id": reviewer_id,
            "reason": reason,
            "created_at": datetime.datetime.now().isoformat(),
        }
        if not self._conn:
            self._memory_revisions.append(record)
            return
        self._execute(
            "INSERT OR IGNORE INTO graph_revisions "
            "(revision_id, parent_revision_id, course_id, candidate_id, action, changed_entities, reviewer_id, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                revision_id,
                parent_revision_id,
                course_id,
                candidate_id,
                action,
                json.dumps(changed_entities, ensure_ascii=False),
                reviewer_id,
                reason,
            ),
        )

    def latest_revision_id(self, course_id: str) -> Optional[str]:
        if not self._conn:
            course_revisions = [r for r in self._memory_revisions if r["course_id"] == course_id]
            return course_revisions[-1]["revision_id"] if course_revisions else None
        rows = self._query(
            "SELECT revision_id FROM graph_revisions WHERE course_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (course_id,),
        )
        return rows[0][0] if rows else None

    def list_revisions(self, course_id: str) -> list[dict[str, Any]]:
        if not self._conn:
            return [r for r in self._memory_revisions if r["course_id"] == course_id]
        rows = self._query(
            "SELECT revision_id, parent_revision_id, candidate_id, action, changed_entities, "
            "reviewer_id, reason, created_at FROM graph_revisions WHERE course_id = ? "
            "ORDER BY created_at ASC",
            (course_id,),
        )
        return [
            {
                "revision_id": r[0],
                "parent_revision_id": r[1],
                "candidate_id": r[2],
                "action": r[3],
                "changed_entities": json.loads(r[4]),
                "reviewer_id": r[5],
                "reason": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]
