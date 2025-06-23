"""
학생 정보 API
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_async_db
from app.services.student_service import StudentService
from app.schemas.base import BaseResponse

router = APIRouter(
    prefix="/students",
    tags=["students"],
    responses={404: {"description": "학생을 찾을 수 없습니다"}}
)


@router.get("")
async def list_students(
    name: Optional[str] = Query(None, description="이름 검색"),
    school: Optional[str] = Query(None, description="학교명 검색"),
    grade: Optional[int] = Query(None, description="학년 필터"),
    search: Optional[str] = Query(None, description="통합 검색 키워드"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db)
):
    """학생 목록 조회"""
    
    service = StudentService(db)
    
    # 통합 검색인지 일반 필터링인지 구분
    if search:
        # 통합 검색 수행
        try:
            result = await service.advanced_search(
                keyword=search,
                search_fields=["name"],
                limit=limit
            )
        except Exception:
            result = {"students": [], "total": 0}
    else:
        # 일반 필터링
        result = await service.list_students(
            name=name,
            school=school,
            grade=grade,
            limit=limit,
            offset=offset
        )
    
    # 실제 학생 목록 데이터 반환
    return {
        "total": result.get("total", result.get("total_matches", 0)) if isinstance(result, dict) else len(result) if result else 0,
        "limit": limit,
        "offset": offset,
        "students": result.get("students", []) if isinstance(result, dict) else result or [],
        "filters": {
            "name": name,
            "school": school,
            "grade": grade,
            "search": search
        }
    }


@router.get("/stats")
async def get_students_statistics(db: AsyncSession = Depends(get_async_db)):
    """학생 통계 조회"""
    
    service = StudentService(db)
    stats = await service.get_student_statistics()
    
    return {"statistics": stats}


@router.get("/{student_id:int}")
async def get_student(
    student_id: int,
    include_scores: bool = Query(False, description="성적 정보 포함"),
    include_attendance: bool = Query(False, description="출결 정보 포함"),
    include_details: bool = Query(False, description="세부사항 포함"),
    db: AsyncSession = Depends(get_async_db)
):
    """개별 학생 조회"""
    service = StudentService(db)
    
    try:
        result = await service.get_student_detailed_profile(
            student_id=student_id,
            include_scores=include_scores,
            include_attendance=include_attendance,
            include_details=include_details
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{student_id:int}/profile")
async def get_student_complete_profile(
    student_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """학생 프로필 전체 조회"""
    service = StudentService(db)
    complete_profile = await service.get_complete_profile(student_id)
    
    if "error" in complete_profile:
        raise HTTPException(status_code=404, detail=complete_profile["error"])
    
    return complete_profile


 