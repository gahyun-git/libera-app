"""
Score schemas - 성적 스키마
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .base import PeriodInfo, BaseResponse, StudentBasicInfo


class ScoreBase(PeriodInfo):
    """성적 기본 스키마"""
    curriculum: str = Field(..., description="교과")
    subject: str = Field(..., description="과목명")
    subject_type: Optional[str] = Field(None, description="과목 유형")
    original_subject_name: Optional[str] = Field(None, description="원본 과목명")
    raw_score: Optional[str] = Field(None, description="원점수")
    subject_average: Optional[str] = Field(None, description="과목평균")
    standard_deviation: Optional[str] = Field(None, description="표준편차")
    achievement_level: Optional[str] = Field(None, description="성취도")
    student_count: Optional[str] = Field(None, description="수강자수")
    grade_rank: Optional[str] = Field(None, description="석차등급")
    credit_hours: Optional[int] = Field(None, description="단위수")


class ScoreCreate(ScoreBase):
    """성적 생성 스키마"""
    student_id: int = Field(..., description="학생 ID")


class ScoreUpdate(BaseModel):
    """성적 수정 스키마"""
    achievement_level: Optional[str] = Field(None, description="성취도")
    raw_score: Optional[str] = Field(None, description="원점수")
    subject_average: Optional[str] = Field(None, description="과목평균")
    standard_deviation: Optional[str] = Field(None, description="표준편차")
    student_count: Optional[str] = Field(None, description="수강자수")
    grade_rank: Optional[str] = Field(None, description="석차등급")
    credit_hours: Optional[int] = Field(None, description="단위수")


class ScoreResponse(ScoreBase):
    """성적 응답 스키마"""
    id: int = Field(..., description="성적 ID")
    student_id: int = Field(..., description="학생 ID")
    
    class Config:
        from_attributes = True


class SemesterScoresResponse(BaseResponse, StudentBasicInfo, PeriodInfo):
    """학기별 성적 응답 스키마"""
    scores: List[ScoreResponse] = Field(..., description="성적 목록")
    academic_details: Optional[Dict[str, Any]] = Field(None, description="세부사항")
    summary: Dict[str, Any] = Field(..., description="학기 요약")


class SubjectTrendsResponse(BaseResponse, StudentBasicInfo):
    """과목별 성적 추이 응답 스키마"""
    requested_subjects: List[str] = Field(..., description="요청된 과목 목록")
    trends: Dict[str, List[Dict[str, Any]]] = Field(..., description="과목별 추이 데이터")
    analysis_summary: Dict[str, Any] = Field(..., description="분석 요약")


class MainSubjectsResponse(BaseResponse, StudentBasicInfo):
    """주요 과목 성적 응답 스키마"""
    target_subjects: List[str] = Field(..., description="대상 과목 목록")
    scores: List[Dict[str, Any]] = Field(..., description="성적 데이터")
    summary: Dict[str, Any] = Field(..., description="요약 정보")


class SemesterComparisonResponse(BaseResponse, StudentBasicInfo):
    """학기별 성적 비교 응답 스키마"""
    comparison_periods: List[Dict[str, int]] = Field(..., description="비교 기간")
    comparison_data: Dict[str, Any] = Field(..., description="비교 데이터")
    summary: Dict[str, Any] = Field(..., description="비교 요약")


class AvailableSubjectsResponse(BaseResponse, StudentBasicInfo, PeriodInfo):
    """수강 과목 목록 응답 스키마"""
    period: str = Field(..., description="학기 정보")
    available_subjects: List[str] = Field(..., description="수강 가능 과목")
    total_count: int = Field(..., description="총 과목 수")
    main_subjects: List[str] = Field(..., description="주요 과목")
    other_subjects: List[str] = Field(..., description="기타 과목")


class StudentScoreSummaryResponse(BaseResponse, StudentBasicInfo):
    """학생 성적 요약 응답 스키마"""
    student_summary: Dict[str, Any] = Field(..., description="학생 성적 요약")


class FlexibleScoreQueryResponse(BaseResponse, StudentBasicInfo):
    """유연한 성적 조회 응답 스키마"""
    query_conditions: Dict[str, Any] = Field(..., description="조회 조건")
    student_summary: Dict[str, Any] = Field(..., description="학생 요약")
    semester_data: Optional[Dict[str, Any]] = Field(None, description="학기별 데이터")
    subject_trends: Optional[Dict[str, Any]] = Field(None, description="과목별 추이")


class SubjectInfo(BaseModel):
    """과목 정보 스키마"""
    curriculum: str = Field(..., description="교과")
    subject: str = Field(..., description="과목명")
    score: Optional[float] = Field(None, description="점수")
    achievement_level: Optional[str] = Field(None, description="성취도")


class ScoreStatisticsResponse(BaseModel):
    """성적 통계 응답 스키마"""
    total_records: int = Field(..., description="총 레코드 수")
    student_count: int = Field(..., description="학생 수")
    subject_count: int = Field(..., description="과목 수")
    average_score: float = Field(..., description="평균 점수")
    score_distribution: Dict[str, int] = Field(..., description="점수 분포")
    grade_distribution: Dict[str, int] = Field(..., description="성취도 분포")
    curriculum_distribution: Dict[str, int] = Field(..., description="교과 분포")
    period_distribution: Dict[str, int] = Field(..., description="학기 분포")