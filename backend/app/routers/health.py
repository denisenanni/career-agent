from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "career-agent-api"}


@router.get("/")
async def root():
    return {"message": "Career Agent API", "docs": "/docs"}
