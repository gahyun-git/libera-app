"""
PDF 처리 서비스
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.pdf_processor import PDFProcessor
from app.services.database_service import DatabaseService
from app.services.file_handler import FileHandler

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """처리 결과 불변 객체"""
    filename: str
    success: bool
    student_id: Optional[int] = None
    scores_count: int = 0
    processing_time: float = 0.0
    extraction_method: str = "unknown"
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PDFService:
    def __init__(self, db: AsyncSession):
        self.processor = PDFProcessor()
        self.db_service = DatabaseService(db)
    
    async def process_multiple_files(self, files: List[UploadFile]) -> Dict[str, Any]:
        start_time = time.time()
        results = []
        
        for file in files:
            try:
                result = await self._process_single_file(file)
                results.append(result)
            except Exception as e:
                logger.error(f"파일 처리 실패: {file.filename} - {e}")
                results.append(ProcessingResult(
                    filename=file.filename or "unknown",
                    success=False,
                    error=str(e)
                ))
        
        return self._create_summary(results, time.time() - start_time)
    
    async def process_multiple_file_data(self, file_data_list: List[Tuple[str, bytes]]) -> Dict[str, Any]:
        """바이트 데이터 처리"""
        start_time = time.time()
        results = []
        
        for filename, content in file_data_list:
            try:
                result = await self._process_file_data(filename, content)
                results.append(result)
            except Exception as e:
                logger.error(f"파일 처리 실패: {filename} - {e}")
                results.append(ProcessingResult(
                    filename=filename,
                    success=False,
                    error=str(e)
                ))
        
        return self._create_summary(results, time.time() - start_time)
    
    async def process_files_in_background(
        self, 
        file_data_list: List[Tuple[str, bytes]], 
        job_service,
        job_id: str
    ):
        """백그라운드에서 파일 처리"""
        try:
            result = await self.process_multiple_file_data(file_data_list)
            await job_service.complete_job(job_id, result["results"])
            
        except Exception as e:
            await job_service.fail_job(job_id, str(e))
    
    async def validate_and_read_files(self, files: List[UploadFile]) -> List[Tuple[str, bytes]]:
        """파일 검증 및 읽기"""
        file_data_list = []
        
        for file in files:
            if not file.filename or not file.filename.endswith('.pdf'):
                continue
            
            try:
                await file.seek(0)
                content = await file.read()
                file_data_list.append((file.filename, content))
                
            except Exception as e:
                logger.error(f"파일 읽기 실패: {file.filename} - {e}")
                continue
        
        return file_data_list
    
    def build_processing_results(self, results: List[Dict[str, Any]]) -> List:
        """처리 결과 빌딩"""
        from datetime import datetime
        from app.schemas.pdf import PDFProcessingResult, ProcessingMetadata
        
        return [
            PDFProcessingResult(
                filename=r["filename"],
                success=r["success"],
                data=ProcessingMetadata(
                    student_id=r.get("data", {}).get("student_id", 0),
                    filename=r["filename"],
                    processing_time=r.get("data", {}).get("processing_time", 0.0),
                    grades_count=r.get("data", {}).get("scores_count", 0),
                    extraction_method=r.get("data", {}).get("extraction_method", "mock"),
                    timestamp=datetime.now().isoformat()
                ) if r["success"] and r.get("data") else None,
                warnings=r.get("warnings"),
                error=r.get("error")
            )
            for r in results
        ]

    async def _process_single_file(self, file: UploadFile) -> ProcessingResult:
        """단일 파일 처리"""
        start_time = time.time()
        
        try:
            content = await FileHandler.read_upload_file(file)
            self.processor.validate_file_info(file.filename or "", len(content))
            
            extracted_data = await self.processor.process_pdf_bytes(
                file.filename or "unknown.pdf", content
            )
            
            student_id = await self.db_service.save_extracted_data(extracted_data)
            
            return ProcessingResult(
                filename=file.filename or "unknown",
                success=True,
                student_id=student_id,
                scores_count=len(extracted_data.scores),
                processing_time=time.time() - start_time,
                extraction_method=extracted_data.extraction_metadata.get("method", "unknown")
            )
            
        except Exception as e:
            logger.error(f"파일 처리 실패: {file.filename} - {e}")
            return ProcessingResult(
                filename=file.filename or "unknown",
                success=False,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _process_file_data(self, filename: str, content: bytes) -> ProcessingResult:
        """바이트 데이터 처리"""
        """
        UploadFile이 제공하는 파일객체는 전송된 데이터를 메모리나 디스크에 잠시 보관하기때문에
        한번 읽고나면 닫힐 수 있고, 여러 비동기 작업에서 재사용하면 문제생김 (둘다 발생했었음)
        그래서 파일내용을 한번 메모리로 읽어서 byte로 보관하고 처리.        
        """
        start_time = time.time()
        
        try:
            self.processor.validate_file_info(filename, len(content))
            
            extracted_data = await self.processor.process_pdf_bytes(filename, content)
            
            student_id = await self.db_service.save_extracted_data(extracted_data)
            
            return ProcessingResult(
                filename=filename,
                success=True,
                student_id=student_id,
                scores_count=len(extracted_data.scores),
                processing_time=time.time() - start_time,
                extraction_method=extracted_data.extraction_metadata.get("method", "unknown")
            )
            
        except Exception as e:
            logger.error(f"파일 처리 실패: {filename} - {e}")
            return ProcessingResult(
                filename=filename,
                success=False,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _create_summary(self, results: List[ProcessingResult], total_time: float) -> Dict[str, Any]:
        """처리 결과 요약 생성"""
        total_count = len(results)
        success_count = sum(1 for r in results if r.success)
        
        return {
            "total": total_count,
            "completed": success_count,
            "failed": total_count - success_count,
            "processing_time": total_time,
            "results": [self._result_to_dict(r) for r in results]
        }
    
    def _result_to_dict(self, result: ProcessingResult) -> Dict[str, Any]:
        """ProcessingResult를 딕셔너리로 변환"""
        return {
            "filename": result.filename,
            "success": result.success,
            "data": {
                "student_id": result.student_id or 0,
                "scores_count": result.scores_count,
                "processing_time": result.processing_time,
                "extraction_method": result.extraction_method
            } if result.success else None,
            "warnings": result.warnings,
            "error": result.error
        }