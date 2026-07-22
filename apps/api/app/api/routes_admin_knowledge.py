from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
from pathlib import Path
from typing import List, Optional
from collections import defaultdict
import logging

from app.config import get_settings, Settings
from app.knowledge.loader import load_knowledge, load_knowledge_units, SUBJECT_BY_FILE
import app.knowledge.search as search_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/knowledge", tags=["admin_knowledge"])

class UnitUpdateRequest(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    latex: Optional[str] = None

class ReviewRequest(BaseModel):
    unit_ids: List[str] = []
    relation_ids: List[str] = []
    action: str

def get_output_dir(settings: Settings) -> Path:
    return settings.knowledge_root / "output"

@router.get("/pending")
def get_pending_knowledge(settings: Settings = Depends(get_settings)):
    output_dir = get_output_dir(settings)
    pending_units = []
    pending_relations = []
    
    if output_dir.exists():
        for file_path in output_dir.glob("m1_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                units = data.get("units", [])
                relations = data.get("relations", [])
                
                for u in units:
                    if u.get("review_status") == "draft":
                        pending_units.append(u)
                        
                for r in relations:
                    if r.get("review_status") == "draft":
                        # Assign a composite id if it doesn't exist
                        if "id" not in r:
                            r["id"] = f"{r.get('source_unit_id')}_{r.get('target_unit_id')}_{r.get('relation_type')}"
                        pending_relations.append(r)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                
    return {"units": pending_units, "relations": pending_relations}

@router.put("/units/{unit_id}")
def update_unit(unit_id: str, payload: UnitUpdateRequest, settings: Settings = Depends(get_settings)):
    output_dir = get_output_dir(settings)
    
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
        
    for file_path in output_dir.glob("m1_*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            updated = False
            for u in data.get("units", []):
                if u.get("id") == unit_id:
                    if payload.content is not None:
                        u["content"] = payload.content
                    if payload.title is not None:
                        u["title"] = payload.title
                    if payload.latex is not None:
                        u["latex"] = payload.latex
                    updated = True
                    break
                    
            if updated:
                tmp_path = file_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                tmp_path.replace(file_path)
                return {"status": "success", "unit_id": unit_id}
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            
    raise HTTPException(status_code=404, detail="Unit not found")

@router.post("/review")
def review_knowledge(payload: ReviewRequest, settings: Settings = Depends(get_settings)):
    if payload.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    new_status = "active" if payload.action == "approve" else "rejected"
    
    output_dir = get_output_dir(settings)
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
        
    unit_ids_set = set(payload.unit_ids)
    relation_ids_set = set(payload.relation_ids)
    
    processed_units = 0
    processed_relations = 0
    
    for file_path in output_dir.glob("m1_*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            updated = False
            for u in data.get("units", []):
                if u.get("id") in unit_ids_set:
                    u["review_status"] = new_status
                    updated = True
                    processed_units += 1
            
            for r in data.get("relations", []):
                r_id = r.get("id") or f"{r.get('source_unit_id')}_{r.get('target_unit_id')}_{r.get('relation_type')}"
                if r_id in relation_ids_set:
                    r["review_status"] = new_status
                    updated = True
                    processed_relations += 1
                    
            if updated:
                tmp_path = file_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                tmp_path.replace(file_path)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            
    return {
        "status": "success",
        "action": payload.action,
        "processed_units": processed_units,
        "processed_relations": processed_relations
    }

@router.post("/publish")
def publish_knowledge(settings: Settings = Depends(get_settings)):
    output_dir = get_output_dir(settings)
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
        
    active_units = []
    active_relations = []
    
    for file_path in output_dir.glob("m1_*.json"):
        subject = SUBJECT_BY_FILE.get(file_path.name, "general")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for u in data.get("units", []):
                if u.get("review_status") == "active":
                    u_copy = dict(u)
                    u_copy["subject"] = subject
                    active_units.append(u_copy)
                    
            for r in data.get("relations", []):
                active_relations.append(dict(r))
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            
    # Filter relations to only keep those whose source and target are active
    active_unit_ids = {u["id"] for u in active_units}
    active_relations = [
        r for r in active_relations 
        if r.get("source_unit_id") in active_unit_ids and r.get("target_unit_id") in active_unit_ids
    ]
            
    pub_path = output_dir / "published_knowledge.json"
    graph_path = output_dir / "prerequisites_graph.json"
    embed_path = settings.knowledge_root / "embeddings.json"

    # Backup existing files
    if pub_path.exists() or graph_path.exists() or embed_path.exists():
        import datetime
        import shutil
        
        snapshot_dir = settings.repo_root / "data" / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"knowledge_snapshot_{timestamp}"
        snapshot_folder = snapshot_dir / snapshot_name
        snapshot_folder.mkdir(parents=True, exist_ok=True)
        
        if pub_path.exists():
            shutil.copy2(pub_path, snapshot_folder / "published_knowledge.json")
        if graph_path.exists():
            shutil.copy2(graph_path, snapshot_folder / "prerequisites_graph.json")
        if embed_path.exists():
            shutil.copy2(embed_path, snapshot_folder / "embeddings.json")
            
        shutil.make_archive(str(snapshot_dir / snapshot_name), 'zip', str(snapshot_folder))
        shutil.rmtree(snapshot_folder)
        logger.info(f"Created knowledge snapshot: {snapshot_name}.zip")

    pub_tmp = pub_path.with_suffix(".tmp")
    pub_data = {
        "units": active_units,
        "relations": active_relations
    }
    with open(pub_tmp, "w", encoding="utf-8") as f:
        json.dump(pub_data, f, ensure_ascii=False, indent=2)
    pub_tmp.replace(pub_path)
        
    graph = defaultdict(list)
    for r in active_relations:
        if r.get("relation_type") == "prereq":
            source = r.get("source_unit_id")
            target = r.get("target_unit_id")
            if source and target:
                graph[target].append(source)
                
    graph_path = output_dir / "prerequisites_graph.json"
    graph_tmp = graph_path.with_suffix(".tmp")
    with open(graph_tmp, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    graph_tmp.replace(graph_path)
        
    load_knowledge.cache_clear()
    load_knowledge_units.cache_clear()
    
    search_module.clear_vector_store_cache()
    
    return {
        "status": "success",
        "published_units": len(active_units),
        "published_relations": len(active_relations)
    }
