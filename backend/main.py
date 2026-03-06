# Step 13: FastAPI app entry
# backend/main.py
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.api.routes import agents, auth, billing, events
from backend.db.database import engine
from backend.db.models import Base
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables (safe — won't drop existing data)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(title="OpenClaw API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        settings.FRONTEND_URL,   # production URL when deployed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(billing.router)
app.include_router(events.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "status": "running",
        "service": "OpenClaw API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "alive", "service": "OpenClaw"}
