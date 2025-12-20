from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.config import settings

logger = logging.getLogger(__name__)
from app.routers import jobs, profile, matches, health, auth, insights, skills, admin, user_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting Career Agent API in {settings.environment} mode")
    yield
    # Shutdown
    print("Shutting down Career Agent API")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)

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


# Global exception handler to prevent internal error message leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler to prevent internal error details from leaking to clients.
    Logs the full error server-side while returning a generic message to the client.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# CORS - parse origins from settings (supports multiple origins for production)
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(user_jobs.router, prefix="/api/user-jobs", tags=["user-jobs"])


# Redoc HTML template with pinned CDN version
REDOC_HTML = """
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
    <script src="https://cdn.redoc.ly/redoc/v2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


# Custom Redoc endpoint with pinned CDN version
@app.get("/redoc", include_in_schema=False)
async def custom_redoc() -> HTMLResponse:
    """Custom Redoc documentation with pinned CDN version (v2.1.3)"""
    return HTMLResponse(content=REDOC_HTML)
