"""
PDF 처리 설정 관리자
"""
from typing import Set
from pathlib import Path


class PDFConfig:
    """PDF 처리 관련 설정값들"""
    
    # 파일 제한
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.pdf'}
    
    # 처리 설정
    DEFAULT_GRADE = 1
    DEFAULT_SEMESTER = 1
    UNKNOWN_STUDENT_NAME = "Unknown"
    
    # 데이터베이스 필드 길이 제한
    FIELD_LIMITS = {
        "student_name": 50,
        "gender": 10, 
        "address": 200,
        "curriculum": 20,
        "subject": 50,
        "subject_type": 20,
        "original_subject_name": 100,
        "score_fields": 20,  # raw_score, subject_average, etc.
        "count_fields": 10   # student_count, grade_rank
    }
    
    # 날짜 형식
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y년 %m월 %d일"
    ]
    
    # 추출 방법
    EXTRACTION_METHODS = {
        "PDF_PARSER": "pdf_parser",
        "FALLBACK": "fallback",
        "MOCK": "mock_extraction"
    }
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """파일 확장자 검증"""
        if not filename:
            return False
        ext = Path(filename).suffix.lower()
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_file_size(cls, size: int) -> bool:
        """파일 크기 검증"""
        return size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def get_field_limit(cls, field_name: str) -> int:
        """필드별 길이 제한 반환"""
        return cls.FIELD_LIMITS.get(field_name, 255) 