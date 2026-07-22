import os
import argparse
import zipfile
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Rollback knowledge snapshot")
    parser.add_argument("--snapshot", type=str, help="Name of the snapshot zip file (without .zip) to restore. If not provided, the latest snapshot will be restored.")
    args = parser.parse_args()

    # Determine paths
    repo_root = Path(__file__).resolve().parents[1]
    snapshot_dir = repo_root / "data" / "snapshots"
    
    if not snapshot_dir.exists():
        print(f"Error: Snapshot directory not found at {snapshot_dir}")
        return

    # Find snapshot zip
    if args.snapshot:
        zip_name = args.snapshot
        if not zip_name.endswith('.zip'):
            zip_name += '.zip'
        target_zip = snapshot_dir / zip_name
        if not target_zip.exists():
            print(f"Error: Specified snapshot not found at {target_zip}")
            return
    else:
        zips = list(snapshot_dir.glob("*.zip"))
        if not zips:
            print(f"Error: No snapshots found in {snapshot_dir}")
            return
        # sort by name, name works since it's timestamped
        zips.sort(key=lambda x: x.name)
        target_zip = zips[-1]

    print(f"Restoring from snapshot: {target_zip.name}")

    # Determine destination paths
    try:
        import sys
        sys.path.insert(0, str(repo_root / "apps" / "api"))
        from app.config import get_settings
        settings = get_settings()
        knowledge_root = settings.knowledge_root
        output_dir = knowledge_root / "output"
    except Exception as e:
        print(f"Warning: Could not load settings from app.config: {e}")
        print("Falling back to default paths.")
        knowledge_root = repo_root / "luojia-math-tutor" / "references"
        output_dir = knowledge_root / "output"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract zip securely and atomically
    with zipfile.ZipFile(target_zip, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        
        def safe_extract(filename, target_dir):
            if filename in file_list:
                target_path = target_dir / filename
                tmp_path = target_path.with_suffix('.tmp')
                # Read bytes and write to temp file
                data = zip_ref.read(filename)
                with open(tmp_path, 'wb') as f:
                    f.write(data)
                # Atomic replace
                os.replace(tmp_path, target_path)
                print(f"Restored {target_path}")

        safe_extract("published_knowledge.json", output_dir)
        safe_extract("prerequisites_graph.json", output_dir)
        safe_extract("embeddings.json", knowledge_root)

    print("Rollback completed successfully.")

if __name__ == "__main__":
    main()
