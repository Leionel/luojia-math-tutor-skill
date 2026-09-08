from fastapi import APIRouter, Depends

from app.auth import Principal, get_principal
from app.main_deps import get_repository
from app.memory.repository import Repository
from app.observability import current_request_id


router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/metrics")
def metrics(
    _principal: Principal = Depends(get_principal),
    repo: Repository = Depends(get_repository),
):
    return {
        "request_id": current_request_id(),
        "routes": repo.request_metrics_summary(),
    }
