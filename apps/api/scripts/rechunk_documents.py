"""Re-chunk every stored document with the current structure-aware chunker.

The read path (fast_context -> search_document_chunks) and the eval set both
assume the chunk table reflects app.knowledge.document_chunking; older rows
came from the fixed-window chunker and must be rebuilt in place.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.knowledge.document_chunking import chunk_document
from app.memory.repository import Repository


def main() -> None:
    repo = Repository(get_settings())
    with repo.connect() as conn:
        docs = [
            (row["id"], row["markdown"])
            for row in conn.execute("select id, markdown from documents")
        ]
    for document_id, markdown in docs:
        chunks = chunk_document(markdown)
        repo.clear_document_chunks(document_id)
        repo.insert_document_chunks(document_id, chunks)
        print(f"{document_id}: {len(chunks)} chunks (from {len(markdown)} chars)")


if __name__ == "__main__":
    main()
