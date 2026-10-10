"""
NILA — AI-Powered Festival Mobility & Crowd Management System
Main Application Entry Point (FastAPI)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.health import router as health_router
from backend.api.routes import router as routes_router
from backend.api.festivals import router as festivals_router
from backend.api.optimize import router as optimize_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend service for NILA festival crowd prediction, fixed-fleet optimization, and mobility routing.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_router, prefix=settings.API_V1_PREFIX)
app.include_router(festivals_router, prefix=settings.API_V1_PREFIX)
app.include_router(optimize_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
