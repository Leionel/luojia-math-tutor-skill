import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def validate_knowledge_files():
    root_dir = Path(__file__).parent.parent
    knowledge_dir = root_dir / "apps" / "api" / "knowledge_root" / "output" # Trying to guess correct path
    
    # We saw earlier in loader.py: output_dir = get_settings().knowledge_root / "output"
    # Wait, the knowledge_root is usually luojia-math-tutor or something like data. 
    # Let's adjust to scan standard directories or just hardcode to `luojia-math-tutor/references/textbook` or `knowledge_root`.
    
    knowledge_dir = root_dir / "knowledge" / "output"
    # Actually, from loader.py, it's `get_settings().knowledge_root / "output"`. 
    
    try:
        import sys
        sys.path.append(str(root_dir / "apps" / "api"))
        from app.config import get_settings
        knowledge_dir = get_settings().knowledge_root / "output"
    except ImportError:
        logging.warning("Could not import app.config. Falling back to default path.")
        knowledge_dir = root_dir / "luojia-math-tutor" / "references" # fallback
    
    if not knowledge_dir.exists():
        logging.error(f"Knowledge directory not found: {knowledge_dir}")
        return False

    all_valid = True
    seen_ids = set()

    for json_file in knowledge_dir.glob("*.json"):
        logging.info(f"Validating {json_file.name}...")
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {json_file.name}: {e}")
            all_valid = False
            continue

        if not isinstance(data, list):
            logging.error(f"{json_file.name} should contain a JSON array.")
            all_valid = False
            continue

        for i, item in enumerate(data):
            # Check ID
            item_id = item.get("id")
            if not item_id:
                logging.warning(f"Item {i} in {json_file.name} is missing 'id'.")
            elif item_id in seen_ids:
                logging.error(f"Duplicate ID found: {item_id} in {json_file.name}")
                all_valid = False
            else:
                seen_ids.add(item_id)
            
            # Check required fields
            for field in ["concept_zh"]:
                if field not in item:
                    logging.warning(f"Item {item_id or i} in {json_file.name} is missing '{field}'.")
            
            # Type checks for new fields (warnings only, to allow incremental adoption)
            if "difficulty" in item and not isinstance(item["difficulty"], int):
                logging.warning(f"Item {item_id or i} 'difficulty' should be an integer.")
            
            if "related_exercises" in item and not isinstance(item["related_exercises"], list):
                logging.warning(f"Item {item_id or i} 'related_exercises' should be a list.")
                
            if "prerequisite" in item and not isinstance(item["prerequisite"], list):
                logging.warning(f"Item {item_id or i} 'prerequisite' should be a list.")

    if all_valid:
        logging.info(f"Validation complete! Checked {len(seen_ids)} unique items.")
    else:
        logging.error("Validation failed with errors. Check the logs above.")
        
    return all_valid


if __name__ == "__main__":
    success = validate_knowledge_files()
    exit(0 if success else 1)
