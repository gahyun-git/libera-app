"""
PDF 처리 관련 스키마 (개선됨)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.schemas.base import BaseResponse


class PDFUploadRequest(BaseModel):
    """PDF 업로드 요청 스키마"""
    extract_scores: bool = Field(True, description="성적 데이터 추출 여부")
    extract_attendance: bool = Field(True, description="출결 데이터 추출 여부")
    extract_details: bool = Field(True, description="세부사항 추출 여부")
    use_ai_backup: bool = Field(False, description="AI 백업 처리 사용 여부")


class ProcessingMetadata(BaseModel):
    """처리 메타데이터"""
    student_id: int = Field(..., description="학생 ID")
    filename: str = Field(..., description="파일명")
    processing_time: float = Field(..., description="처리 시간(초)")
    grades_count: int = Field(0, description="추출된 성적 수")
    extraction_method: str = Field(..., description="추출 방법")
    timestamp: str = Field(..., description="처리 완료 시간")


class PDFProcessingResult(BaseModel):
    """PDF 처리 결과 스키마"""
    filename: str = Field(..., description="파일명")
    success: bool = Field(..., description="처리 성공 여부")
    data: Optional[ProcessingMetadata] = Field(None, description="처리 결과 데이터")
    warnings: Optional[List[str]] = Field(None, description="경고 메시지")
    error: Optional[str] = Field(None, description="에러 메시지")


class SingleUploadResponse(BaseResponse):
    """단일 파일 업로드 응답"""
    data: ProcessingMetadata = Field(..., description="처리 결과")
    warnings: Optional[List[str]] = Field(None, description="경고 메시지")


class MultipleUploadResponse(BaseResponse):
    """다중 파일 업로드 응답"""
    job_id: str = Field(..., description="작업 ID")
    total_files: int = Field(..., description="총 파일 수")
    status_url: str = Field(..., description="상태 조회 URL")


class ProcessingStatusResponse(BaseModel):
    """처리 상태 응답"""
    job_id: str = Field(..., description="작업 ID")
    status: str = Field(..., description="처리 상태")
    progress: float = Field(..., description="진행률 (0-100)")
    total: int = Field(..., description="총 파일 수")
    completed: int = Field(..., description="완료된 파일 수")
    failed: int = Field(..., description="실패한 파일 수")
    results: Optional[List[PDFProcessingResult]] = Field(None, description="처리 결과 목록")
    start_time: str = Field(..., description="시작 시간")
    end_time: Optional[str] = Field(None, description="종료 시간")
    error: Optional[str] = Field(None, description="에러 메시지")
    
    @validator('progress')
    def validate_progress(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('진행률은 0-100 사이여야 합니다')
        return v


class ParserFeatures(BaseModel):
    """파서 기능 스키마"""
    dynamic_header_detection: bool = Field(..., description="동적 헤더 인식")
    context_inheritance: bool = Field(..., description="컨텍스트 상속")
    flexible_cell_parsing: bool = Field(..., description="유연한 셀 파싱")
    proximity_extraction: bool = Field(..., description="근접 기반 추출")
    ai_fallback: bool = Field(..., description="AI 백업 처리")


class ParserConfigResponse(BaseModel):
    """파서 설정 응답"""
    parser_type: str = Field(..., description="파서 타입")
    ai_backup_enabled: bool = Field(..., description="AI 백업 활성화 여부")
    features: ParserFeatures = Field(..., description="파서 기능")
    version: str = Field(..., description="버전")


class PDFMetadataResponse(BaseModel):
    """PDF 메타데이터 응답"""
    id: int = Field(..., description="메타데이터 ID")
    original_filename: str = Field(..., description="원본 파일명")
    file_hash: str = Field(..., description="파일 해시")
    file_size: int = Field(..., description="파일 크기")
    page_count: int = Field(..., description="페이지 수")
    upload_timestamp: datetime = Field(..., description="업로드 시간")
    processed_at: datetime = Field(..., description="처리 완료 시간")
    processing_version: str = Field(..., description="처리 버전")
    
    class Config:
        from_attributes = True 