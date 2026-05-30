from fastapi import APIRouter
from pydantic import BaseModel

from app.math_tools.visualizer import VizType, generate_plot


router = APIRouter(prefix="/api", tags=["viz"])


class PlotRequest(BaseModel):
    viz_type: VizType
    params: dict = {}


from fastapi.responses import Response

@router.post("/viz/plot")
def create_plot_post(payload: PlotRequest):
    try:
        image_base64 = generate_plot(payload.viz_type, payload.params)
        return {"ok": True, "image": image_base64}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

@router.get("/viz/plot")
def create_plot_get(viz_type: str, expr: str = "x**2", a: float = 0, b: float = 2, mu: float = 0, sigma: float = 1):
    try:
        params = {"expr": expr, "a": a, "b": b, "mu": mu, "sigma": sigma}
        image_base64 = generate_plot(VizType(viz_type), params)
        import base64
        image_data = base64.b64decode(image_base64)
        return Response(content=image_data, media_type="image/png")
    except Exception as exc:
        return Response(content=str(exc).encode(), status_code=400)
