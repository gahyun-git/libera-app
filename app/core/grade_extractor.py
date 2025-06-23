"""
성적 데이터 추출
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import pdfplumber

from app.utils.pdf_utils import PDFUtils, TableValidator, PDFContentClassifier
from app.utils.text_utils import PatternMatcher, ScoreParser, ExtractedContext
from app.core.constants import ScoreConstants

logger = logging.getLogger(__name__)


class GradeExtractor:
    # 성적 테이블 식별 키워드
    GRADE_TABLE_KEYWORDS = ["과목", "단위수", "원점수", "성취도", "교과"]
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.context_cache = {}  # 페이지별 컨텍스트 캐시
        
    def extract_all_grades(self) -> List[Dict[str, Any]]:
        """PDF에서 모든 성적 데이터 추출"""
        all_grades = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.logger.info(f"성적 추출 시작: {len(pdf.pages)} 페이지")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_grades = self._extract_grades_from_page(page, page_num)
                    if page_grades:
                        all_grades.extend(page_grades)
                        self.logger.info(f"페이지 {page_num}: {len(page_grades)}개 성적 추출")
                
                self.logger.info(f"총 {len(all_grades)}개 성적 데이터 추출 완료")
                return all_grades
                
        except Exception as e:
            self.logger.error(f"성적 추출 실패: {e}")
            return []
    
    def _extract_grades_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """페이지에서 성적 데이터 추출"""
        page_grades = []
        
        # 1단계: 텍스트로 성적 페이지 판별
        text = PDFUtils.extract_text_safe(page)
        
        if PDFContentClassifier.classify_page_type(text) != "academic":
            return page_grades
        
        # 2단계: 페이지 컨텍스트 추출 (학년/학기)
        context = self._get_page_context(text, page_num)
        
        # 3단계: 테이블에서 성적 데이터 추출
        tables = PDFUtils.extract_tables_safe(page)
        
        for table_idx, table in enumerate(tables):
            if self._is_grade_table(table):
                table_grades = self._extract_grades_from_table(
                    table, context, page_num, table_idx
                )
                page_grades.extend(table_grades)
        
        return page_grades
    
    def _get_page_context(self, text: str, page_num: int) -> ExtractedContext:
        """페이지 컨텍스트 추출 및 캐시"""
        if page_num in self.context_cache:
            return self.context_cache[page_num]
        
        # 현재 페이지에서 컨텍스트 추출
        context = PatternMatcher.extract_context(text, page_num)
        
        # 컨텍스트가 불완전하면 이전 페이지에서 상속
        if not context.grade and page_num > 1:
            prev_context = self.context_cache.get(page_num - 1)
            if prev_context and prev_context.grade:
                context.grade = prev_context.grade
                context.semester = prev_context.semester
                context.confidence = prev_context.confidence * 0.8
                context.source = f"inherited_from_page_{page_num - 1}"
        
        # 기본값 설정
        if not context.grade:
            context.grade = 1
            context.semester = 1
            context.confidence = 0.3
            context.source = "default"
        
        self.context_cache[page_num] = context
        return context
    
    def _is_grade_table(self, table: List[List[str]]) -> bool:
        """성적 테이블 여부 판별"""
        return (
            PDFUtils.is_valid_table(table) and
            TableValidator.contains_keywords(table, self.GRADE_TABLE_KEYWORDS, 3) and
            TableValidator.has_numeric_data(table)
        )
    
    def _extract_grades_from_table(
        self, 
        table: List[List[str]], 
        context: ExtractedContext,
        page_num: int,
        table_idx: int
    ) -> List[Dict[str, Any]]:
        """테이블에서 성적 데이터 추출"""
        grades = []
        
        if not table or len(table) < 2:
            return grades
        
        # 헤더 찾기 및 매핑
        header_row_idx = PDFUtils.find_header_row(table, self.GRADE_TABLE_KEYWORDS)
        if header_row_idx < 0:
            header_row_idx = 0
        
        headers = table[header_row_idx]
        header_map = self._create_header_mapping(headers)
        
        # 현재 학기 정보 (행별로 업데이트됨)
        current_semester = context.semester
        
        # 데이터 행 처리
        for row_idx, row in enumerate(table[header_row_idx + 1:], 1):
            if self._should_skip_row(row):
                continue
            
            grade_data = self._parse_grade_row(
                row, header_map, context, page_num, table_idx, row_idx, current_semester
            )
            
            if grade_data and grade_data.get('subject'):
                # 학기 정보 업데이트
                if 'semester' in grade_data:
                    current_semester = grade_data['semester']
                grades.append(grade_data)
        
        return grades
    
    def _create_header_mapping(self, headers: List[str]) -> Dict[str, int]:
        """헤더 매핑 생성"""
        header_map = {}
        
        mapping_rules = {
            'semester': ['학기'],
            'curriculum': ['교과', '영역'],
            'subject': ['과목', '과목명'],
            'credit_hours': ['단위수', '단위', '학점'],
            'raw_score': ['원점수', '점수'],
            'subject_average': ['과목평균', '평균'],
            'achievement_level': ['성취도', '등급'],
            'student_count': ['수강자수', '수강자'],
            'grade_rank': ['석차등급', '석차']
        }
        
        for field, keywords in mapping_rules.items():
            for i, header in enumerate(headers):
                if any(keyword in header.lower() for keyword in keywords):
                    header_map[field] = i
                    break
        
        return header_map
    
    def _should_skip_row(self, row: List[str]) -> bool:
        """행을 건너뛸지 확인"""
        if not row or all(not str(cell).strip() for cell in row):
            return True
        
        row_text = " ".join(str(cell) for cell in row).lower()
        skip_keywords = ['합계', '총계', '소계', '이수단위']
        
        return any(keyword in row_text for keyword in skip_keywords)
    
    def _parse_grade_row(
        self,
        row: List[str],
        header_map: Dict[str, int],
        context: ExtractedContext,
        page_num: int,
        table_idx: int,
        row_idx: int,
        current_semester: Optional[int]
    ) -> Dict[str, Any]:
        """성적 행 파싱"""
        grade_data = {
            'grade': context.grade,
            'semester': current_semester or context.semester,
            'page_num': page_num,
            'table_index': table_idx,
            'row_index': row_idx,
            'context_confidence': context.confidence,
            'context_source': context.source
        }
        
        # 각 필드 추출
        for field, col_index in header_map.items():
            if col_index < len(row):
                cell_value = str(row[col_index] or "").strip()
                
                if field == 'semester' and cell_value:
                    # 테이블에서 학기 정보 추출
                    try:
                        semester = int(cell_value)
                        if semester in ScoreConstants.VALID_SEMESTERS:
                            grade_data['semester'] = semester
                    except ValueError:
                        pass
                
                elif field == 'curriculum' and cell_value:
                    # curriculum 텍스트 정리
                    grade_data['curriculum'] = ScoreParser.clean_curriculum_text(cell_value)
                
                elif field in ['raw_score', 'subject_average'] and cell_value:
                    # 복합 점수 파싱 - 한 번만 수행하고 결과를 모든 관련 필드에 적용
                    if 'score_parsed' not in grade_data:
                        parsed_scores = ScoreParser.parse_complex_score(cell_value)
                        if parsed_scores:
                            # 파싱된 결과를 개별 필드에 저장
                            for key, value in parsed_scores.items():
                                grade_data[key] = value
                            grade_data['score_parsed'] = True
                        else:
                            grade_data[field] = cell_value
                    # 이미 파싱된 경우 추가 처리 안함
                
                elif field == 'achievement_level' and cell_value:
                    # 성취도 파싱
                    parsed = ScoreParser.parse_achievement_level(cell_value)
                    if parsed:
                        grade_data.update(parsed)
                
                elif field in ['grade_rank', 'credit_hours'] and cell_value:
                    # 숫자 변환
                    try:
                        grade_data[field] = int(cell_value)
                    except ValueError:
                        grade_data[field] = cell_value
                
                elif cell_value:
                    grade_data[field] = cell_value
        
        # 임시 플래그 제거
        grade_data.pop('score_parsed', None)
        
        return grade_data 