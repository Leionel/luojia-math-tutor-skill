from fastapi import APIRouter, Depends
from app.agents.cron_agent import run_proactive_review_cron
from app.auth import get_principal

router = APIRouter(
    prefix="/api/cron",
    tags=["cron"],
    dependencies=[Depends(get_principal)],
)

@router.post("/run")
async def trigger_cron():
    """Manually trigger the background proactive review cron."""
    result = await run_proactive_review_cron()
    return result
