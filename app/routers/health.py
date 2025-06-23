from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app_name": settings.project_name,
        "version": settings.version
    }


@router.get("/ready")
async def readiness_check():
    """준비 상태 체크"""
    # 여기에 데이터베이스 연결 체크 등의 로직을 추가할 수 있습니다
    
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/live")
async def liveness_check():
    """생존 상태 체크"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    } 