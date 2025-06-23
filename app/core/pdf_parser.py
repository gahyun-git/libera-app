"""
PDF 파서
공통 유틸리티를 활용하여 PDF 데이터 추출
"""
import logging
import time
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import pdfplumber

from app.utils.pdf_utils import PDFUtils
from app.utils.text_utils import PatternMatcher, ContentExtractor

from app.core.grade_extractor import GradeExtractor
from app.core.attendance_extractor import AttendanceExtractor

logger = logging.getLogger(__name__)


class PDFParser:
    def __init__(self, page_limit: Optional[int] = 15):
        self.page_limit = page_limit
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_comprehensive_data(self, pdf_path: Path) -> Dict[str, Any]:
        """PDF 파일에서 포괄적인 데이터 추출"""
        return self._extract_data(pdf_path, pdf_path.name)
    
    def extract_comprehensive_data_from_bytes(self, pdf_bytes: io.BytesIO) -> Dict[str, Any]:
        """바이트 데이터에서 포괄적인 데이터 추출"""
        return self._extract_data(pdf_bytes, "memory_pdf")
    
    def _extract_data(self, source: Union[Path, io.BytesIO], source_name: str) -> Dict[str, Any]:
        """공통 데이터 추출 로직"""
        start_time = time.time()
        self.logger.info(f"PDF 데이터 추출 시작: {source_name}")
        
        try:
            pdf_metadata = self._create_metadata(source, source_name)
            extracted_data = self._extract_using_specialists(source)
            processing_time = time.time() - start_time
            
            result = {
                "pdf_metadata": pdf_metadata,
                "extracted_data": extracted_data,
                "processing_time": processing_time,
                "extracted_at": datetime.now().isoformat()
            }
            
            self._log_summary(extracted_data, processing_time)
            return result
            
        except Exception as e:
            self.logger.error(f"PDF 추출 실패: {e}")
            raise Exception(f"PDF 데이터 추출 실패: {str(e)}")
    
    def _create_metadata(self, source: Union[Path, io.BytesIO], source_name: str) -> Dict[str, Any]:
        """PDF 메타데이터 생성"""
        try:
            with pdfplumber.open(source) as pdf:
                metadata = {
                    "filename": source_name,
                    "total_pages": len(pdf.pages),
                    "metadata": pdf.metadata or {}
                }
                
                if isinstance(source, Path):
                    metadata["file_size"] = source.stat().st_size
                    metadata["file_hash"] = PDFUtils.calculate_file_hash(source) # 해시값으로 저장
                else:
                    metadata["file_size"] = len(source.getvalue())
                
                return metadata
        except Exception as e:
            self.logger.error(f"메타데이터 생성 실패: {e}")
            return {"filename": source_name, "error": str(e)}
    
    def _extract_using_specialists(self, source: Union[Path, io.BytesIO]) -> Dict[str, Any]:
        """담당 extractor들을 사용하여 데이터 추출"""
        extracted_data = {
            "student_basic_info": {},
            "academic_records": [],
            "attendance_records": [],
            "detailed_records": [],
            "school_history": [],
            "creative_activities": [],
            "behavioral_records": []
        }
        
        try:
            self.logger.debug("학생 기본 정보 추출")
            extracted_data["student_basic_info"] = self._extract_student_info(source)
            
            if isinstance(source, Path):
                self.logger.debug("성적 정보 추출")
                grade_extractor = GradeExtractor(source)
                extracted_data["academic_records"] = grade_extractor.extract_all_grades()
                
                self.logger.debug("출결 정보 추출")
                attendance_extractor = AttendanceExtractor(source)
                extracted_data["attendance_records"] = attendance_extractor.extract_all_attendance()
            
            with pdfplumber.open(source) as pdf:
                full_text = self._extract_full_text(pdf)
                
                extracted_data["detailed_records"] = self._extract_detailed_records_simple(full_text)
                extracted_data["school_history"] = self._extract_school_history_simple(full_text)
                extracted_data["creative_activities"] = self._extract_creative_activities_simple(full_text)
                extracted_data["behavioral_records"] = self._extract_behavioral_records_simple(full_text)
            
        except Exception as e:
            self.logger.error(f"전문 extractor 사용 중 오류: {e}")
        
        return extracted_data
    
    def _extract_student_info(self, source: Union[Path, io.BytesIO]) -> Dict[str, Any]:
        """학생 기본 정보 추출"""
        student_info = {}
        
        try:
            with pdfplumber.open(source) as pdf:
                text_parts = []
                for page in pdf.pages[:2]:
                    text = PDFUtils.extract_text_safe(page)
                    if text:
                        text_parts.append(text)
                
                combined_text = "\n".join(text_parts)
                student_info = PatternMatcher.extract_student_info(combined_text)
                
                self.logger.debug(f"학생 정보 추출 완료: {list(student_info.keys())}")
                
        except Exception as e:
            self.logger.error(f"학생 정보 추출 실패: {e}")
        
        return student_info
    
    def _extract_full_text(self, pdf) -> str:
        """PDF에서 전체 텍스트 추출"""
        text_parts = []
        
        for i, page in enumerate(pdf.pages[:self.page_limit]):
            try:
                page_text = PDFUtils.extract_text_safe(page)
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                self.logger.warning(f"페이지 {i+1} 텍스트 추출 실패: {e}")
        
        return "\n".join(text_parts)
    
    def _extract_detailed_records_simple(self, text: str) -> List[Dict[str, Any]]:
        """세부능력특기사항 간단 추출"""
        import re
        records = []
        
        # 세부능력 섹션 찾기
        detailed_patterns = [
            r'세\s*부\s*능\s*력.*?및.*?특\s*기\s*사\s*항(.*?)(?=행동특성|진로|수상|\Z)',
            r'교과학습발달상황.*?세부능력.*?특기사항(.*?)(?=행동특성|진로|수상|\Z)'
        ]
        
        for pattern in detailed_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1)
                
                # 과목별로 분할
                subject_pattern = r'([가-힣\s]+?)\s*:\s*([^:]*?)(?=\n[가-힣\s]+?\s*:|\Z)'
                matches = re.finditer(subject_pattern, content, re.DOTALL)
                
                for subject_match in matches:
                    subject_name, subject_content = subject_match.groups()
                    subject_name = subject_name.strip()
                    subject_content = subject_content.strip()
                    
                    if len(subject_content) > 20 and len(subject_name) >= 2:
                        records.append({
                            "subject": subject_name,
                            "content": subject_content,
                            "grade": 1,  # 기본값
                            "semester": 1,  # 기본값
                            "content_length": len(subject_content),
                            "source": "simple_extraction"
                        })
        
        return records
    
    def _extract_school_history_simple(self, text: str) -> List[Dict[str, Any]]:
        """학교 이력 간단 추출"""
        import re
        histories = []
        
        # 기본적인 패턴만 추출
        pattern = r'(\d{4})[년.\- ]+(\d{1,2})[월.\- ]+(\d{1,2})[일.\s]*([가-힣]+(?:초등학교|중학교|고등학교))\s+제?(\d)학년\s+(입학|졸업)'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            year, month, day, school_name, grade, event = match.groups()
            histories.append({
                "date": f"{year}-{int(month):02d}-{int(day):02d}",
                "school_name": school_name.strip(),
                "grade": int(grade),
                "event_type": event
            })
        
        return histories
    
    def _extract_creative_activities_simple(self, text: str) -> List[Dict[str, Any]]:
        """창의적체험활동 간단 추출"""
        import re
        activities = []
        
        # 창의적체험활동 섹션에서 기본 정보만 추출
        creative_section = re.search(r'창의적\s*체험\s*활동.*?(?=진로|수상|봉사|독서|\Z)', text, re.DOTALL)
        if creative_section:
            section_text = creative_section.group(0)
            
            # 학년별 시간 정보 추출
            pattern = r'(\d+)학년\s+(\d+)학기.*?(\d+)(?:시간|분)'
            matches = re.finditer(pattern, section_text)
            
            for match in matches:
                grade, semester, hours = match.groups()
                activities.append({
                    "grade": int(grade),
                    "semester": int(semester),
                    "activity_type": "창의적체험활동",
                    "hours": int(hours) if hours.isdigit() else 0
                })
        
        return activities
    
    def _extract_behavioral_records_simple(self, text: str) -> List[Dict[str, Any]]:
        """행동특성 및 종합의견 추출"""
        import re
        records = []
        
        # 행동특성 및 종합의견 섹션 찾기
        behavioral_patterns = [
            r'(\d+)학년.*?행동특성.*?및.*?종합의견.*?([가-힣\s,.\-()]*?)(?=\d+학년|\Z)',
            r'행동특성.*?종합의견.*?(\d+)학년(.*?)(?=\d+학년|\Z)'
        ]
        
        for pattern in behavioral_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                if len(match.groups()) >= 2:
                    grade_text, content = match.groups()
                    
                    # 학년 추출
                    grade_match = re.search(r'(\d+)학년', grade_text)
                    grade = int(grade_match.group(1)) if grade_match else None
                    
                    if content and len(content.strip()) > 10:
                        records.append({
                            "grade": grade,
                            "content": content.strip(),
                            "content_length": len(content.strip()),
                            "source": "text_extraction"
                        })
        
        return records
    
    def _log_summary(self, extracted_data: Dict[str, Any], processing_time: float):
        """추출 결과 요약 로그"""
        summary = []
        
        for section, data in extracted_data.items():
            if isinstance(data, list):
                count = len(data)
                summary.append(f"{section}: {count}개")
            elif isinstance(data, dict) and data:
                summary.append(f"{section}: 추출됨")
        
        self.logger.info(f"추출 완료 - {', '.join(summary)} (처리시간: {processing_time:.2f}초)")
