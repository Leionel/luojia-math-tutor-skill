from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="Luojia Math Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(models_router)
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
