"""Small, versioned SQLite migrations.

SQLite is the authoritative local store. The app intentionally supports a
single database file; WAL mode allows multiple API workers to share cache and
job state without a process-local source of truth.
"""

import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"pragma table_info({table})")}


def _add_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    declaration: str,
) -> None:
    if column not in _columns(conn, table):
        conn.execute(f"alter table {table} add column {column} {declaration}")


def _migration_001_message_metadata(conn: sqlite3.Connection) -> None:
    _add_column(conn, "sessions", "document_id", "text")
    _add_column(conn, "messages", "thinking_summary", "text")
    _add_column(conn, "messages", "thinking_elapsed_ms", "integer")
    _add_column(conn, "messages", "learning_meta", "text")


def _migration_002_auth_credentials(conn: sqlite3.Connection) -> None:
    _add_column(conn, "users", "password_hash", "text")
    _add_column(conn, "users", "password_salt", "text")


def _migration_003_shared_runtime_state(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists semantic_cache (
          cache_key text primary key,
          subject text not null,
          query text not null,
          hits_json text not null,
          created_at_epoch integer not null
        );
        create table if not exists semantic_jobs (
          id text primary key,
          cache_key text not null unique,
          subject text not null,
          query text not null,
          status text not null,
          attempts integer not null default 0,
          last_error text,
          created_at text not null,
          updated_at text not null
        );
        create index if not exists idx_semantic_jobs_status
          on semantic_jobs(status, updated_at);
        create table if not exists request_metrics (
          id text primary key,
          request_id text not null,
          method text not null,
          route text not null,
          status_code integer not null,
          duration_ms real not null,
          created_at text not null
        );
        create index if not exists idx_request_metrics_created
          on request_metrics(created_at);
        """
    )


def _migration_004_document_markdown(conn: sqlite3.Connection) -> None:
    # Databases created before the parsed source text was persisted have no
    # markdown column. Existing rows keep '' and are reported as needing a
    # re-upload rather than being silently reconstructed from FTS chunks.
    _add_column(conn, "documents", "markdown", "text not null default ''")


def _cjk_bigram_text(text: str) -> str:
    # SQLite's default tokenizer cannot split long CJK runs, so the index
    # stores whitespace-separated bigrams; queries are transformed the same way.
    from app.memory.text_index import cjk_bigram_text

    return cjk_bigram_text(text)


def _migration_005_document_chunk_bigram_index(conn: sqlite3.Connection) -> None:
    from app.memory.text_index import cjk_bigram_text

    conn.execute(
        """
        create virtual table if not exists document_chunks_index using fts5(
          chunk_rowid unindexed,
          text
        )
        """
    )
    tables = {
        str(row[0]) for row in conn.execute("select name from sqlite_master where type='table'")
    }
    if "document_chunks" not in tables:
        return
    indexed = {
        int(row[0])
        for row in conn.execute("select chunk_rowid from document_chunks_index")
    }
    for row in conn.execute("select rowid, content from document_chunks"):
        if row[0] in indexed:
            continue
        conn.execute(
            "insert into document_chunks_index(chunk_rowid, text) values (?, ?)",
            (row[0], cjk_bigram_text(row[1])),
        )


def _migration_006_agent_runs(conn: sqlite3.Connection) -> None:
    # execute (not executescript) preserves the caller's transaction/rollback.
    if not conn.in_transaction:
        conn.execute("begin")
    conn.execute("""create table agent_runs (
        id text primary key, session_id text not null references sessions(id) on delete cascade,
        user_id text not null, message_id text references messages(id) on delete set null,
        parent_run_id text references agent_runs(id) on delete set null,
        model_alias text, hidden integer not null default 0,
        status text not null check(status in ('running','succeeded','clarification','failed','cancelled','interrupted')),
        seq integer not null default 0, steps text not null default '[]', truncated integer not null default 0,
        prompt_version text not null, guard_version text not null,
        created_at text not null, updated_at text not null)""")
    conn.execute("create index agent_runs_owner_session on agent_runs(user_id,session_id,created_at)")


def _migration_007_auth_sessions(conn: sqlite3.Connection) -> None:
    if not conn.in_transaction:conn.execute("begin")
    conn.execute("""create table if not exists auth_sessions (
        sid text primary key,
        user_id text not null references users(id) on delete cascade,
        expires_at integer not null,
        revoked_at integer,
        created_at text not null)""")
    conn.execute("create index if not exists auth_sessions_owner on auth_sessions(user_id,expires_at)")


MIGRATIONS: tuple[tuple[int, str, Callable[[sqlite3.Connection], None]], ...] = (
    (1, "message_metadata", _migration_001_message_metadata),
    (2, "auth_credentials", _migration_002_auth_credentials),
    (3, "shared_runtime_state", _migration_003_shared_runtime_state),
    (4, "document_markdown", _migration_004_document_markdown),
    (5, "document_chunk_bigram_index", _migration_005_document_chunk_bigram_index),
    (6, "agent_runs", _migration_006_agent_runs),
    (7, "auth_sessions", _migration_007_auth_sessions),
)


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        create table if not exists schema_migrations (
          version integer primary key,
          name text not null,
          applied_at text not null
        )
        """
    )
    applied = {
        int(row[0])
        for row in conn.execute("select version from schema_migrations")
    }
    for version, name, migrate in MIGRATIONS:
        if version in applied:
            continue
        migrate(conn)
        conn.execute(
            "insert into schema_migrations(version, name, applied_at) values (?, ?, ?)",
            (version, name, datetime.now(timezone.utc).isoformat()),
        )
