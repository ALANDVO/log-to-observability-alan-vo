import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.architecture import router as architecture_router
from app.api.observability import router as observability_router
from app.api.auth import router as auth_router
from app.api.evaluation import router as evaluation_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    yield

def create_app() -> FastAPI:
    settings.validate_production_safety()

    application = FastAPI(
        title="Log to Observability Pipeline",
        description="Auto-detects service architectures and generates Grafana dashboards, alert rules, and SLOs from log patterns.",
        version=settings.app_version,
        lifespan=lifespan
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Routers
    application.include_router(auth_router)
    application.include_router(architecture_router)
    application.include_router(observability_router)
    application.include_router(evaluation_router)

    @application.get("/api/health", tags=["system"])
    def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "demo_mode": settings.demo_mode
        }

    @application.get("/api/stats", tags=["system"])
    def stats():
        return {
            "version": settings.app_version,
            "llm_provider": settings.llm_provider,
            "llm_configured": bool(settings.llm_api_key) or settings.llm_provider == "ollama",
            "demo_mode": settings.demo_mode
        }

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Prevent leaking raw error stack traces
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."}
        )

    return application

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
