"""
기본 공통 스키마
"""
from typing import Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field, validator

T = TypeVar('T')

class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    success: bool = Field(True, description="요청 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")

class PaginatedResponse(BaseResponse, Generic[T]):
    """페이지네이션 응답 스키마"""
    data: List[T] = Field(..., description="데이터 목록")
    total: int = Field(..., description="전체 항목 수")
    page: int = Field(1, description="현재 페이지")
    size: int = Field(10, description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")

class GradeInfo(BaseModel):
    """학년 정보 스키마"""
    grade: int = Field(..., description="학년 (1, 2, 3)")
    
    @validator('grade')
    def validate_grade(cls, v):
        if not (1 <= v <= 3):
            raise ValueError('학년은 1-3 사이여야 합니다')
        return v

class SemesterInfo(BaseModel):
    """학기 정보 스키마"""
    semester: int = Field(..., description="학기 (1, 2)")
    
    @validator('semester')
    def validate_semester(cls, v):
        if not (1 <= v <= 2):
            raise ValueError('학기는 1-2 사이여야 합니다')
        return v

class PeriodInfo(GradeInfo, SemesterInfo):
    """학년+학기 정보 스키마"""
    pass

class OptionalPeriodInfo(BaseModel):
    """선택적 학년+학기 정보 스키마"""
    grade: Optional[int] = Field(None, description="학년 (1, 2, 3)")
    semester: Optional[int] = Field(None, description="학기 (1, 2)")
    
    @validator('grade')
    def validate_grade(cls, v):
        if v is not None and not (1 <= v <= 3):
            raise ValueError('학년은 1-3 사이여야 합니다')
        return v
    
    @validator('semester')
    def validate_semester(cls, v):
        if v is not None and not (1 <= v <= 2):
            raise ValueError('학기는 1-2 사이여야 합니다')
        return v

class FilterInfo(OptionalPeriodInfo):
    """필터 정보 스키마"""
    limit: Optional[int] = Field(None, description="조회 제한")
    offset: Optional[int] = Field(None, description="오프셋")

class StudentBasicInfo(BaseModel):
    """학생 기본 정보 스키마"""
    student_id: int = Field(..., description="학생 ID")
    student_name: str = Field(..., description="학생 이름")
    
class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    type: str = Field(..., description="에러 타입")
    message: str = Field(..., description="에러 메시지")
    field: Optional[str] = Field(None, description="관련 필드")

class ValidationError(BaseModel):
    """유효성 검사 에러"""
    errors: List[ErrorDetail] = Field(..., description="에러 목록")
