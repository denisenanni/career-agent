from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import jobs, profile, matches, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting Career Agent API in {settings.environment} mode")
    yield
    # Shutdown
    print("Shutting down Career Agent API")


app = FastAPI(
    title="Career Agent API",
    description="AI-powered job hunting assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite + fallback
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
