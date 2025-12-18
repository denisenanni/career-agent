from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import jobs, profile, matches, health, auth, insights, skills


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting Career Agent API in {settings.environment} mode")
    yield
    # Shutdown
    print("Shutting down Career Agent API")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Career Agent API",
    description="AI-powered job hunting assistant",
    version="0.1.0",
    lifespan=lifespan,
    # Disable default redoc (we'll create a custom one)
    redoc_url=None,
)

# Add rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])


# Custom Redoc endpoint with working CDN
@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """Custom Redoc documentation with working CDN URL"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Career Agent API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url="/openapi.json"></redoc>
        <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
