from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.database import init_db, close_db
from app.api import auth, users
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/users/docs",
    redoc_url="/api/users/redoc",
    lifespan=lifespan,
)

@app.get("/api/users/health")
async def health():
    return {"status": "ok", "service": settings.app_name}

app.include_router(auth.router)
app.include_router(users.router)
