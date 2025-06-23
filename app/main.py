    
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.base import create_tables
from app.routers import health, students, pdf, scores

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 테이블 생성
    await create_tables()
    yield
    # 종료 시 정리 작업 (필요한 경우)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="학생 성적 관리 시스템",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router)
app.include_router(students.router)
app.include_router(pdf.router)
app.include_router(scores.router)

@app.get("/")
async def root():
    return {
        "message": "Libera 생기부 프로젝트",
        "version": settings.version,
        "features": [
        ]
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "libera-app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 