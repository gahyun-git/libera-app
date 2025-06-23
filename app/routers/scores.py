"""
Score API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_async_db
from app.services.score_service import ScoreService
from app.utils.validation_utils import ScoreValidation, APIValidation
from app.core.constants import SuccessMessages, ErrorMessages
from app.schemas.scores import (
    SemesterScoresResponse,
    MainSubjectsResponse,
    AvailableSubjectsResponse,
)

router = APIRouter(
    prefix="/scores",
    tags=["scores"],
    responses={404: {"description": "성적 데이터를 찾을 수 없습니다"}}
)


@router.get("/students/{student_id}/semester/{grade}/{semester}", response_model=SemesterScoresResponse)
async def get_semester_scores_with_details(
    student_id: int,
    grade: int,
    semester: int,
    db: AsyncSession = Depends(get_async_db)
):
    """학기별 전과목 성적 + 세부사항 통합 조회"""
    
    # 유효성 검사
    ScoreValidation.validate_grade_semester(grade, semester)
    
    # 서비스 호출
    service = ScoreService(db)
    result = await service.get_semester_scores_with_details(student_id, grade, semester)
    
    # 빈 결과 체크
    APIValidation.check_empty_result(
        result["scores"], 
        ErrorMessages.no_semester_data(grade, semester)
    )
    
    # 응답 생성
    return SemesterScoresResponse(
        success=True,
        message=SuccessMessages.semester_scores_retrieved(grade, semester),
        **result
    )


@router.get("/students/{student_id}/main-subjects", response_model=MainSubjectsResponse)
async def get_main_subjects(
    student_id: int,
    target_subjects: Optional[List[str]] = Query(None, description="조회할 주요 과목"),
    db: AsyncSession = Depends(get_async_db)
):
    """주요 과목 성적 조회"""
    
    # 서비스 호출
    service = ScoreService(db)
    result = await service.get_main_subjects_flexible(student_id, target_subjects or [])
    
    # 빈 결과 체크
    APIValidation.check_empty_result(
        result["scores"], 
        ErrorMessages.NO_SCORE_DATA
    )
    
    # 응답 생성
    return MainSubjectsResponse(
        success=True,
        message=SuccessMessages.MAIN_SUBJECTS_RETRIEVED,
        **result
    )


@router.get("/students/{student_id}/available-subjects/{grade}/{semester}", response_model=AvailableSubjectsResponse)
async def get_available_subjects(
    student_id: int,
    grade: int,
    semester: int,
    db: AsyncSession = Depends(get_async_db)
):
    """해당 학기에 실제 수강한 과목 목록"""
    
    # 유효성 검사
    ScoreValidation.validate_grade_semester(grade, semester)
    
    # 서비스 호출
    service = ScoreService(db)
    result = await service.get_available_subjects(student_id, grade, semester)
    
    # 응답 생성
    return AvailableSubjectsResponse(
        success=True,
        message=SuccessMessages.subjects_retrieved(grade, semester),
        **result
    )


@router.get("/students/{student_id}/summary")
async def get_student_score_summary(
    student_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """학생의 전체 수강 과목 요약"""
    
    # 서비스 호출
    service = ScoreService(db)
    result = await service.get_student_score_summary(student_id)
    
    # 빈 결과 체크
    if result.get("total_subjects", 0) == 0:
        raise HTTPException(status_code=404, detail="성적 데이터가 없습니다.")
    
    # 응답 생성
    return {
        "success": True,
        "message": "성적 요약 조회 성공",
        "data": result
    }


# TODO: 과목별 성적 추이 분석 기능 추가 예정
# @router.get("/students/{student_id}/trends")
