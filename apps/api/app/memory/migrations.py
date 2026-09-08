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


MIGRATIONS: tuple[tuple[int, str, Callable[[sqlite3.Connection], None]], ...] = (
    (1, "message_metadata", _migration_001_message_metadata),
    (2, "auth_credentials", _migration_002_auth_credentials),
    (3, "shared_runtime_state", _migration_003_shared_runtime_state),
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
