"""
세부능력특기사항 추출
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import pdfplumber

from app.utils.pdf_utils import PDFUtils, TableValidator, PDFContentClassifier
from app.utils.text_utils import PatternMatcher, ContentExtractor, ContentValidator

logger = logging.getLogger(__name__)


class DetailExtractor:
    
    # 세부능력 식별 키워드
    DETAIL_KEYWORDS = ["세 부 능 력 특 기 사 항", "세부능력", "특기사항", "과목세부", "교과세부", "세특"]
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def extract_all_details(self) -> List[Dict[str, Any]]:
        """모든 세부능력특기사항 추출"""
        all_details = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.logger.info(f"세부능력특기사항 추출 시작: {len(pdf.pages)} 페이지")
                
                current_grade = None
                current_semester = None
                previous_page_text = ""
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_details = self._extract_details_from_page(
                        page, page_num, current_grade, current_semester, previous_page_text
                    )
                    
                    if page_details:
                        all_details.extend(page_details)
                        # 컨텍스트 업데이트
                        if page_details:
                            current_grade = page_details[0].get("grade", current_grade)
                            current_semester = page_details[0].get("semester", current_semester)
                    
                    # 다음 페이지를 위해 텍스트 저장
                    text = PDFUtils.extract_text_safe(page)
                    if PDFContentClassifier.classify_page_type(text) == "detail":
                        previous_page_text = text
                
                # 중복 제거
                unique_details = self._remove_duplicates_advanced(all_details)
                
                self.logger.info(f"세부능력특기사항 추출 완료: {len(all_details)}개 (중복 제거 후: {len(unique_details)}개)")
                return unique_details
                
        except Exception as e:
            self.logger.error(f"세부능력특기사항 추출 실패: {e}")
            return []
    
    def _extract_details_from_page(
        self, 
        page, 
        page_num: int, 
        current_grade: Optional[int],
        current_semester: Optional[int],
        previous_page_text: str
    ) -> List[Dict[str, Any]]:
        """페이지에서 세부능력특기사항 추출"""
        page_details = []
        
        # 1단계: 텍스트로 세부능력 페이지 판별
        text = PDFUtils.extract_text_safe(page)
        
        if PDFContentClassifier.classify_page_type(text) != "detail":
            return page_details
        
        self.logger.debug(f"페이지 {page_num}: 세부능력특기사항 페이지 감지")
        
        # 2단계: 컨텍스트 추출 (학년/학기)
        context = PatternMatcher.extract_context(text, page_num)
        page_grade = context.grade or current_grade or self._estimate_grade(page_num)
        page_semester = context.semester or current_semester or 1
        
        # 3단계: 페이지 간 연결 처리
        combined_text = self._combine_page_texts(previous_page_text, text, page_num)
        
        # 4단계: 테이블에서 추출
        tables = PDFUtils.extract_tables_safe(page)
        for table_idx, table in enumerate(tables):
            if self._is_detail_table(table):
                table_details = self._extract_from_table(
                    table, page_num, table_idx, page_grade, page_semester
                )
                page_details.extend(table_details)
        
        # 5단계: 텍스트에서 추출 (연결된 텍스트 사용)
        text_details = ContentExtractor.extract_subject_details(combined_text)
        for detail in text_details:
            detail.update({
                "grade": page_grade,
                "semester": detail.get("semester") or page_semester,
                "page": page_num,
                "extraction_method": "text"
            })
        page_details.extend(text_details)
        
        return page_details
    
    def _estimate_grade(self, page_num: int) -> int:
        """페이지 번호 기반 학년 추정"""
        if page_num <= 8:
            return 1
        elif page_num <= 16:
            return 2
        else:
            return 3
    
    def _combine_page_texts(self, previous_text: str, current_text: str, page_num: int) -> str:
        """페이지 간 텍스트 연결 처리"""
        if not previous_text:
            return current_text
        
        import re
        
        # 이전 페이지에서 잘린 부분 찾기
        previous_lines = previous_text.strip().split('\n')
        current_lines = current_text.strip().split('\n')
        
        # 이전 페이지의 마지막 부분에서 과목이 시작되었는지 확인
        for i in range(min(5, len(previous_lines))):
            line = previous_lines[-(i+1)]
            
            # 과목명: 패턴이 있고 내용이 불완전한 경우
            subject_match = re.search(r'([가-힣]{2,10})\s*[:：]\s*(.+)', line)
            if subject_match:
                subject = subject_match.group(1)
                content_start = subject_match.group(2).strip()
                
                # 내용이 짧거나 문장이 불완전한 경우
                if len(content_start) < 100 or not content_start.endswith('.'):
                    # 다음 페이지 시작 부분에서 연결될 수 있는 텍스트 찾기
                    for j, next_line in enumerate(current_lines[:10]):
                        if any(next_line.startswith(pattern) for pattern in ['을 함.', '을 통해', '에 대해', '을 위해', '을 하며']):
                            combined_content = content_start + next_line
                            modified_previous = '\n'.join(previous_lines[:-i-1] + [f"{subject}: {combined_content}"])
                            modified_current = '\n'.join(current_lines[j+1:])
                            
                            self.logger.info(f"페이지 {page_num-1}-{page_num}: {subject} 과목 텍스트 연결됨")
                            return modified_previous + '\n' + modified_current
        
        return current_text
    
    def _is_detail_table(self, table: List[List[str]]) -> bool:
        """세부능력특기사항 테이블 여부 판별"""
        return (
            PDFUtils.is_valid_table(table) and
            TableValidator.contains_keywords(table, self.DETAIL_KEYWORDS, 1)
        )
    
    def _extract_from_table(
        self, 
        table: List[List[str]], 
        page_num: int, 
        table_idx: int,
        current_grade: Optional[int] = None,
        current_semester: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """테이블에서 세부능력특기사항 추출"""
        details = []
        
        if len(table) < 2:
            return details
        
        headers = [str(cell or "").strip() for cell in table[0]]
        self.logger.debug(f"페이지 {page_num} 테이블 {table_idx}: 헤더 {headers}")
        
        # 과목 컬럼과 내용 컬럼 찾기
        subject_col = self._find_subject_column(headers)
        content_col = self._find_content_column(headers)
        
        if subject_col is None or content_col is None:
            # 테이블 구조가 예상과 다른 경우, 텍스트로 처리
            self.logger.warning(f"페이지 {page_num} 테이블 {table_idx}: 과목/내용 컬럼을 찾을 수 없음")
            
            table_text = ""
            for row in table[1:]:
                row_text = " ".join(str(cell or "") for cell in row if cell)
                if row_text.strip():
                    table_text += row_text + "\n"
            
            if table_text.strip():
                text_details = ContentExtractor.extract_subject_details(table_text)
                for detail in text_details:
                    detail.update({
                        "grade": current_grade or 1,
                        "semester": current_semester or 1,
                        "page": page_num,
                        "table_idx": table_idx,
                        "extraction_method": "table_as_text"
                    })
                details.extend(text_details)
            
            return details
        
        # 데이터 행 처리
        for row_idx, row in enumerate(table[1:], 1):
            try:
                if len(row) <= max(subject_col, content_col):
                    continue
                
                subject = str(row[subject_col] or "").strip()
                content = str(row[content_col] or "").strip()
                
                if ContentValidator.is_valid_detail_record(subject, content):
                    detail_record = {
                        "subject": subject,
                        "content": content,
                        "grade": current_grade or 1,
                        "semester": current_semester or 1,
                        "page": page_num,
                        "table_idx": table_idx,
                        "row_idx": row_idx,
                        "extraction_method": "table"
                    }
                    
                    details.append(detail_record)
                    self.logger.debug(f"세부능력 추출: {current_grade or 1}학년 {current_semester or 1}학기 - {subject}")
                
            except Exception as e:
                self.logger.warning(f"페이지 {page_num} 테이블 {table_idx} 행 {row_idx} 처리 오류: {e}")
                continue
        
        return details
    
    def _find_subject_column(self, headers: List[str]) -> Optional[int]:
        """과목 컬럼 찾기"""
        subject_keywords = ["과목", "교과", "과목명", "교과명"]
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in subject_keywords):
                return i
        
        return 0 if headers else None
    
    def _find_content_column(self, headers: List[str]) -> Optional[int]:
        """내용 컬럼 찾기"""
        content_keywords = ["세부능력", "특기사항", "내용", "세특", "세부", "능력", "특기"]
        
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in content_keywords):
                return i
        
        return 1 if len(headers) > 1 else None
    
    def _remove_duplicates_advanced(self, details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """고급 중복 제거 (페이지 연결 고려)"""
        unique_details = []
        seen_combinations = set()
        
        # 내용 길이 기준으로 정렬 (긴 내용이 우선)
        sorted_details = sorted(details, key=lambda x: len(x.get("content", "")), reverse=True)
        
        for detail in sorted_details:
            # 학년, 학기, 과목, 내용의 첫 100자로 중복 판별
            key = (
                detail.get("grade", 1),
                detail.get("semester", 1),
                detail.get("subject", ""),
                detail.get("content", "")[:100]
            )
            
            # 유사한 내용인지 확인 (페이지 연결로 인한 중복 방지)
            is_duplicate = False
            for seen_key in seen_combinations:
                if (seen_key[0] == key[0] and  # 같은 학년
                    seen_key[1] == key[1] and  # 같은 학기
                    seen_key[2] == key[2] and  # 같은 과목
                    len(seen_key[3]) < len(key[3]) and  # 기존 내용이 더 짧고
                    key[3].startswith(seen_key[3][:50])):  # 새 내용이 기존 내용을 포함
                    is_duplicate = True
                    break
            
            if not is_duplicate and key not in seen_combinations:
                seen_combinations.add(key)
                unique_details.append(detail)
            else:
                self.logger.debug(f"중복 제거: {detail.get('grade')}학년 {detail.get('semester')}학기 - {detail.get('subject')}")
        
        return unique_details