"""
데이터 검증 유틸리티
"""

from typing import List, Dict, Any
from fastapi import HTTPException, status
from app.core.constants import ScoreConstants, ErrorMessages


class ScoreValidation:
    """성적 관련 검증"""
    
    @staticmethod
    def validate_grade(grade: int):
        """학년 유효성 검사"""
        if grade not in ScoreConstants.VALID_GRADES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.INVALID_GRADE
            )
    
    @staticmethod
    def validate_semester(semester: int):
        """학기 유효성 검사"""
        if semester not in ScoreConstants.VALID_SEMESTERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.INVALID_SEMESTER
            )
    
    @staticmethod
    def validate_grade_semester(grade: int, semester: int):
        """학년/학기 동시 검증"""
        ScoreValidation.validate_grade(grade)
        ScoreValidation.validate_semester(semester)
    
    @staticmethod
    def validate_periods(periods: List[Dict[str, int]]):
        """기간 목록 유효성 검사"""
        for period in periods:
            if "grade" not in period or "semester" not in period:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorMessages.INVALID_PERIOD_FORMAT
                )
            ScoreValidation.validate_grade_semester(period["grade"], period["semester"])


class APIValidation:
    """API 공통 검증"""
    
    @staticmethod
    def check_empty_result(data: Any, error_message: str):
        """결과가 비어있는지 체크하고 에러 발생"""
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            ) 