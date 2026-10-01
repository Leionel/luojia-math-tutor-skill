"""Offline SQLite backup/restore-to-new-file and legacy review recovery audit.

Never resets candidates, reapplies reviews, or overwrites an existing database.
"""
import argparse
import json
import sqlite3
from pathlib import Path


def inspect(path: Path) -> dict:
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Integrity check failed: {integrity}")
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        graphs = {cid: json.loads(data) for cid, data in conn.execute("SELECT course_id,data FROM canonical_graphs")} if "canonical_graphs" in tables else {}
        candidates = [json.loads(r[0]) for r in conn.execute("SELECT data FROM graph_candidates")]
        counts, recovery = {}, []
        for candidate in candidates:
            status = candidate["status"]
            counts[status] = counts.get(status, 0) + 1
            if status in ("approved", "merged"):
                graph = graphs.get(candidate["course_id"])
                recovery.append({"candidate_id": candidate["candidate_id"], "course_id": candidate["course_id"],
                                 "status": status, "candidate_type": candidate["candidate_type"],
                                 "evidence_refs": candidate.get("evidence_refs", []),
                                 "canonical_snapshot_exists": graph is not None,
                                 "instruction": "Compare payload, complete revision and source manually; do not reapprove."})
        return {"integrity": integrity, "candidate_status_counts": counts, "canonical_courses": sorted(graphs),
                "reviewed_candidates_for_reconciliation": recovery}


def copy_database(source: Path, destination: Path):
    if destination.exists():
        raise ValueError("Destination exists; refusing to overwrite")
    if not source.is_file():
        raise ValueError("Source database does not exist")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
    return inspect(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "backup", "restore-copy"])
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action != "audit" and args.destination is None:
        parser.error("--destination is required; restore-copy always targets a new file")
    result = inspect(args.source) if args.action == "audit" else copy_database(args.source, args.destination)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
