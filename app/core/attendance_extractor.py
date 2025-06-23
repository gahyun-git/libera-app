"""
출결 데이터 추출
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import pdfplumber

from app.utils.pdf_utils import PDFUtils, TableValidator, PDFContentClassifier
from app.utils.text_utils import ContentExtractor

logger = logging.getLogger(__name__)


class AttendanceExtractor:
    # 출결 테이블 식별 키워드
    ATTENDANCE_KEYWORDS = ["출결", "지각", "조퇴", "결석", "질병", "미인정", "기타"]
    
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def extract_all_attendance(self) -> List[Dict[str, Any]]:
        """모든 출결 데이터 추출"""
        attendance_records = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.logger.info(f"출결 추출 시작: {len(pdf.pages)} 페이지")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_records = self._extract_attendance_from_page(page, page_num)
                    if page_records:
                        attendance_records.extend(page_records)
                        self.logger.info(f"페이지 {page_num}: {len(page_records)}개 출결 기록 추출")
                
                self.logger.info(f"총 {len(attendance_records)}개 출결 기록 추출 완료")
                return attendance_records
                
        except Exception as e:
            self.logger.error(f"출결 추출 실패: {e}")
            return []
    
    def _extract_attendance_from_page(self, page, page_num: int) -> List[Dict[str, Any]]:
        """페이지에서 출결 데이터 추출"""
        page_records = []
        
        # 1단계: 텍스트로 출결 페이지 판별
        text = PDFUtils.extract_text_safe(page)
        
        if PDFContentClassifier.classify_page_type(text) != "attendance":
            return page_records
        
        self.logger.debug(f"페이지 {page_num}: 출결 페이지 발견")
        
        # 2단계: 테이블에서 출결 데이터 추출
        tables = PDFUtils.extract_tables_safe(page)
        
        for table_idx, table in enumerate(tables):
            if self._is_attendance_table(table):
                self.logger.debug(f"페이지 {page_num}, 테이블 {table_idx}: 출결 테이블 발견")
                
                records = self._extract_from_attendance_table(table, page_num, table_idx)
                page_records.extend(records)
        
        # 3단계: 텍스트에서 출결 데이터 추출 (보완용)
        text_records = ContentExtractor.extract_attendance_data(text)
        for record in text_records:
            record.update({
                "page_num": page_num,
                "extraction_method": "text"
            })
        page_records.extend(text_records)
        
        return self._remove_duplicates(page_records)
    
    def _is_attendance_table(self, table: List[List[str]]) -> bool:
        """출결 테이블 여부 판별"""
        return (
            PDFUtils.is_valid_table(table, min_rows=3) and
            TableValidator.contains_keywords(table, self.ATTENDANCE_KEYWORDS, 4) and
            TableValidator.has_numeric_data(table, min_numbers=3)
        )
    
    def _extract_from_attendance_table(
        self, 
        table: List[List[str]], 
        page_num: int,
        table_idx: int
    ) -> List[Dict[str, Any]]:
        """출결 테이블에서 데이터 추출"""
        records = []
        
        if not table or len(table) < 2:
            return records
        
        # 헤더 찾기
        header_row_idx = PDFUtils.find_header_row(table, self.ATTENDANCE_KEYWORDS)
        if header_row_idx < 0:
            header_row_idx = 0
        
        headers = table[header_row_idx]
        self.logger.debug(f"출결 헤더: {headers}")
        
        # 데이터 행 처리
        for row_idx, row in enumerate(table[header_row_idx + 1:], 1):
            if not row or len(row) < 3:
                continue
            
            # 학년 정보 추출
            grade = self._extract_grade_from_row(row)
            if not grade:
                continue
            
            # 출결 데이터 파싱
            attendance_data = self._parse_attendance_row(
                headers, row, grade, page_num, table_idx, row_idx
            )
            
            if attendance_data and self._has_attendance_data(attendance_data):
                records.append(attendance_data)
                self.logger.debug(f"{grade}학년 출결 데이터 추출 완료")
        
        return records
    
    def _extract_grade_from_row(self, row: List[str]) -> Optional[int]:
        """행에서 학년 정보 추출"""
        # 첫 번째 셀에서 학년 찾기
        if row and row[0]:
            first_cell = str(row[0]).strip()
            if first_cell.isdigit() and 1 <= int(first_cell) <= 3:
                return int(first_cell)
        
        # 행 전체에서 학년 찾기
        row_text = ' '.join(str(cell) for cell in row if cell)
        import re
        grade_match = re.search(r'(\d)학년', row_text)
        if grade_match:
            return int(grade_match.group(1))
        
        return None
    
    def _parse_attendance_row(
        self, 
        headers: List[str], 
        row: List[str], 
        grade: int,
        page_num: int,
        table_idx: int,
        row_idx: int
    ) -> Dict[str, Any]:
        """출결 행 파싱"""
        attendance_data = {
            "grade": grade,
            "semester": 1,  # 출결은 연간이지만 DB 제약조건상 1로 설정
            "page_num": page_num,
            "table_index": table_idx,
            "row_index": row_idx,
            "extraction_method": "table",
            "extraction_confidence": 0.8,
            
            # 기본값 설정
            "absence_disease": 0,
            "absence_unexcused": 0,
            "absence_etc": 0,
            "tardiness_disease": 0,
            "tardiness_unexcused": 0,
            "tardiness_etc": 0,
            "early_leave_disease": 0,
            "early_leave_unexcused": 0,
            "early_leave_etc": 0,
            "result_disease": 0,
            "result_unexcused": 0,
            "result_etc": 0,
            "special_notes": ""
        }
        
        # 실제 출결표 구조에 따른 컬럼 매핑
        # 컬럼 2-4: 결석 (질병, 미인정, 기타)
        if len(row) > 2:
            attendance_data["absence_disease"] = self._safe_int_convert(row[2])
        if len(row) > 3:
            attendance_data["absence_unexcused"] = self._safe_int_convert(row[3])
        if len(row) > 4:
            attendance_data["absence_etc"] = self._safe_int_convert(row[4])
        
        # 컬럼 5-7: 지각 (질병, 미인정, 기타)
        if len(row) > 5:
            attendance_data["tardiness_disease"] = self._safe_int_convert(row[5])
        if len(row) > 6:
            attendance_data["tardiness_unexcused"] = self._safe_int_convert(row[6])
        if len(row) > 7:
            attendance_data["tardiness_etc"] = self._safe_int_convert(row[7])
        
        # 컬럼 8-10: 조퇴 (질병, 미인정, 기타)
        if len(row) > 8:
            attendance_data["early_leave_disease"] = self._safe_int_convert(row[8])
        if len(row) > 9:
            attendance_data["early_leave_unexcused"] = self._safe_int_convert(row[9])
        if len(row) > 10:
            attendance_data["early_leave_etc"] = self._safe_int_convert(row[10])
        
        # 특기사항 (마지막 컬럼)
        if len(row) > 14 and row[14]:
            special_notes = str(row[14]).strip()
            if special_notes and special_notes != '.':
                attendance_data["special_notes"] = special_notes
        
        # 헤더 기반 매핑 (보완용)
        self._map_by_headers(headers, row, attendance_data)
        
        return attendance_data
    
    def _map_by_headers(self, headers: List[str], row: List[str], attendance_data: Dict[str, Any]):
        """헤더 기반 데이터 매핑"""
        for idx, header in enumerate(headers):
            if idx >= len(row) or not header:
                continue
            
            header_text = str(header).lower()
            cell_value = self._safe_int_convert(row[idx])
            
            # 결석 매핑
            if "결석" in header_text:
                if "질병" in header_text:
                    attendance_data["absence_disease"] = cell_value
                elif "미인정" in header_text:
                    attendance_data["absence_unexcused"] = cell_value
                elif "기타" in header_text:
                    attendance_data["absence_etc"] = cell_value
            
            # 지각 매핑
            elif "지각" in header_text:
                if "질병" in header_text:
                    attendance_data["tardiness_disease"] = cell_value
                elif "미인정" in header_text:
                    attendance_data["tardiness_unexcused"] = cell_value
                elif "기타" in header_text:
                    attendance_data["tardiness_etc"] = cell_value
            
            # 조퇴 매핑
            elif "조퇴" in header_text:
                if "질병" in header_text:
                    attendance_data["early_leave_disease"] = cell_value
                elif "미인정" in header_text:
                    attendance_data["early_leave_unexcused"] = cell_value
                elif "기타" in header_text:
                    attendance_data["early_leave_etc"] = cell_value
            
            # 특기사항
            elif "특기" in header_text or "비고" in header_text:
                if row[idx]:
                    attendance_data["special_notes"] = str(row[idx]).strip()
    
    def _safe_int_convert(self, value) -> int:
        """안전한 정수 변환"""
        if not value or value == '.' or value == '':
            return 0
        val_str = str(value).strip()
        if val_str == '.' or val_str == '' or val_str == '-':
            return 0
        if val_str.isdigit():
            return int(val_str)
        return 0
    
    def _has_attendance_data(self, data: Dict[str, Any]) -> bool:
        """출결 데이터가 있는지 확인"""
        # 출결 문제가 있거나, 특기사항이 있거나, 학년 정보가 있으면 유효
        has_issues = any([
            data.get("tardiness_disease", 0) > 0,
            data.get("tardiness_unexcused", 0) > 0,
            data.get("tardiness_etc", 0) > 0,
            data.get("absence_disease", 0) > 0,
            data.get("absence_unexcused", 0) > 0,
            data.get("absence_etc", 0) > 0,
            data.get("early_leave_disease", 0) > 0,
            data.get("early_leave_unexcused", 0) > 0,
            data.get("early_leave_etc", 0) > 0
        ])
        
        has_notes = bool(data.get("special_notes", "").strip())
        has_grade = data.get("grade", 0) > 0
        
        return has_issues or has_notes or has_grade
    
    def _remove_duplicates(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 제거"""
        unique_records = []
        seen = set()
        
        for record in records:
            key = (record.get("grade"), record.get("semester"))
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        return unique_records 