"""
공통 PDF 처리 유틸리티
모든 PDF 추출기들이 공통으로 사용하는 PDF 처리 static 함수들
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page


logger = logging.getLogger(__name__)


class PDFUtils:
    """PDF 처리 관련 공통 유틸리티"""
    
    @staticmethod
    def calculate_file_hash(pdf_path: Path) -> str:
        """PDF 파일 해시 계산"""
        hash_sha256 = hashlib.sha256()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    @staticmethod
    def extract_text_safe(page: Page) -> str:
        """안전한 텍스트 추출"""
        try:
            return page.extract_text() or ""
        except Exception as e:
            logger.warning(f"텍스트 추출 실패: {e}")
            return ""
    
    @staticmethod
    def extract_tables_safe(page: Page) -> List[List[List[str]]]:
        """안전한 테이블 추출"""
        try:
            tables = page.extract_tables() or []
            return [PDFUtils.clean_table(table) for table in tables if table]
        except Exception as e:
            logger.warning(f"테이블 추출 실패: {e}")
            return []
    
    @staticmethod
    def clean_table(table: List[List[Union[str, None]]]) -> List[List[str]]:
        """테이블 데이터 정리"""
        if not table:
            return []
        
        cleaned = []
        for row in table:
            if row and any(cell for cell in row if cell):
                cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                if any(cell for cell in cleaned_row if cell):
                    cleaned.append(cleaned_row)
        
        return cleaned if len(cleaned) > 1 else []
    
    @staticmethod
    def is_valid_table(table: List[List[str]], min_rows: int = 2, min_cols: int = 2) -> bool:
        """유효한 테이블인지 확인"""
        return (
            len(table) >= min_rows and
            all(len(row) >= min_cols for row in table) and
            any(any(cell.strip() for cell in row) for row in table)
        )
    
    @staticmethod
    def find_header_row(table: List[List[str]], keywords: List[str]) -> int:
        """키워드 기반 헤더 행 찾기"""
        for idx, row in enumerate(table[:5]):  # 처음 5개 행만 검사
            if not row:
                continue
                
            row_text = ' '.join(str(cell) for cell in row if cell).lower()
            keyword_count = sum(1 for keyword in keywords if keyword in row_text)
            
            if keyword_count >= len(keywords) // 2:  # 키워드의 절반 이상 포함
                return idx
                
        return -1
    
    @staticmethod
    def extract_page_metadata(page: Page, page_num: int) -> Dict[str, Any]:
        """페이지 메타데이터 추출"""
        return {
            "page_number": page_num,
            "width": page.width,
            "height": page.height,
            "rotation": getattr(page, 'rotation', 0)
        }


class TableValidator:
    """테이블 검증 유틸리티"""
    
    @staticmethod
    def contains_keywords(table: List[List[str]], keywords: List[str], threshold: int = 3) -> bool:
        """테이블이 특정 키워드들을 포함하는지 확인"""
        if not table:
            return False
            
        table_text = ' '.join([
            ' '.join([str(cell) for cell in row if cell])
            for row in table
        ]).lower()
        
        keyword_count = sum(1 for keyword in keywords if keyword in table_text)
        return keyword_count >= threshold
    
    @staticmethod
    def has_numeric_data(table: List[List[str]], min_numbers: int = 5) -> bool:
        """테이블에 충분한 숫자 데이터가 있는지 확인"""
        number_count = 0
        
        for row in table:
            for cell in row:
                if cell and str(cell).strip().replace('.', '').isdigit():
                    number_count += 1
                    
        return number_count >= min_numbers
    
    @staticmethod
    def is_header_like(row: List[str]) -> bool:
        """행이 헤더처럼 보이는지 확인"""
        if not row:
            return False
            
        # 대부분이 한글 텍스트이고 숫자가 적으면 헤더로 간주
        text_cells = sum(1 for cell in row if cell and not str(cell).strip().isdigit())
        number_cells = sum(1 for cell in row if cell and str(cell).strip().isdigit())
        
        return text_cells > number_cells and text_cells >= len(row) // 2


class PDFContentClassifier:
    """PDF 콘텐츠 분류기"""
    
    # 섹션별 키워드
    SECTION_KEYWORDS = {
        "student_info": ["인적사항", "학적사항", "성명", "생년월일", "주민등록번호"],
        "academic": ["교과학습발달상황", "성적", "원점수", "성취도", "과목", "교과"],
        "attendance": ["출결상황", "출석일수", "지각", "조퇴", "결석"],
        "detail": ["세부능력", "특기사항", "과목세부", "교과세부"],
        "school_history": ["학교별", "교육과정", "학적변동", "전학", "편입"],
        "creative": ["창의적체험활동", "자율활동", "동아리활동", "봉사활동", "진로활동"]
    }
    
    @classmethod
    def classify_page_type(cls, text: str) -> str:
        """페이지 유형 분류"""
        if not text:
            return "unknown"
            
        text_lower = text.lower()
        scores = {}
        
        for section_type, keywords in cls.SECTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[section_type] = score
        
        if not scores:
            return "unknown"
            
        # 가장 높은 점수의 섹션 반환
        return max(scores.items(), key=lambda x: x[1])[0]
    
    @classmethod
    def classify_table_type(cls, table: List[List[str]]) -> str:
        """테이블 유형 분류"""
        if not table:
            return "unknown"
            
        table_text = ' '.join([
            ' '.join([str(cell) for cell in row if cell])
            for row in table
        ]).lower()
        
        # 각 섹션별 점수 계산
        scores = {}
        for section_type, keywords in cls.SECTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in table_text)
            if score > 0:
                scores[section_type] = score
        
        if not scores:
            return "unknown"
            
        return max(scores.items(), key=lambda x: x[1])[0] 