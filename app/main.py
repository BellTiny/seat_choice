from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.student import router as student_router
from app.core.config import settings
from app.core.database import init_database, SessionLocal
from app.services.selection import get_or_create_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    db = SessionLocal()
    try:
        get_or_create_settings(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Backend service for classroom seat selection driven by moral score ranking.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(student_router)


@app.get("/", summary="Health check")
def health_check() -> dict:
    return {"message": "Seat selection backend is running", "docs": "/docs", "openapi": "/openapi.json"}
