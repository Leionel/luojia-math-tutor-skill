from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio

# Fix for Windows uvicorn exit code -1073741510 during reload
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.routes_exercises import router as exercises_router
from app.api.routes_mastery import router as mastery_router
from app.api.routes_mistakes import router as mistakes_router
from app.api.routes_models import router as models_router
from app.api.routes_sessions import router as sessions_router
from app.api.routes_tutor import router as tutor_router
from app.api.routes_viz import router as viz_router
from app.api.routes_notes import router as notes_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_resources import router as resources_router
from app.api.routes_cron import router as cron_router
from app.api.routes_admin_knowledge import router as admin_knowledge_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_courses import router as courses_router
from app.api.routes_auth import router as auth_router
from app.api.routes_observability import router as observability_router
from app.config import get_settings
from app.main_deps import get_orchestrator
from app.observability import request_observability_middleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.validate_runtime()
    orchestrator = get_orchestrator()
    await orchestrator.workflow_owner.start_background_worker()
    try:
        yield
    finally:
        await orchestrator.workflow_owner.stop_background_worker()


settings = get_settings()
settings.validate_runtime()
app = FastAPI(
    title="Luojia Math Tutor API",
    version="0.2.0",
    lifespan=lifespan,
)
app.middleware("http")(request_observability_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Luojia-LLM-Key"],
)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(models_router)
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(tutor_router)
app.include_router(exercises_router)
app.include_router(viz_router)
app.include_router(uploads_router)
app.include_router(mistakes_router)
app.include_router(mastery_router)
app.include_router(resources_router)
app.include_router(notes_router)
app.include_router(cron_router)
app.include_router(admin_knowledge_router)
app.include_router(knowledge_router)
app.include_router(courses_router)
app.include_router(observability_router)
