"""
데이터 변환 클래스
모델 데이터를 클라이언트에 전달하기 위한 형식으로 변환
클래스 메서드가 아닌 정적 메서드로 선언하여 인스턴스 생성 없이 다른 클래스에서 호출 하기위함
"""
from typing import Dict, Any
import re
from app.models.student import Student
from app.utils.score_utils import ScoreUtils
from app.utils.student_utils import StudentUtils
from app.utils.text_utils import ScoreParser


class StudentConverter:
    @staticmethod
    def to_basic_info(student: Student) -> Dict[str, Any]:
        return {
            "id": student.id,
            "name": student.name or "Unknown",
            "birth_date": StudentUtils.format_birth_date(student.birth_date),
            "gender": student.gender,
            "address": student.address,
        }

    @staticmethod
    def to_summary(student: Student) -> Dict[str, Any]:
        return {
            "id": student.id,
            "name": student.name or "Unknown",
            "birth_date": StudentUtils.format_birth_date(student.birth_date),
            "gender": student.gender,
            "created_at": StudentUtils.format_datetime(student.created_at)
        }

    @staticmethod
    def to_search_result(student, scores_count: int = 0, attendance_count: int = 0) -> Dict[str, Any]:
        return {
            "id": student.id,
            "name": student.name or "Unknown",
            "birth_date": StudentUtils.format_birth_date(student.birth_date),
            "gender": student.gender,
            "current_school_name": StudentUtils.get_default_school_name(),
            "scores_count": scores_count,
            "attendance_count": attendance_count
        }


class ScoreConverter:
    @staticmethod
    def extract_student_count(student_count_str: str) -> int:
        """student_count에서 숫자만 추출 (예: 'A(190)' -> 190)"""
        if not student_count_str:
            return 0
        
        # 괄호 안의 숫자 추출
        match = re.search(r'\((\d+)\)', student_count_str)
        if match:
            return int(match.group(1))
        
        # 괄호가 없고 숫자만 있는 경우
        match = re.search(r'\d+', student_count_str)
        if match:
            return int(match.group())
        
        return 0
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트에서 개행문자 및 불필요한 공백 제거"""
        if not text:
            return text
        
        # 개행문자 제거 및 연속된 공백을 하나로 통합
        cleaned = re.sub(r'\s+', ' ', text.replace('\n', '').replace('\r', ''))
        return cleaned.strip()
    
    @staticmethod
    def to_summary(score) -> Dict[str, Any]:
        return {
            "id": score.id,
            "curriculum": score.curriculum,
            "subject": score.subject,
            "raw_score": score.raw_score,
            "achievement_level": score.achievement_level,
            "credit_hours": score.credit_hours,
            "period": f"{score.grade}학년 {score.semester}학기",
            "numeric_score": ScoreUtils.parse_numeric_score(score.raw_score),
            "is_main_subject": ScoreUtils.is_main_subject(score.curriculum)
        }

    @staticmethod
    def to_detailed_info(score) -> Dict[str, Any]:
        return {
            "id": score.id,
            "grade": score.grade,
            "semester": score.semester,
            "curriculum": score.curriculum,
            "subject": score.subject,
            "subject_type": score.subject_type,
            "raw_score": score.raw_score,
            "subject_average": score.subject_average,
            "standard_deviation": score.standard_deviation,
            "achievement_level": score.achievement_level,
            "student_count": score.student_count,
            "grade_rank": score.grade_rank,
            "credit_hours": score.credit_hours,
            "numeric_score": ScoreUtils.parse_numeric_score(score.raw_score),
            "is_main_subject": ScoreUtils.is_main_subject(score.curriculum)
        }

    @staticmethod
    def to_structured_format(score) -> Dict[str, Any]:
        """구조화된 성적 정보 형식으로 변환"""
        return {
            "period": f"{score.grade}학년 {score.semester}학기",
            "subject_info": {
                "curriculum": ScoreParser.clean_curriculum_text(score.curriculum or ""),
                "subject": ScoreConverter.clean_text(score.subject or ""),
                "is_main_subject": ScoreUtils.is_main_subject(score.curriculum),
                "credit_hours": score.credit_hours
            },
            "performance": {
                "raw_score": score.raw_score,
                "subject_average": score.subject_average,
                "standard_deviation": score.standard_deviation,
                "achievement_level": score.achievement_level,
                "student_count": ScoreConverter.extract_student_count(score.student_count),
                "grade_rank": score.grade_rank
            }
        }