"""
학생 관련 Pydantic 스키마
"""
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from pydantic import BaseModel, Field, validator

from .base import BaseResponse
from app.schemas.converters import StudentConverter


class StudentBase(BaseModel):
    """학생 기본 스키마"""
    name: Optional[str] = Field(None, max_length=50)
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=200)
    current_school_name: Optional[str] = Field(None, max_length=100)
    current_class_info: Optional[str] = Field(None, max_length=50)

    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    """학생 생성 스키마"""
    name: str = Field(..., max_length=50)
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=200)
    current_school_name: Optional[str] = Field(None, max_length=100)
    current_class_info: Optional[str] = Field(None, max_length=50)


class StudentUpdate(StudentBase):
    """학생 수정 스키마"""
    pass


class StudentResponse(StudentBase):
    """학생 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentSummary(BaseModel):
    """학생 요약 정보 (딕셔너리 호환)"""
    id: int
    name: str
    birth_date: Optional[str] = None  # ISO 형식 문자열
    gender: Optional[str] = None
    current_school_name: Optional[str] = None
    has_scores: bool = False
    has_attendance: bool = False

    @validator('name')
    def validate_name(cls, v):
        return v or "Unknown"


class StudentBasicInfo(BaseModel):
    """학생 기본 정보 (딕셔너리 호환)"""
    id: int
    name: str
    birth_date: Optional[str] = None  # ISO 형식 문자열
    gender: Optional[str] = None
    address: Optional[str] = None
    current_school_name: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        return v or "Unknown"


class StudentListResponse(BaseResponse):
    """학생 목록 응답"""
    total: int
    limit: int
    offset: int
    students: List[Dict[str, Any]]  # 딕셔너리 형태로 수용
    filters: Dict[str, Any]


class DataCompleteness(BaseModel):
    """데이터 완성도"""
    with_scores: int
    with_attendance: int
    with_academic_details: int
    with_school_history: int
    complete_profile: int


class TotalStatistics(BaseModel):
    """전체 통계"""
    total_students: int
    data_completeness: DataCompleteness


class DataCoverage(BaseModel):
    """데이터 커버리지"""
    scores_coverage: float
    attendance_coverage: float
    details_coverage: float
    history_coverage: float


class StudentStatisticsResponse(BaseResponse):
    """학생 통계 응답"""
    total_statistics: TotalStatistics
    by_school: Dict[str, int]
    by_grade: Dict[int, int]
    by_gender: Dict[str, int]
    data_coverage: DataCoverage


class SearchCriteria(BaseModel):
    """검색 조건"""
    keyword: str
    search_fields: List[str]
    grade_range: List[Optional[int]]
    has_scores: Optional[bool]
    has_attendance: Optional[bool]
    limit: int


class StudentSearchResult(BaseModel):
    """학생 검색 결과"""
    id: int
    name: str
    birth_date: Optional[str] = None  # ISO 형식
    gender: Optional[str] = None
    current_school_name: Optional[str] = None
    scores_count: int
    attendance_count: int


class StudentSearchResponse(BaseModel):
    """학생 검색 응답"""
    keyword: str
    total_matches: int
    students: List[Dict[str, Any]]  # 딕셔너리 형태로 수용
    search_criteria: Dict[str, Any]  # 딕셔너리 형태로 수용


class ScoreInfo(BaseModel):
    """성적 정보"""
    id: int
    grade: int
    semester: int
    subject: str
    raw_score: Optional[float] = None
    achievement_level: Optional[str] = None


class ScoreData(BaseModel):
    """성적 데이터"""
    total_records: int
    latest: List[Dict[str, Any]]  # 딕셔너리 형태로 수용


class AttendanceSummary(BaseModel):
    """출결 요약"""
    total_absence: int
    total_tardiness: int
    total_early_leave: int


class AttendanceData(BaseModel):
    """출결 데이터"""
    total_records: int
    summary: Optional[AttendanceSummary] = None


class AcademicDetailInfo(BaseModel):
    """세부사항 정보"""
    id: int
    grade: int
    semester: int
    detail_data: Dict[str, Any]


class AcademicDetailData(BaseModel):
    """세부사항 데이터"""
    total_records: int
    latest: Optional[Dict[str, Any]] = None  # 딕셔너리 형태로 수용


class StudentProfileResponse(BaseModel):
    """학생 프로필 응답"""
    student_id: int
    basic_info: Dict[str, Any]  # 딕셔너리 형태로 수용
    scores: Optional[ScoreData] = None
    attendance: Optional[AttendanceData] = None
    academic_details: Optional[AcademicDetailData] = None


class ScoreRecord(BaseModel):
    """성적 레코드"""
    id: int
    grade: int
    semester: int
    subject: str
    raw_score: Optional[float] = None
    achievement_level: Optional[str] = None
    subject_average: Optional[float] = None
    grade_rank: Optional[str] = None


class CompleteScoreData(BaseModel):
    """완전한 성적 데이터"""
    total_records: int
    records: List[Dict[str, Any]]  # 딕셔너리 형태로 수용


class AttendanceRecord(BaseModel):
    """출결 레코드"""
    id: int
    grade: int
    semester: int
    absence_disease: int
    absence_unexcused: int
    tardiness_disease: int
    tardiness_unexcused: int


class CompleteAttendanceData(BaseModel):
    """완전한 출결 데이터"""
    total_records: int
    records: List[Dict[str, Any]]  # 딕셔너리 형태로 수용
    summary: AttendanceSummary


class AcademicDetailRecord(BaseModel):
    """세부사항 레코드"""
    id: int
    grade: int
    semester: int
    detail_data: Dict[str, Any]


class CompleteAcademicDetailData(BaseModel):
    """완전한 세부사항 데이터"""
    total_records: int
    records: List[Dict[str, Any]]  # 딕셔너리 형태로 수용


class SchoolHistoryRecord(BaseModel):
    """학교 이력 레코드"""
    id: int
    grade: int
    school_name: str
    start_date: Optional[str] = None  # ISO 형식
    end_date: Optional[str] = None    # ISO 형식


class SchoolHistoryData(BaseModel):
    """학교 이력 데이터"""
    total_records: int
    records: List[Dict[str, Any]]  # 딕셔너리 형태로 수용
    current_school: Optional[str] = None


class StudentCompleteProfileResponse(BaseModel):
    """학생 완전한 프로필 응답"""
    student_id: int
    basic_info: Dict[str, Any]  # 딕셔너리 형태로 수용
    scores: Dict[str, Any]      # 딕셔너리 형태로 수용
    attendance: Dict[str, Any]  # 딕셔너리 형태로 수용
    academic_details: Dict[str, Any]  # 딕셔너리 형태로 수용
    school_history: Dict[str, Any]    # 딕셔너리 형태로 수용


# SQLAlchemy 모델과 호환되는 변환 함수들
def student_to_dict(student) -> Dict[str, Any]:
    """SQLAlchemy Student 객체를 딕셔너리로 변환"""
    return {
        "id": student.id,
        "name": student.name or "Unknown",
        "birth_date": student.birth_date.isoformat() if student.birth_date is not None else None,
        "gender": student.gender,
        "address": student.address,
        "current_school_name": student.current_school_name,
        "current_class_info": student.current_class_info,
        "created_at": student.created_at.isoformat() if student.created_at is not None else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at is not None else None
    }


def student_summary_dict(student, has_scores: bool = False, has_attendance: bool = False) -> Dict[str, Any]:
    """학생 요약 정보 딕셔너리 생성 - 하위 호환성을 위해 유지"""
    result = StudentConverter.to_search_result(student, 0, 0)
    result["has_scores"] = has_scores
    result["has_attendance"] = has_attendance
    return result


def student_search_result_dict(student, scores_count: int = 0, attendance_count: int = 0) -> Dict[str, Any]:
    """학생 검색 결과 딕셔너리 생성 - 하위 호환성을 위해 유지"""
    return StudentConverter.to_search_result(student, scores_count, attendance_count)


# 기존 호환성을 위한 스키마들
class PDFMetadataResponse(BaseModel):
    """PDF 메타데이터 응답"""
    id: int
    original_filename: str
    file_hash: str
    file_size: int
    page_count: int
    upload_timestamp: datetime
    processed_at: datetime
    processing_version: str
    
    class Config:
        from_attributes = True


class StudentWithPDFResponse(StudentResponse):
    """PDF 정보가 포함된 학생 응답"""
    pdf_metadata: Optional[PDFMetadataResponse] = None 