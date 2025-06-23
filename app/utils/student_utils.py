"""
Student 관련 유틸리티 static 함수들
"""
from typing import Optional
from datetime import date, datetime


class StudentUtils:
    """학생 관련 유틸리티"""
    
    @staticmethod
    def format_birth_date(birth_date: Optional[date]) -> Optional[str]:
        """생년월일 포맷팅"""
        return birth_date.isoformat() if birth_date else None
    
    @staticmethod
    def format_datetime(dt: Optional[datetime]) -> Optional[str]:
        """날짜시간 포맷팅"""
        return dt.isoformat() if dt else None
    
    @staticmethod
    def normalize_gender(gender: Optional[str]) -> str:
        """성별 정규화"""
        if not gender:
            return "기타"
        return gender if gender in ["M", "F"] else "기타"
    
    @staticmethod
    def get_default_school_name() -> str:
        """기본 학교명"""
        return "Unknown"