from contextlib import contextmanager
import copy
import datetime
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS root_episodes (
    episode_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS canonical_graphs (
    course_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL DEFAULT 0,
    seed_checksum TEXT NOT NULL,
    data TEXT NOT NULL
);
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
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        # In-memory fallbacks keep event idempotency and revision history
        # working in demo/test mode (no COURSE_STORE_PATH configured).
        self._memory_events: set[str] = set()
        self._event_records: dict[str, dict] = {}
        self._memory_unit_states: dict[tuple, dict] = {}
        self._memory_case_states: dict[tuple, dict] = {}
        self._memory_episodes: dict[str, dict] = {}
        self._transaction_depth = 0
        self._memory_revisions: list[dict[str, Any]] = []
        self._memory_graphs: dict[str, dict[str, Any]] = {}
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.executescript(SCHEMA)
            self._conn.commit()
            logger.info(f"CourseStore opened at {path}")

    @property
    def persistent(self) -> bool:
        return self._conn is not None

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def load_graph(self, course_id: str) -> Optional[dict[str, Any]]:
        if not self._conn:
            record = self._memory_graphs.get(course_id)
            return json.loads(json.dumps(record)) if record else None
        rows = self._query("SELECT generation, seed_checksum, data FROM canonical_graphs WHERE course_id=?", (course_id,))
        return {"generation": rows[0][0], "seed_checksum": rows[0][1], "data": json.loads(rows[0][2])} if rows else None

    def initialize_graph(self, course_id: str, data: dict[str, Any], seed_checksum: str) -> dict[str, Any]:
        """Seed once. Changing a seed file never overwrites reviewed database state."""
        with self._lock:
            if self._conn:
                self._execute("INSERT OR IGNORE INTO canonical_graphs(course_id,seed_checksum,data) VALUES(?,?,?)",
                              (course_id, seed_checksum, json.dumps(data, ensure_ascii=False)))
            elif course_id not in self._memory_graphs:
                self._memory_graphs[course_id] = {"generation": 0, "seed_checksum": seed_checksum, "data": json.loads(json.dumps(data))}
            return self.load_graph(course_id)

    def commit_review(self, candidate_before: dict[str, Any], candidate_after: dict[str, Any],
                      graph: dict[str, Any], generation: int, revision: dict[str, Any]) -> None:
        """One CAS transaction for candidate, canonical graph and complete audit record."""
        course_id = candidate_before["course_id"]
        with self._lock:
            if not self._conn:
                current = self._memory_graphs[course_id]
                if current["generation"] != generation:
                    raise ValueError("Graph changed; reload before reviewing")
                self._memory_graphs[course_id] = {**current, "generation": generation + 1, "data": json.loads(json.dumps(graph))}
                self._memory_revisions.append(revision)
                return
            with self._conn:
                self._conn.execute("BEGIN IMMEDIATE")
                row = self._conn.execute("SELECT data FROM graph_candidates WHERE candidate_id=? AND course_id=?",
                                         (candidate_before["candidate_id"], course_id)).fetchone()
                if not row or json.loads(row[0]) != candidate_before:
                    raise ValueError("Candidate changed; reload before reviewing")
                cursor = self._conn.execute("UPDATE canonical_graphs SET data=?, generation=generation+1 WHERE course_id=? AND generation=?",
                                            (json.dumps(graph, ensure_ascii=False), course_id, generation))
                if cursor.rowcount != 1:
                    raise ValueError("Graph changed; reload before reviewing")
                self._conn.execute("UPDATE graph_candidates SET data=?, updated_at=datetime('now') WHERE candidate_id=? AND course_id=?",
                                   (json.dumps(candidate_after, ensure_ascii=False), candidate_before["candidate_id"], course_id))
                self._conn.execute("INSERT INTO graph_revisions(revision_id,parent_revision_id,course_id,candidate_id,action,changed_entities,reviewer_id,reason) VALUES(?,?,?,?,?,?,?,?)",
                                   (revision["revision_id"], revision["parent_revision_id"], course_id, revision["candidate_id"], revision["action"], json.dumps(revision["changed_entities"], ensure_ascii=False), revision["reviewer_id"], revision["reason"]))

    def _execute(self, sql: str, params: tuple = ()) -> None:
        if not self._conn:
            return
        with self._lock:
            self._conn.execute(sql, params)
            if not self._transaction_depth:
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
        if not self._conn:
            self._memory_unit_states[(student_id, course_id, unit_id)] = copy.deepcopy(data)
            return
        self._execute(
            "INSERT INTO student_unit_states (student_id, course_id, unit_id, data) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(student_id, course_id, unit_id) DO UPDATE SET data = excluded.data",
            (student_id, course_id, unit_id, json.dumps(data, ensure_ascii=False)),
        )

    def load_unit_states(self, course_id: Optional[str] = None) -> list[dict[str, Any]]:
        if not self._conn:
            return copy.deepcopy([v for (_, cid, _), v in self._memory_unit_states.items() if not course_id or cid == course_id])
        if course_id:
            rows = self._query(
                "SELECT data FROM student_unit_states WHERE course_id = ?", (course_id,)
            )
        else:
            rows = self._query("SELECT data FROM student_unit_states")
        return [json.loads(r[0]) for r in rows]

    def upsert_case_state(self, student_id: str, course_id: str, case_id: str, data: dict[str, Any]) -> None:
        if not self._conn:
            self._memory_case_states[(student_id, course_id, case_id)] = copy.deepcopy(data)
            return
        self._execute(
            "INSERT INTO student_case_states (student_id, course_id, case_id, data) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(student_id, course_id, case_id) DO UPDATE SET data = excluded.data",
            (student_id, course_id, case_id, json.dumps(data, ensure_ascii=False)),
        )

    def load_case_states(self, course_id: Optional[str] = None) -> list[dict[str, Any]]:
        if not self._conn:
            return copy.deepcopy([v for (_, cid, _), v in self._memory_case_states.items() if not course_id or cid == course_id])
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
            self._event_records[event_id] = {"event_id": event_id, "student_id": student_id, "course_id": course_id, "event_type": event_type, "payload": copy.deepcopy(payload)}
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
            "ORDER BY rowid DESC LIMIT 1",
            (course_id,),
        )
        return rows[0][0] if rows else None

    def list_revisions(self, course_id: str) -> list[dict[str, Any]]:
        if not self._conn:
            return [r for r in self._memory_revisions if r["course_id"] == course_id]
        rows = self._query(
            "SELECT revision_id, parent_revision_id, candidate_id, action, changed_entities, "
            "reviewer_id, reason, created_at FROM graph_revisions WHERE course_id = ? "
            "ORDER BY rowid ASC",
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

    @contextmanager
    def transaction(self):
        """Shared lock + SQLite IMMEDIATE transaction; nested operations never commit early."""
        with self._lock:
            outer = self._transaction_depth == 0
            snapshot = None
            if outer:
                if self._conn:
                    self._conn.execute("BEGIN IMMEDIATE")
                else:
                    snapshot = copy.deepcopy((self._memory_events, self._event_records, self._memory_unit_states, self._memory_case_states, self._memory_episodes))
            self._transaction_depth += 1
            try:
                yield
                if outer and self._conn:
                    self._conn.commit()
            except BaseException:
                if outer:
                    if self._conn: self._conn.rollback()
                    elif snapshot:
                        self._memory_events, self._event_records, self._memory_unit_states, self._memory_case_states, self._memory_episodes = snapshot
                raise
            finally:
                self._transaction_depth -= 1

    def list_events(self, student_id: str, course_id: str, episode_id: str | None = None) -> list[dict]:
        if self._conn:
            rows = self._query("SELECT event_id,event_type,payload FROM process_events WHERE student_id=? AND course_id=? ORDER BY rowid", (student_id, course_id))
            events = [{"event_id": r[0], "event_type": r[1], "student_id": student_id, "course_id": course_id, "payload": json.loads(r[2])} for r in rows]
        else:
            events = copy.deepcopy([r for r in self._event_records.values() if r["student_id"] == student_id and r["course_id"] == course_id])
        return [e for e in events if not episode_id or e["payload"].get("episode_id") == episode_id]

    def event_record(self, event_id: str) -> dict | None:
        if self._conn:
            rows = self._query("SELECT student_id,course_id,event_type,payload FROM process_events WHERE event_id=?", (event_id,))
            return {"student_id": rows[0][0], "course_id": rows[0][1], "event_type": rows[0][2], "payload": json.loads(rows[0][3])} if rows else None
        return copy.deepcopy(self._event_records.get(event_id))

    def load_episode(self, episode_id: str) -> dict | None:
        if self._conn:
            rows = self._query("SELECT data FROM root_episodes WHERE episode_id=?", (episode_id,))
            return json.loads(rows[0][0]) if rows else None
        return copy.deepcopy(self._memory_episodes.get(episode_id))

    def save_episode(self, data: dict) -> None:
        if self._conn:
            self._execute("INSERT INTO root_episodes(episode_id,student_id,course_id,session_id,data) VALUES(?,?,?,?,?) ON CONFLICT(episode_id) DO UPDATE SET data=excluded.data",
                          (data["episode_id"], data["student_id"], data["course_id"], data["session_id"], json.dumps(data, ensure_ascii=False)))
        else:
            self._memory_episodes[data["episode_id"]] = copy.deepcopy(data)
