"""Owner-scoped exploration adapter over the existing learning record store."""

from fastapi import APIRouter, Depends, HTTPException
from app.auth import Principal, get_principal
from app.main_deps import get_learning_workspace
from app.tutor.help_boundary import assert_reference_help_allowed
from app.tutor.learning_workspace import digest
from app.tutor.explorations import (
    Explorations,
    Create,
    Revise,
    EditGraph,
    RestoreGraph,
    Execute,
    proposal,
    KIND,
)

router = APIRouter(prefix="/api/explorations", tags=["explorations"])


def owner(principal: Principal = Depends(get_principal)):
    if not principal.authenticated:
        raise HTTPException(401, "请先登录保存私人探索。")
    return principal.user_id


def invoke(action):
    try:
        return action()
    except KeyError as exc:
        raise HTTPException(404, "探索或引用不存在，或不属于当前账号。") from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ArithmeticError as exc:
        raise HTTPException(422, "计算无法完成，请检查矩阵与数值预算。") from exc


@router.get("")
def listing(user=Depends(owner), workspace=Depends(get_learning_workspace)):
    values = workspace.store.learning_records(user, workspace.course_id, KIND)
    return {
        "items": [
            {
                k: v[k]
                for k in ("id", "title", "revision", "updated_at", "help_exposure")
            }
            for v in reversed(values)
        ]
    }


@router.get("/proposal")
def proposed(user=Depends(owner), workspace=Depends(get_learning_workspace)):
    invoke(lambda: assert_reference_help_allowed(user, workspace.course))
    return proposal()


@router.get("/sources")
def sources(user=Depends(owner), workspace=Depends(get_learning_workspace)):
    invoke(lambda: assert_reference_help_allowed(user, workspace.course))
    saved = workspace.store.load_graph(workspace.course_id) or {}
    revision = workspace.revision()
    return {
        "course": [
            {
                "title": u["title"],
                "ref": {
                    "kind": "course",
                    "unit_id": u["id"],
                    "graph_revision": revision,
                },
            }
            for u in saved.get("data", {}).get("units", [])
        ],
        "notes": [
            {
                "title": n["subject"],
                "ref": {
                    "kind": "note",
                    "note_id": n["id"],
                    "source_hash": digest(n["content"]),
                },
            }
            for n in workspace.repository.list_notes(user)[:100]
        ],
        "documents": workspace.repository.list_documents(user)[:100],
    }


@router.post("", status_code=201)
def create(
    body: Create, user=Depends(owner), workspace=Depends(get_learning_workspace)
):
    return invoke(lambda: Explorations(workspace).create(user, body))


@router.get("/{id}")
def read(id: str, user=Depends(owner), workspace=Depends(get_learning_workspace)):
    return invoke(
        lambda: Explorations(workspace).view(
            user, Explorations(workspace).get(user, id)
        )
    )


@router.post("/{id}/claim")
def revise(
    id: str,
    body: Revise,
    user=Depends(owner),
    workspace=Depends(get_learning_workspace),
):
    return invoke(lambda: Explorations(workspace).update(user, id, "revise", body))


@router.post("/{id}/graph")
def graph(
    id: str,
    body: EditGraph,
    user=Depends(owner),
    workspace=Depends(get_learning_workspace),
):
    return invoke(lambda: Explorations(workspace).update(user, id, "graph", body))


@router.post("/{id}/restore-graph")
def restore(
    id: str,
    body: RestoreGraph,
    user=Depends(owner),
    workspace=Depends(get_learning_workspace),
):
    return invoke(
        lambda: Explorations(workspace).update(user, id, "restore_graph", body)
    )


@router.post("/{id}/runs")
def run(
    id: str,
    body: Execute,
    user=Depends(owner),
    workspace=Depends(get_learning_workspace),
):
    return invoke(lambda: Explorations(workspace).update(user, id, "run", body))
