from typing import Any, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator

from app.auth import Principal, get_principal, require_role
from app.config import Settings
from app.knowledge.candidate_pipeline import build_candidates_from_document
from app.knowledge.course_service import get_course_service
from app.main_deps import get_app_settings, get_repository

router = APIRouter(prefix="/api/courses", tags=["courses"])

EventType = Literal[
    "attempt", "hint", "revision", "revision_success", "probe", "error"
]
# Events that assert an outcome and therefore change evidence counts.
OUTCOME_EVENT_TYPES = {"attempt", "revision", "revision_success", "probe", "error"}


class MatchRequest(BaseModel):
    query: str
    context: Optional[dict[str, Any]] = None


class CandidateCreateRequest(BaseModel):
    candidate_id: str
    candidate_type: str
    payload: dict[str, Any]
    proposed_by: str = "teacher"
    evidence_ref: Optional[str] = None


class CandidatesFromDocumentRequest(BaseModel):
    document_id: str


class ReviewCandidateRequest(BaseModel):
    action: str  # "approve" | "merge" | "reject" | "defer"
    reviewer_id: str = "teacher"
    review_note: str = ""
    merge_target_id: Optional[str] = None


class ProcessEventRequest(BaseModel):
    event_id: str
    unit_ids: list[str]
    case_id: Optional[str] = None
    event_type: EventType = "attempt"
    help_level: int = 0
    misconception_id: Optional[str] = None
    # Outcome fields have no defaults: an event that asserts an outcome must
    # state it explicitly instead of silently defaulting to success.
    is_independent: Optional[bool] = None
    is_success: Optional[bool] = None

    @model_validator(mode="after")
    def validate_outcome_fields(self):
        if self.event_type in OUTCOME_EVENT_TYPES and self.is_success is None:
            raise ValueError(
                f"is_success is required for event_type={self.event_type!r}"
            )
        if self.event_type in OUTCOME_EVENT_TYPES and self.is_independent is None:
            raise ValueError(
                f"is_independent is required for event_type={self.event_type!r}"
            )
        return self


@router.get("/{course_id}/graph")
def get_course_graph(
    course_id: str,
    scope: Optional[str] = Query(None, description="Filter by scope: core, prerequisite, extension"),
    student_id: Optional[str] = Query(None, description="Overlay student evidence"),
    format: str = Query("react_flow", description="react_flow or raw")
):
    service = get_course_service(course_id)
    overlay = None
    if student_id:
        overlay = service.overlay_store.get_course_overlay(student_id, course_id)

    if format == "raw":
        units = [
            {
                "id": u.id,
                "title": u.title,
                "type": u.type,
                "content": u.content,
                "scope": service.graph_repo.boundary_checker.get_scope_level(u.id).value,
                "difficulty": u.difficulty,
            }
            for u in service.graph_repo.units.values()
            if not scope or service.graph_repo.boundary_checker.get_scope_level(u.id).value == scope
        ]
        relations = [
            {
                "source": r.source_unit_id,
                "target": r.target_unit_id,
                "relation_type": r.relation_type,
            }
            for r in service.graph_repo.relations
        ]
        return {"course_id": course_id, "units": units, "relations": relations}

    return service.graph_repo.export_react_flow(student_overlay=overlay, scope_filter=scope)


@router.get("/{course_id}/graph/subgraph")
def get_course_subgraph(
    course_id: str,
    unit_id: str = Query(..., description="Center unit id"),
    depth: int = Query(1, ge=1, le=3),
    task_mode: Optional[str] = Query(None),
    allow_extension: bool = Query(True)
):
    service = get_course_service(course_id)
    if unit_id not in service.graph_repo.units:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")

    units, relations = service.graph_repo.get_subgraph(
        center_unit_ids=[unit_id],
        max_depth=depth,
        task_mode=task_mode,
        allow_extension=allow_extension,
    )
    return {
        "center_unit_id": unit_id,
        "units": [
            {
                "id": u.id,
                "title": u.title,
                "type": u.type,
                "scope": service.graph_repo.boundary_checker.get_scope_level(u.id).value,
            }
            for u in units
        ],
        "relations": [
            {
                "source": r.source_unit_id,
                "target": r.target_unit_id,
                "relation_type": r.relation_type,
            }
            for r in relations
        ],
    }


