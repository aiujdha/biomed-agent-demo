from fastapi import FastAPI

from app.api.routes.agent import router as agent_router
from app.api.routes.documents import router as documents_router
from app.api.routes.extract import router as extract_router
from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.core.config import settings
from app.core.errors import register_error_handlers

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Biomedical document retrieval, RAG query, structured trial extraction, and agent report workflow.",
)

register_error_handlers(app)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(extract_router)
app.include_router(agent_router)
