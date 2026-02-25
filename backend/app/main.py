"""IaaS Backend - FastAPI application."""

from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.projects.routes import router as projects_router
from app.users.routes import router as users_router

app = FastAPI(title="IaaS API", version="0.1.0")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.get("/health")
def health():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "ok"}
