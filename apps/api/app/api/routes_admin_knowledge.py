from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
from pathlib import Path
from typing import List, Optional
import logging

from app.config import get_settings, Settings
from app.auth import get_principal, Principal

logger = logging.getLogger(__name__)


def legacy_staff(principal: Principal = Depends(get_principal)):
    if not principal.authenticated:
        raise HTTPException(401, "请以教师身份登录。")
    if not principal.is_teacher:
        raise HTTPException(403, "此入口仅供教师查看历史资料。")


def retired_write():
    raise HTTPException(
        410, "旧文件发布路径已停用；请通过课程候选审核发布版本化 Course Graph。"
    )


router = APIRouter(
    prefix="/api/admin/knowledge",
    tags=["admin_knowledge"],
    dependencies=[Depends(legacy_staff)],
)


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


@router.get("/list")
def get_knowledge_list(settings: Settings = Depends(get_settings)):
    output_dir = get_output_dir(settings)
    all_units = []
    all_relations = []

    if output_dir.exists():
        for file_path in output_dir.glob("m1_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                units = data.get("units", [])
                relations = data.get("relations", [])

                for u in units:
                    all_units.append(u)

                for r in relations:
                    # Assign a composite id if it doesn't exist
                    if "id" not in r:
                        r["id"] = (
                            f"{r.get('source_unit_id')}_{r.get('target_unit_id')}_{r.get('relation_type')}"
                        )
                    all_relations.append(r)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

    return {"units": all_units, "relations": all_relations}


@router.put("/units/{unit_id}", dependencies=[Depends(retired_write)])
def update_unit(unit_id: str, payload: UnitUpdateRequest):
    retired_write()


@router.post("/review", dependencies=[Depends(retired_write)])
def review_knowledge(payload: ReviewRequest):
    retired_write()


@router.post("/publish", dependencies=[Depends(retired_write)])
def publish_knowledge():
    retired_write()