@router.get("/{course_id}/cases")
def list_cases(
    course_id: str,
    task_type: Optional[str] = Query(None),
    concept_id: Optional[str] = Query(None)
):
    service = get_course_service(course_id)
    if concept_id:
        cases = service.graph_repo.case_repo.find_by_concept(concept_id)
    else:
        cases = service.graph_repo.case_repo.list_cases(course_id=course_id, task_type=task_type)
    return {"cases": [c.to_dict() for c in cases], "total": len(cases)}


@router.post("/{course_id}/cases/match")
def match_case(course_id: str, payload: MatchRequest):
    service = get_course_service(course_id)
    result = service.case_matcher.match(
        query=payload.query,
        course_id=course_id,
        context=payload.context or {}
    )
    return result.to_dict()


@router.get("/{course_id}/candidates")
def list_candidates(course_id: str, status: Optional[str] = Query(None)):
    service = get_course_service(course_id)
    candidates = service.candidate_mgr.list_candidates(course_id=course_id, status=status)
    return {"candidates": [c.to_dict() for c in candidates], "total": len(candidates)}


@router.post("/{course_id}/candidates")
def create_candidate(
    course_id: str,
    payload: CandidateCreateRequest,
    principal: Principal = Depends(get_principal),
):
    require_role(principal, ("teacher", "admin"), get_app_settings())
    service = get_course_service(course_id)
    candidate = service.candidate_mgr.add_candidate(
        candidate_id=payload.candidate_id,
        candidate_type=payload.candidate_type,
        course_id=course_id,
        payload=payload.payload,
        proposed_by=payload.proposed_by,
        evidence_ref=payload.evidence_ref,
    )
    return {"status": "created", "candidate": candidate.to_dict()}


@router.post("/{course_id}/candidates/from-document")
def create_candidates_from_document(
    course_id: str,
    payload: CandidatesFromDocumentRequest,
    principal: Principal = Depends(get_principal),
    repo=Depends(get_repository),
):
    require_role(principal, ("teacher", "admin"), get_app_settings())
    service = get_course_service(course_id)

    doc = repo.get_document(payload.document_id, principal.user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document was not found.")
    chunks = repo.list_document_chunks(payload.document_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="该文档尚未完成解析，稍后再试。")

    proposals = build_candidates_from_document(
        payload.document_id,
        doc["filename"],
        "\n".join(chunks),
    )
    created = []
    for proposal in proposals:
        candidate = service.candidate_mgr.add_candidate(
            candidate_id=proposal["candidate_id"],
            candidate_type=proposal["candidate_type"],
            course_id=course_id,
            payload=proposal["payload"],
            proposed_by=proposal["proposed_by"],
            evidence_ref=proposal["evidence_ref"],
        )
        created.append(candidate.to_dict())
    return {"status": "created", "total": len(created), "candidates": created}


@router.post("/{course_id}/candidates/{candidate_id}/review")
def review_candidate(
    course_id: str,
    candidate_id: str,
    payload: ReviewCandidateRequest,
    principal: Principal = Depends(get_principal),
):
    require_role(principal, ("teacher", "admin"), get_app_settings())
    service = get_course_service(course_id)
    try:
        result = service.review_service.review_candidate(
            candidate_id=candidate_id,
            action=payload.action,
            reviewer_id=principal.user_id if principal.authenticated else payload.reviewer_id,
            review_note=payload.review_note,
            merge_target_id=payload.merge_target_id,
        )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{course_id}/revisions")
def list_revisions(course_id: str):
    service = get_course_service(course_id)
    revisions = service.store.list_revisions(course_id)
    return {"revisions": revisions, "total": len(revisions)}


@router.get("/users/{user_id}/{course_id}/overlay")
def get_student_overlay(user_id: str, course_id: str):
    service = get_course_service(course_id)
    return service.overlay_store.get_course_overlay(student_id=user_id, course_id=course_id)


@router.post("/users/{user_id}/{course_id}/events")
def record_student_event(
    user_id: str,
    course_id: str,
    payload: ProcessEventRequest,
    principal: Principal = Depends(get_principal),
):
    require_role(principal, ("student", "teacher", "admin"), get_app_settings())
    service = get_course_service(course_id)
    result = service.overlay_store.record_process_event(
        event_id=payload.event_id,
        student_id=user_id,
        course_id=course_id,
        unit_ids=payload.unit_ids,
        case_id=payload.case_id,
        event_type=payload.event_type,
        is_independent=payload.is_independent,
        is_success=payload.is_success,
        help_level=payload.help_level,
        misconception_id=payload.misconception_id,
    )
    if result.get("status") == "duplicate":
        return {"status": "duplicate", "event_id": payload.event_id}
    return {"status": "success", "event_id": payload.event_id}
