import hashlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from app.config import Settings
from app.knowledge.concepts import extract_explicit_concepts
from app.knowledge.schema import KnowledgeHit, KnowledgeItem
from app.memory.migrations import apply_migrations
from app.memory.models import new_id, now_iso


def _sqlite_path(database_url: str) -> Path:
    if database_url.startswith("sqlite:///"):
        return Path(database_url.replace("sqlite:///", "", 1)).resolve()
    raise ValueError("MVP only supports sqlite:/// database URLs")


class Repository:
    def __init__(self, settings: Settings):
        self.db_path = _sqlite_path(settings.database_url)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("pragma foreign_keys = on")
        conn.execute("pragma journal_mode = wal")
        conn.execute("pragma busy_timeout = 5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                create table if not exists users (
                  id text primary key,
                  display_name text,
                  created_at text not null
                );

                create table if not exists sessions (
                  id text primary key,
                  user_id text not null,
                  title text,
                  subject text,
                  created_at text not null,
                  updated_at text not null
                );

                create table if not exists messages (
                  id text primary key,
                  session_id text not null,
                  role text not null,
                  content text not null,
                  intent text,
                  created_at text not null
                );

                create table if not exists attempts (
                  id text primary key,
                  session_id text not null,
                  user_id text not null,
                  problem_text text not null,
                  student_step text,
                  is_correct integer,
                  mistake_code text,
                  verifier_summary text,
                  created_at text not null
                );

                create table if not exists mistake_events (
                  id text primary key,
                  user_id text not null,
                  session_id text not null,
                  subject text,
                  concept text,
                  mistake_code text not null,
                  created_at text not null
                );

                create table if not exists mastery (
                  id text primary key,
                  user_id text not null,
                  concept text not null,
                  score real not null default 0.5,
                  attempts_count integer not null default 0,
                  correct_count integer not null default 0,
                  updated_at text not null,
                  last_pushed_at text,
                  unique(user_id, concept)
                );

                create table if not exists documents (
                  id text primary key,
                  filename text,
                  user_id text not null,
                  created_at text not null
                );

                create virtual table if not exists document_chunks using fts5(
                  id unindexed,
                  document_id unindexed,
                  content
                );

                create table if not exists notes (
                  id text primary key,
                  user_id text not null,
                  session_id text not null,
                  subject text,
                  content text not null,
                  created_at text not null
                );
                """
            )
            
            apply_migrations(conn)

    def ensure_user(self, user_id: str, display_name: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "insert or ignore into users(id, display_name, created_at) values (?, ?, ?)",
                (user_id, display_name or user_id, now_iso()),
            )

    def create_session(self, user_id: str, subject: str, title: str | None = None, document_id: str | None = None) -> dict[str, Any]:
        self.ensure_user(user_id)
        session_id = new_id("sess")
        ts = now_iso()
        title = title or self._default_title(subject)
        with self.connect() as conn:
            conn.execute(
                """
                insert into sessions(id, user_id, title, subject, created_at, updated_at, document_id)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, title, subject, ts, ts, document_id),
            )
        return {"session_id": session_id, "title": title, "subject": subject, "document_id": document_id}

    def list_sessions(self, user_id: str, query: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if query:
                rows = conn.execute(
                    """
                    SELECT DISTINCT s.id, s.user_id, s.title, s.subject,
                           s.created_at, s.updated_at, s.document_id
                    FROM sessions s
                    LEFT JOIN messages m ON s.id = m.session_id
                    WHERE s.user_id = ? AND (
                        s.title LIKE ? OR m.content LIKE ?
                    )
                    ORDER BY s.updated_at DESC
                    """,
                    (user_id, f"%{query}%", f"%{query}%")
                )
            else:
                rows = conn.execute(
                    """
                    select id, user_id, title, subject, created_at,
                           updated_at, document_id
                    from sessions
                    where user_id = ?
                    order by updated_at desc
                    """,
                    (user_id,),
                )
            return [dict(row) for row in rows.fetchall()]

    def delete_session(self, session_id: str) -> None:
        with self.connect() as conn:
            conn.execute("delete from messages where session_id = ?", (session_id,))
            conn.execute("delete from attempts where session_id = ?", (session_id,))
            conn.execute("delete from mistake_events where session_id = ?", (session_id,))
            conn.execute("delete from notes where session_id = ?", (session_id,))
            conn.execute("delete from sessions where id = ?", (session_id,))

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        thinking_summary: str | None = None,
        thinking_elapsed_ms: int | None = None,
        learning_meta: dict[str, Any] | None = None,
    ) -> str:
        message_id = new_id("msg")
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                insert into messages(
                  id, session_id, role, content, intent, thinking_summary,
                  thinking_elapsed_ms, learning_meta, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    intent,
                    thinking_summary,
                    thinking_elapsed_ms,
                    (
                        json.dumps(learning_meta, ensure_ascii=False)
                        if learning_meta is not None
                        else None
                    ),
                    ts,
                ),
            )
            conn.execute("update sessions set updated_at = ? where id = ?", (ts, session_id))
        return message_id

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select m.id, m.session_id, m.role, m.content, m.intent,
                       m.thinking_summary, m.thinking_elapsed_ms,
                       m.learning_meta, m.created_at,
                       s.subject as session_subject
                from messages m
                join sessions s on s.id = m.session_id
                where m.session_id = ?
                order by m.created_at asc
                """,
                (session_id,),
            ).fetchall()
        messages = [dict(row) for row in rows]
        for message in messages:
            raw_meta = message.get("learning_meta")
            if not raw_meta:
                message["learning_meta"] = self._legacy_learning_meta(
                    message
                )
                message.pop("session_subject", None)
                continue
            try:
                message["learning_meta"] = json.loads(raw_meta)
            except (TypeError, json.JSONDecodeError):
                message["learning_meta"] = None
            explicit_concepts = extract_explicit_concepts(
                message.get("content") or ""
            )
            if explicit_concepts and isinstance(
                message["learning_meta"],
                dict,
            ):
                message["learning_meta"]["concepts"] = explicit_concepts
            message.pop("session_subject", None)
        return messages

    @staticmethod
    def _legacy_learning_meta(message: dict[str, Any]) -> dict | None:
        if message.get("role") != "assistant":
            return None
        summary = message.get("thinking_summary") or ""
        intent = message.get("intent")
        if not summary and not intent:
            return None

        concepts_match = re.search(
            r"(?:涉及概念|已定位相关概念)：([^；。\n]+)",
            summary,
        )
        summary_concepts = (
            [
                concept.strip()
                for concept in concepts_match.group(1).split("、")
                if concept.strip()
            ]
            if concepts_match
            else []
        )
        explicit_concepts = extract_explicit_concepts(
            message.get("content") or ""
        )
        concepts = explicit_concepts or summary_concepts
        objective_match = re.search(
            r"已识别学习目标：([^；。\n]+)",
            summary,
        )
        strategy_match = re.search(
            r"采用教学策略：([^；。\n]+)",
            summary,
        )
        verify_match = re.search(
            r"\[VERIFY\]\s*([^\n]+)",
            summary,
        )
        verifier_summary = (
            verify_match.group(1).strip()
            if verify_match
            else ""
        )
        verified = any(
            marker in verifier_summary
            for marker in ("验证已通过", "验算正确", "符号验证已通过")
        )
        is_correct = True if verified else None
        if any(
            marker in verifier_summary
            for marker in ("不一致", "发现偏差", "验算错误")
        ):
            verified = True
            is_correct = False

        return {
            "intent": intent or "solve_step_by_step",
            "subject": message.get("session_subject") or "auto",
            "concepts": concepts,
            "verified": verified,
            "is_correct": is_correct,
            "mistake": None,
            "verifier_summary": verifier_summary,
            "hint_level": 0,
            "mastery_score": 0.5,
            "mastery_label": "待评估",
            "mastery_delta": 0.0,
            "pedagogical_action": (
                strategy_match.group(1).strip()
                if strategy_match
                else ""
            ),
            "learning_objective": (
                objective_match.group(1).strip()
                if objective_match
                else ""
            ),
            "route": "legacy",
        }

    def truncate_messages_after(self, session_id: str, message_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                delete from messages
                where session_id = ? and created_at >= (
                  select created_at from messages where id = ?
                )
                """,
                (session_id, message_id),
            )

    def add_attempt(
        self,
        session_id: str,
        user_id: str,
        problem_text: str,
        student_step: str | None,
        is_correct: bool | None,
        mistake_code: str | None,
        verifier_summary: str | None,
    ) -> str:
        attempt_id = new_id("att")
        with self.connect() as conn:
            conn.execute(
                """
                insert into attempts(
                  id, session_id, user_id, problem_text, student_step,
                  is_correct, mistake_code, verifier_summary, created_at
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    session_id,
                    user_id,
                    problem_text,
                    student_step,
                    None if is_correct is None else int(is_correct),
                    mistake_code,
                    verifier_summary,
                    now_iso(),
                ),
            )
        return attempt_id

    def insert_document(self, filename: str, user_id: str) -> str:
        document_id = new_id("doc")
        with self.connect() as conn:
            conn.execute(
                """
                insert into documents(id, filename, user_id, created_at)
                values (?, ?, ?, ?)
                """,
                (document_id, filename, user_id, now_iso()),
            )
        return document_id

    def insert_document_chunks(self, document_id: str, chunks: list[str]) -> None:
        with self.connect() as conn:
            conn.executemany(
                """
                insert into document_chunks(id, document_id, content)
                values (?, ?, ?)
                """,
                [(new_id("chunk"), document_id, chunk) for chunk in chunks],
            )

    def list_document_chunks(self, document_id: str) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select content from document_chunks
                where document_id = ?
                order by rowid
                """,
                (document_id,),
            ).fetchall()
        return [row["content"] for row in rows]

    def get_document(self, document_id: str, user_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                select id, filename, user_id, created_at from documents
                where id = ? and user_id = ?
                """,
                (document_id, user_id),
            ).fetchone()
        return dict(row) if row else None

    def save_note(self, user_id: str, session_id: str, subject: str, content: str) -> str:
        note_id = new_id("note")
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                insert into notes(id, user_id, session_id, subject, content, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (note_id, user_id, session_id, subject, content, ts),
            )
        return note_id

    def list_notes(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, user_id, session_id, subject, content, created_at
                from notes
                where user_id = ?
                order by created_at desc
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_note(self, note_id: str) -> None:
        with self.connect() as conn:
            conn.execute("delete from notes where id = ?", (note_id,))

    def add_mistake_event(
        self,
        user_id: str,
        session_id: str,
        subject: str,
        concept: str | None,
        mistake_code: str,
    ) -> str:
        event_id = new_id("mis")
        with self.connect() as conn:
            conn.execute(
                """
                insert into mistake_events(id, user_id, session_id, subject, concept, mistake_code, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, user_id, session_id, subject, concept, mistake_code, now_iso()),
            )
        return event_id

    def list_mistakes(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, user_id, session_id, subject, concept, mistake_code, created_at
                from mistake_events
                where session_id = ?
                order by created_at desc
                """,
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ── mastery ──

    def get_mastery(self, user_id: str, concept: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "select * from mastery where user_id = ? and concept = ?",
                (user_id, concept),
            ).fetchone()
        return dict(row) if row else None

    def upsert_mastery(
        self, user_id: str, concept: str, score: float, is_correct: bool
    ) -> None:
        ts = now_iso()
        with self.connect() as conn:
            existing = conn.execute(
                "select id, attempts_count, correct_count from mastery where user_id = ? and concept = ?",
                (user_id, concept),
            ).fetchone()
            if existing:
                new_attempts = existing["attempts_count"] + 1
                new_correct = existing["correct_count"] + (1 if is_correct else 0)
                conn.execute(
                    "update mastery set score = ?, attempts_count = ?, correct_count = ?, updated_at = ? where id = ?",
                    (score, new_attempts, new_correct, ts, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    insert into mastery(id, user_id, concept, score, attempts_count, correct_count, updated_at)
                    values (?, ?, ?, ?, 1, ?, ?)
                    """,
                    (new_id("mst"), user_id, concept, score, 1 if is_correct else 0, ts),
                )

    def list_mastery(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "select concept, score, attempts_count, correct_count, updated_at from mastery where user_id = ? order by updated_at desc",
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_consecutive_errors(self, user_id: str, concept: str) -> int:
        """获取用户最近连续错误次数（从最近的 attempt 往回数）。

        统计所有概念的连续错误，不按单个概念过滤。
        这样即使用户原题文本不含标准概念名，也能正确累积错误计数。
        """
        with self.connect() as conn:
            rows = conn.execute(
                """
                select is_correct from attempts
                where user_id = ?
                order by created_at desc
                limit 20
                """,
                (user_id,),
            ).fetchall()
        count = 0
        for row in rows:
            if row["is_correct"] == 0:
                count += 1
            else:
                break
        return count

    # ── user mistakes aggregation ──

    def list_user_mistakes(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, user_id, session_id, subject, concept, mistake_code, created_at
                from mistake_events
                where user_id = ?
                order by created_at desc
                limit ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_mistake(self, mistake_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                select id, user_id, session_id, subject, concept, mistake_code, created_at
                from mistake_events
                where id = ?
                """,
                (mistake_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_mistake_stats(self, user_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select mistake_code, concept, count(*) as count
                from mistake_events
                where user_id = ?
                group by mistake_code, concept
                order by count desc
                limit 20
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def update_session_meta(self, session_id: str, title: str, subject: str = None) -> None:
        ts = now_iso()
        with self.connect() as conn:
            if subject:
                conn.execute(
                    "update sessions set title = ?, subject = ?, updated_at = ? where id = ?",
                    (title, subject, ts, session_id),
                )
            else:
                conn.execute(
                    "update sessions set title = ?, updated_at = ? where id = ?",
                    (title, ts, session_id),
                )

    def session_belongs_to(self, session_id: str, user_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "select 1 from sessions where id = ? and user_id = ?",
                (session_id, user_id),
            ).fetchone()
        return row is not None

    def note_belongs_to(self, note_id: str, user_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "select 1 from notes where id = ? and user_id = ?",
                (note_id, user_id),
            ).fetchone()
        return row is not None

    def create_auth_user(
        self,
        user_id: str,
        display_name: str,
        password_hash: str,
        password_salt: str,
    ) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    """
                    insert into users(
                      id, display_name, password_hash, password_salt, created_at
                    ) values (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        display_name,
                        password_hash,
                        password_salt,
                        now_iso(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_auth_user(self, user_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                select id, display_name, password_hash, password_salt, created_at
                from users where id = ?
                """,
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def semantic_cache_key(subject: str, query: str) -> str:
        normalized = f"{subject.strip()}\n{' '.join(query.split())}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_semantic_cache(
        self,
        subject: str,
        query: str,
        ttl_seconds: int,
    ) -> list[KnowledgeHit]:
        cache_key = self.semantic_cache_key(subject, query)
        cutoff = int(time.time()) - max(0, ttl_seconds)
        with self.connect() as conn:
            row = conn.execute(
                """
                select hits_json from semantic_cache
                where cache_key = ? and created_at_epoch >= ?
                """,
                (cache_key, cutoff),
            ).fetchone()
        if not row:
            return []
        try:
            payload = json.loads(row["hits_json"])
            return [
                KnowledgeHit(
                    item=KnowledgeItem(**entry["item"]),
                    score=int(entry["score"]),
                )
                for entry in payload
            ]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return []

    def put_semantic_cache(
        self,
        subject: str,
        query: str,
        hits: list[KnowledgeHit],
    ) -> None:
        cache_key = self.semantic_cache_key(subject, query)
        payload = json.dumps(
            [
                {"item": asdict(hit.item), "score": hit.score}
                for hit in hits
            ],
            ensure_ascii=False,
        )
        with self.connect() as conn:
            conn.execute(
                """
                insert into semantic_cache(
                  cache_key, subject, query, hits_json, created_at_epoch
                ) values (?, ?, ?, ?, ?)
                on conflict(cache_key) do update set
                  hits_json = excluded.hits_json,
                  created_at_epoch = excluded.created_at_epoch
                """,
                (cache_key, subject, query, payload, int(time.time())),
            )

    def enqueue_semantic_job(self, subject: str, query: str) -> str:
        cache_key = self.semantic_cache_key(subject, query)
        job_id = new_id("sem")
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                insert into semantic_jobs(
                  id, cache_key, subject, query, status, created_at, updated_at
                ) values (?, ?, ?, ?, 'pending', ?, ?)
                on conflict(cache_key) do update set
                  status = case
                    when semantic_jobs.status = 'running' then 'running'
                    else 'pending'
                  end,
                  last_error = null,
                  updated_at = excluded.updated_at
                """,
                (job_id, cache_key, subject, query, ts, ts),
            )
            row = conn.execute(
                "select id from semantic_jobs where cache_key = ?",
                (cache_key,),
            ).fetchone()
        return str(row["id"])

    def recover_semantic_jobs(self) -> None:
        with self.connect() as conn:
            conn.execute(
                "update semantic_jobs set status = 'pending' where status = 'running'"
            )

    def claim_semantic_job(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("begin immediate")
            row = conn.execute(
                """
                select * from semantic_jobs
                where status = 'pending' and attempts < 3
                order by updated_at asc limit 1
                """
            ).fetchone()
            if not row:
                return None
            conn.execute(
                """
                update semantic_jobs
                set status = 'running', attempts = attempts + 1, updated_at = ?
                where id = ?
                """,
                (now_iso(), row["id"]),
            )
        return dict(row)

    def complete_semantic_job(
        self,
        job_id: str,
        subject: str,
        query: str,
        hits: list[KnowledgeHit],
    ) -> None:
        self.put_semantic_cache(subject, query, hits)
        with self.connect() as conn:
            conn.execute(
                "update semantic_jobs set status = 'done', updated_at = ? where id = ?",
                (now_iso(), job_id),
            )

    def fail_semantic_job(self, job_id: str, error: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                update semantic_jobs
                set status = case when attempts >= 3 then 'failed' else 'pending' end,
                    last_error = ?, updated_at = ?
                where id = ?
                """,
                (error[:500], now_iso(), job_id),
            )

    def record_request_metric(
        self,
        request_id: str,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                insert into request_metrics(
                  id, request_id, method, route, status_code, duration_ms, created_at
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("metric"),
                    request_id,
                    method,
                    route,
                    status_code,
                    duration_ms,
                    now_iso(),
                ),
            )

    def request_metrics_summary(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select route, count(*) as request_count,
                       round(avg(duration_ms), 2) as average_ms,
                       sum(case when status_code >= 500 then 1 else 0 end) as errors
                from request_metrics
                group by route order by request_count desc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def _default_title(self, subject: str) -> str:
        from datetime import datetime
        return f"新会话 {datetime.now().strftime('%m-%d %H:%M')}"
