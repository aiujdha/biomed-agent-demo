from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Biomedical RAG and Agent workflow demo.",
)

app.include_router(health_router)
