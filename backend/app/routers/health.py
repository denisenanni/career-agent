from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "career-agent-api"}


@router.get("/", include_in_schema=False)
async def root():
    return {"message": "Career Agent API", "docs": "/docs"}
