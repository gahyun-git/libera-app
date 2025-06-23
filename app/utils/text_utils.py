"""
공통 텍스트 처리 유틸리티
모든 추출기들이 공통으로 사용하는 텍스트 파싱 및 패턴 매칭 함수들
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.constants import ScoreConstants


logger = logging.getLogger(__name__)


@dataclass
class ExtractedContext:
    """추출된 컨텍스트 정보"""
    grade: Optional[int] = None
    semester: Optional[int] = None
    confidence: float = 0.0
    source: str = ""


class PatternMatcher:
    """패턴 매칭 유틸리티"""
    
    # 학생 정보 패턴
    STUDENT_PATTERNS = {
        "name": [
            r'성명\s*[:：]\s*([가-힣]{2,4})\s+성별',
            r'성명\s*[:：]\s*([가-힣]{2,4})',
            r'이름\s*[:：]\s*([가-힣]{2,4})',
            r'학생\s*[:：]\s*([가-힣]{2,4})',
        ],
        "birth_date": [
            r'주민등록번호\s*[:：]\s*(\d{2})(\d{2})(\d{2})-\d{7}',
            r'생년월일\s*[:：]\s*(\d{4})[년\-\.]\s*(\d{1,2})[월\-\.]\s*(\d{1,2})',
            r'(\d{4})[년\-\.]\s*(\d{1,2})[월\-\.]\s*(\d{1,2})[일]?.*?생',
            r'(\d{4})\-(\d{2})\-(\d{2})',
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
        ],
        "gender": [
            r'성별\s*[:：]\s*([남여])',
            r'([남여])성',
        ],
        "school": [
            r'학교명\s*[:：]\s*([가-힣]+고등학교)',
            r'([가-힣]+고등학교)',
            r'학교\s*[:：]\s*([가-힣]+고등학교)',
        ]
    }
    
    # 컨텍스트 패턴 (학년/학기)
    CONTEXT_PATTERNS = [
        (r'\[(\d+)학년\]', 1.0, 'bracket'),
        (r'(\d+)학년\s*(\d+)학기', 1.0, 'grade_semester'),
        (r'(\d+)\s*-\s*(\d+)', 0.8, 'dash'),
        (r'제\s*(\d+)\s*학년', 0.9, 'ordinal'),
    ]
    
    @classmethod
    def extract_student_info(cls, text: str) -> Dict[str, Any]:
        """학생 정보 추출"""
        info = {}
        
        for field, patterns in cls.STUDENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if field == "birth_date":
                        info[field] = cls._parse_birth_date(match)
                        info["birth_date_source"] = "regex_extraction"
                    else:
                        info[field] = match.group(1).strip()
                    break
                    
        return info
    
    @classmethod
    def extract_context(cls, text: str, page_num: int = 0) -> ExtractedContext:
        """학년/학기 컨텍스트 추출"""
        context = ExtractedContext()
        
        for pattern, confidence, pattern_type in cls.CONTEXT_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if pattern_type == 'bracket':
                        # [n학년] 형태
                        grade = int(match.group(1))
                        if grade in ScoreConstants.VALID_GRADES:
                            context.grade = grade
                            context.confidence = confidence
                            context.source = f"bracket_pattern_page_{page_num}"
                            return context
                            
                    elif pattern_type == 'grade_semester':
                        # n학년 n학기 형태
                        grade = int(match.group(1))
                        semester = int(match.group(2))
                        if grade in ScoreConstants.VALID_GRADES and semester in ScoreConstants.VALID_SEMESTERS:
                            context.grade = grade
                            context.semester = semester
                            context.confidence = confidence
                            context.source = f"grade_semester_pattern_page_{page_num}"
                            return context
                            
                    elif pattern_type == 'dash':
                        # n-n 형태
                        grade = int(match.group(1))
                        semester = int(match.group(2))
                        if grade in ScoreConstants.VALID_GRADES and semester in ScoreConstants.VALID_SEMESTERS:
                            context.grade = grade
                            context.semester = semester
                            context.confidence = confidence
                            context.source = f"dash_pattern_page_{page_num}"
                            return context
                            
                    elif pattern_type == 'ordinal':
                        # 제n학년 형태
                        grade = int(match.group(1))
                        if grade in ScoreConstants.VALID_GRADES:
                            context.grade = grade
                            context.confidence = confidence
                            context.source = f"ordinal_pattern_page_{page_num}"
                            
                except ValueError:
                    continue
                    
        return context
    
    @classmethod
    def _parse_birth_date(cls, match) -> str:
        """생년월일 파싱"""
        groups = match.groups()
        
        if len(groups) >= 3:
            year, month, day = groups[:3]
            
            # 주민등록번호 패턴인 경우 (2자리 연도)
            if len(year) == 2:
                year_int = int(year)
                if year_int >= 0 and year_int <= 30:
                    year = f"20{year_int:02d}"
                else:
                    year = f"19{year_int:02d}"
            elif len(year) == 2:
                year_int = int(year)
                year = f"20{year}" if year_int < 50 else f"19{year}"
                    
            return f"{year}-{int(month):02d}-{int(day):02d}"
            
        return ""


class TextCleaner:
    """텍스트 정리 유틸리티"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
            
        # 불필요한 공백 제거
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # 특수 문자 정리
        cleaned = re.sub(r'[^\w\s가-힣\(\)\[\].:：/-]', '', cleaned)
        
        return cleaned
    
    @staticmethod
    def normalize_spacing(text: str) -> str:
        """공백 정규화"""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def remove_page_markers(text: str) -> str:
        """페이지 마커 제거 (- 1 -, (1) 등)"""
        patterns = [
            r'-\s*\d+\s*-',
            r'\(\s*\d+\s*\)',
            r'page\s+\d+',
            r'\d+페이지'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        return text.strip()


class ScoreParser:
    """점수 파싱 유틸리티"""
    
    @staticmethod
    def parse_complex_score(score_text: str) -> Dict[str, Any]:
        """복합 점수 파싱"""
        result = {}
        
        if not score_text:
            return result
        
        score_text = score_text.strip()
        
        # 패턴 1: 원점수/평균(표준편차) 형태
        pattern_with_std = r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)\((\d+(?:\.\d+)?)\)'
        match = re.search(pattern_with_std, score_text)
        
        if match:
            result['raw_score'] = str(float(match.group(1)))
            result['subject_average'] = str(float(match.group(2)))
            result['standard_deviation'] = str(float(match.group(3)))
            return result
        
        # 패턴 2: 원점수/평균 형태 (괄호 없음)
        pattern_simple = r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)'
        match = re.search(pattern_simple, score_text)
        
        if match:
            result['raw_score'] = str(float(match.group(1)))
            result['subject_average'] = str(float(match.group(2)))
            return result
        
        # 패턴 3: 단순 점수
        try:
            if score_text.replace('.', '').replace('-', '').isdigit():
                result['raw_score'] = str(float(score_text))
        except ValueError:
            pass
        
        return result
    
    @staticmethod
    def clean_curriculum_text(text: str) -> str:
        """교과명 텍스트 정리 - 불규칙한 공백 제거"""
        if not text:
            return text
        
        # 기본 정리
        cleaned = text.strip()
        
        # 연속된 공백을 단일 공백으로
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 슬래시 앞뒤 공백 정리
        cleaned = re.sub(r'\s*/\s*', '/', cleaned)
        
        # 특수 문자 앞뒤 공백 정리
        cleaned = re.sub(r'\s*・\s*', '・', cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def parse_achievement_level(achievement_text: str) -> Dict[str, Any]:
        """성취도 파싱 (예: "C(186)")"""
        result = {}
        
        if not achievement_text:
            return result
        
        # 패턴: 성취도(수강자수)
        pattern = r'([A-F])\((\d+)\)'
        match = re.search(pattern, achievement_text.strip())
        
        if match:
            result['achievement_level'] = match.group(1)
            result['student_count'] = int(match.group(2))
        else:
            # 단순 성취도 - 상수 사용
            achievement_levels_str = ''.join(ScoreConstants.ACHIEVEMENT_LEVELS)
            if len(achievement_text) == 1 and achievement_text in achievement_levels_str:
                result['achievement_level'] = achievement_text
        
        return result


class ContentExtractor:
    """콘텐츠 추출 유틸리티"""
    
    @staticmethod
    def extract_subject_details(text: str) -> List[Dict[str, Any]]:
        """과목별 세부능력특기사항 추출"""
        details = []
        
        # 다양한 패턴으로 과목:내용 형태 추출
        patterns = [
            # (1학기)과목명: 내용
            r'\((\d)학기\)([가-힣\s]+?)\s*[:：]\s*(.*?)(?=\(\d학기\)|$)',
            # 과목명: 내용 (교과목 키워드 포함)
            r'([가-힣]+(?:과학|수학|국어|영어|사회|체육|음악|미술|기술|가정|정보|한문|윤리|지리|역사|물리|화학|생물|지구과학))\s*[:：]\s*([^:：]{50,}?)(?=[가-힣]+(?:과학|수학|국어|영어|사회|체육|음악|미술|기술|가정|정보|한문|윤리|지리|역사|물리|화학|생물|지구과학)\s*[:：]|$)',
            # 일반적인 과목명: 내용
            r'([가-힣]{2,10})\s*[:：]\s*([^:：]{50,}?)(?=[가-힣]{2,10}\s*[:：]|$)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                if len(match.groups()) == 3:  # (학기)과목명: 내용
                    semester = int(match.group(1))
                    subject = match.group(2).strip()
                    content = match.group(3).strip()
                else:  # 과목명: 내용
                    semester = None
                    subject = match.group(1).strip()
                    content = match.group(2).strip()
                
                if ContentValidator.is_valid_detail_record(subject, content):
                    details.append({
                        "subject": subject,
                        "content": content,
                        "semester": semester,
                        "extraction_method": "text_pattern"
                    })
        
        return details
    
    @staticmethod
    def extract_attendance_data(text: str) -> List[Dict[str, Any]]:
        """출결 데이터 추출"""
        records = []
        
        # 출결 패턴들
        patterns = [
            # 학년별 상세 출결
            r'(\d+)학년\s*(?:(\d+)학기)?\s*수업일수\s*(\d+)\s*출석일수\s*(\d+)\s*지각\s*(\d+)\s*조퇴\s*(\d+)\s*결석\s*(\d+)',
            # 간단한 형태
            r'(\d+)학년.*?출석\s*(\d+).*?지각\s*(\d+).*?조퇴\s*(\d+).*?결석\s*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                groups = match.groups()
                try:
                    if len(groups) >= 5:
                        grade = int(groups[0])
                        semester = int(groups[1]) if groups[1] and groups[1].isdigit() else 1
                        
                        if len(groups) == 7:  # 상세 패턴
                            records.append({
                                "grade": grade,
                                "semester": semester,
                                "school_days": int(groups[2]) if groups[2] else None,
                                "attendance_days": int(groups[3]) if groups[3] else None,
                                "tardiness_count": int(groups[4]) if groups[4] else 0,
                                "early_leave_count": int(groups[5]) if groups[5] else 0,
                                "absence_days": int(groups[6]) if groups[6] else 0
                            })
                        else:  # 간단한 패턴
                            records.append({
                                "grade": grade,
                                "semester": semester,
                                "attendance_days": int(groups[1]) if groups[1] else None,
                                "tardiness_count": int(groups[2]) if groups[2] else 0,
                                "early_leave_count": int(groups[3]) if groups[3] else 0,
                                "absence_days": int(groups[4]) if groups[4] else 0
                            })
                            
                except (ValueError, IndexError):
                    continue
        
        return records


class ContentValidator:
    """콘텐츠 검증 유틸리티"""
    
    @staticmethod
    def is_valid_student_name(name: str) -> bool:
        """유효한 학생 이름인지 확인"""
        if not name or len(name) < 2 or len(name) > 4:
            return False
            
        # 한글만 포함
        if not re.match(r'^[가-힣]+$', name):
            return False
            
        # 제외할 키워드 @TODO: 추후 상수 모음집으로 보낼예정    
        invalid_keywords = [
            "학년", "학교", "성명", "이름", "학생", "성별", "남성", "여성"
        ]
        
        return name not in invalid_keywords
    
    @staticmethod
    def is_valid_subject_name(subject: str) -> bool:
        """유효한 과목명인지 확인"""
        if not subject or len(subject) < 2 or len(subject) > 20:
            return False
            
        # 제외할 키워드 @TODO: 추후 상수 모음집으로 보낼예정
        exclude_keywords = [
            "세부능력", "특기사항", "과목", "교과", "헤더", "표", "페이지"
        ]
        
        return not any(keyword in subject for keyword in exclude_keywords)
    
    @staticmethod
    def is_valid_detail_record(subject: str, content: str) -> bool:
        """유효한 세부능력 레코드인지 확인"""
        if not ContentValidator.is_valid_subject_name(subject):
            return False
            
        if not content or len(content) < 20:
            return False
            
        return True
    
    @staticmethod
    def is_header_value(value: str) -> bool:
        """헤더 값인지 판단"""
        if not value:
            return True
            
        value_lower = value.lower()
        # 헤더 키워드 @TODO: 추후 상수 모음집으로 보낼예정
        header_keywords = [
            "원점수", "과목평균", "표준편차", "성취도", "성취수준", 
            "교과", "과목", "단위", "학점", "석차", "수강자", "인원",
            "학기", "학년", "계열", "영역", "세분류"
        ]
        
        return any(keyword in value_lower for keyword in header_keywords) 