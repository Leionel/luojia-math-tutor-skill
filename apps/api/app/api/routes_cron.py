from fastapi import APIRouter
from app.agents.cron_agent import run_proactive_review_cron

router = APIRouter(prefix="/api/cron", tags=["cron"])

@router.post("/run")
async def trigger_cron():
    """Manually trigger the background proactive review cron."""
    result = await run_proactive_review_cron()
    return result
