"""
PDF 데이터 추출 및 타입 안전 변환
"""
import logging
import io
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from app.core.pdf_config import PDFConfig
from app.utils.data_converter import StudentDataConverter, ScoreDataConverter

logger = logging.getLogger(__name__)


@dataclass
class ExtractedData:
    """추출된 데이터 불변 객체"""
    student_info: Dict[str, Any]
    scores: list
    attendance_records: list
    detail_records: list
    extraction_metadata: Dict[str, Any]


class PDFProcessor:
    """PDF 처리 전담 클래스"""
    
    def __init__(self):
        self.config = PDFConfig()
    
    def validate_file_info(self, filename: str, content_size: int) -> None:
        """파일 정보 검증"""
        if not filename:
            raise ValueError("파일명이 없습니다")
        
        if not self.config.validate_file_extension(filename):
            ext = Path(filename).suffix.lower()
            raise ValueError(f"지원하지 않는 파일 형식: {ext}")
        
        if not self.config.validate_file_size(content_size):
            raise ValueError(f"파일 크기 초과: {content_size} bytes")
    
    async def process_pdf_bytes(self, filename: str, content: bytes) -> ExtractedData:
        """바이트 데이터에서 직접 PDF 처리"""
        try:
            pdf_source = io.BytesIO(content)
            return await self._extract_from_source(pdf_source, filename)
            
        except Exception as e:
            raise ValueError(f"PDF 처리 실패: {e}") from e
    
    async def extract_pdf_data(self, file_path: Path) -> ExtractedData:
        """파일 경로에서 PDF 데이터 추출"""
        try:
            return await self._extract_from_source(file_path, file_path.name)
            
        except Exception as e:
            logger.error(f"PDF 추출 실패: {e}")
            return self._create_fallback_data(file_path, str(e))
    
    async def _extract_from_source(self, source: Union[Path, io.BytesIO], filename: str) -> ExtractedData:
        """PDF 소스에서 데이터 추출"""
        raw_data = await self._extract_raw_data(source)
        return self._convert_extracted_data(raw_data, filename)
    
    async def _extract_raw_data(self, source: Union[Path, io.BytesIO]) -> Dict[str, Any]:
        """PDF 파서를 사용한 원본 데이터 추출"""
        try:
            from app.core.pdf_parser import PDFParser
            
            parser = PDFParser()
            
            if isinstance(source, io.BytesIO):
                result = parser.extract_comprehensive_data_from_bytes(source)
            else:
                result = parser.extract_comprehensive_data(source)
            
            return result.get("extracted_data", {})
            
        except Exception as e:
            logger.warning(f"PDF 파서 실패, 기본값 사용: {e}")
            return self._create_default_data()
    
    def _create_default_data(self) -> Dict[str, Any]:
        """기본 데이터 생성"""
        return {
            "student_basic_info": {"name": self.config.UNKNOWN_STUDENT_NAME},
            "academic_records": []
        }
    
    def _convert_extracted_data(self, raw_data: Dict[str, Any], filename: str) -> ExtractedData:
        """추출된 원본 데이터를 타입 안전하게 변환"""
        raw_student_info = raw_data.get("student_basic_info", {})
        converted_student_info = StudentDataConverter.convert_student_info(raw_student_info)
        
        raw_scores = raw_data.get("academic_records", [])
        converted_scores = ScoreDataConverter.batch_convert_scores(raw_scores)
        
        metadata = {
            "method": self.config.EXTRACTION_METHODS["PDF_PARSER"],
            "original_filename": filename
        }
        
        return ExtractedData(
            student_info=converted_student_info,
            scores=converted_scores,
            attendance_records=raw_data.get("attendance_records", []),
            detail_records=raw_data.get("detailed_records", []),
            extraction_metadata=metadata
        )
    
    def _create_fallback_data(self, file_path: Path, error: str) -> ExtractedData:
        """실패 시 fallback 데이터 생성"""
        fallback_raw = self._extract_from_filename(file_path)
        
        student_info = StudentDataConverter.convert_student_info(
            fallback_raw.get("student_basic_info", {})
        )
        
        metadata = {
            "method": self.config.EXTRACTION_METHODS["FALLBACK"],
            "error": error,
            "file_size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        return ExtractedData(
            student_info=student_info,
            scores=[],
            attendance_records=[],
            detail_records=[],
            extraction_metadata=metadata
        )
    
    def _extract_from_filename(self, file_path: Path) -> Dict[str, Any]:
        """파일명에서 기본 정보 추출"""
        filename = file_path.name
        student_info = {"name": self.config.UNKNOWN_STUDENT_NAME}
        
        import re
        name_match = re.search(r'([가-힣]{2,4})', filename)
        if name_match:
            student_info["name"] = name_match.group(1)
        
        return {
            "student_basic_info": student_info,
            "academic_records": []
        } 