import sqlite3
from pathlib import Path
from typing import Any

from app.config import Settings
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

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
                  unique(user_id, concept)
                );
                """
            )

    def ensure_user(self, user_id: str, display_name: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "insert or ignore into users(id, display_name, created_at) values (?, ?, ?)",
                (user_id, display_name or user_id, now_iso()),
            )

    def create_session(self, user_id: str, subject: str, title: str | None = None) -> dict[str, Any]:
        self.ensure_user(user_id)
        session_id = new_id("sess")
        ts = now_iso()
        title = title or self._default_title(subject)
        with self.connect() as conn:
            conn.execute(
                """
                insert into sessions(id, user_id, title, subject, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (session_id, user_id, title, subject, ts, ts),
            )
        return {"session_id": session_id, "title": title, "subject": subject}

    def list_sessions(self, user_id: str, query: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if query:
                rows = conn.execute(
                    """
                    SELECT DISTINCT s.id, s.user_id, s.title, s.subject, s.created_at, s.updated_at
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
                    select id, user_id, title, subject, created_at, updated_at
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
            conn.execute("delete from sessions where id = ?", (session_id,))

    def add_message(self, session_id: str, role: str, content: str, intent: str | None = None) -> str:
        message_id = new_id("msg")
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                """
                insert into messages(id, session_id, role, content, intent, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, intent, ts),
            )
            conn.execute("update sessions set updated_at = ? where id = ?", (ts, session_id))
        return message_id

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                select id, session_id, role, content, intent, created_at
                from messages
                where session_id = ?
                order by created_at asc
                """,
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

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

    def update_session_title(self, session_id: str, title: str) -> None:
        ts = now_iso()
        with self.connect() as conn:
            conn.execute(
                "update sessions set title = ?, updated_at = ? where id = ?",
                (title, ts, session_id),
            )

    def _default_title(self, subject: str) -> str:
        names = {"calculus": "\u9ad8\u6570\u7ec3\u4e60", "linear_algebra": "\u7ebf\u4ee3\u7ec3\u4e60", "probability": "\u6982\u7387\u8bba\u7ec3\u4e60"}
        return names.get(subject, "\u6570\u5b66\u8f85\u5bfc")

