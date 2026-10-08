"""Persistence of the parsed document source text.

`documents.markdown` is the single source of truth for anything that needs the
whole parsed text. FTS chunks are a derived retrieval artifact and must never
be re-joined to reconstruct a document: `chunk_markdown` overlaps by 50 chars,
so the reconstruction duplicates text at every boundary.
"""

import sqlite3

from app.main_deps import get_repository
from app.memory.migrations import MIGRATIONS, apply_migrations


def test_insert_document_persists_markdown():
    repo = get_repository()
    markdown = "# 第2章\n\n定义 2.1 不动点：若 f(x*) = x*，则称 x* 为不动点。\n"

    document_id = repo.insert_document("sample.pdf", "md-user", markdown)
    try:
        assert repo.get_document_markdown(document_id, "md-user") == markdown
    finally:
        with repo.connect() as conn:
            conn.execute("delete from documents where id = ?", (document_id,))


def test_insert_document_defaults_to_empty_markdown():
    repo = get_repository()

    document_id = repo.insert_document("legacy.pdf", "md-user")
    try:
        assert repo.get_document_markdown(document_id, "md-user") == ""
    finally:
        with repo.connect() as conn:
            conn.execute("delete from documents where id = ?", (document_id,))


def test_get_document_markdown_is_scoped_to_the_owner():
    repo = get_repository()

    document_id = repo.insert_document("scoped.pdf", "owner-a", "# secret")
    try:
        assert repo.get_document_markdown(document_id, "owner-b") is None
        assert repo.get_document_markdown("doc_missing", "owner-a") is None
    finally:
        with repo.connect() as conn:
            conn.execute("delete from documents where id = ?", (document_id,))


def test_migration_adds_markdown_to_a_legacy_documents_table(tmp_path):
    """Databases created before this column existed must be upgraded in place."""
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            create table documents (
              id text primary key,
              filename text,
              user_id text not null,
              created_at text not null
            );
            create table sessions (id text primary key);
            create table messages (id text primary key);
            create table users (id text primary key);
            """
        )
        conn.execute(
            "insert into documents(id, filename, user_id, created_at) "
            "values ('doc1', 'old.pdf', 'u1', '2026-01-01T00:00:00Z')"
        )

    with sqlite3.connect(db_path) as conn:
        apply_migrations(conn)
        columns = {str(row[1]) for row in conn.execute("pragma table_info(documents)")}
        assert "markdown" in columns

        row = conn.execute(
            "select filename, markdown from documents where id = 'doc1'"
        ).fetchone()
        assert row[0] == "old.pdf"
        assert row[1] == "", "pre-existing rows must default to empty, not NULL"

        versions = {int(v[0]) for v in conn.execute("select version from schema_migrations")}
        assert 4 in versions


def test_migrations_are_registered_in_order():
    versions = [version for version, _, _ in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(set(versions)) == len(versions)
    assert versions[-1] == 7
