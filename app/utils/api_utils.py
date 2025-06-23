"""
API 공통 헬퍼 static 함수들
"""

from typing import List, Dict, Any

from app.core.constants import ScoreConstants


class ScoreAPIHelper:
    """성적 API 헬퍼"""
    
    @staticmethod
    def get_main_subjects_list(target_subjects: List[str] | None = None) -> List[str]:
        """주요 과목 리스트 반환"""
        return target_subjects if target_subjects is not None else ScoreConstants.MAIN_SUBJECTS.copy()
    
    @staticmethod
    def categorize_subjects(subjects: List[str]) -> Dict[str, List[str]]:
        """과목을 주요/기타로 분류"""
        main_subjects = [s for s in subjects if s in ScoreConstants.MAIN_SUBJECTS]
        other_subjects = [s for s in subjects if s not in ScoreConstants.MAIN_SUBJECTS]
        return {
            "main_subjects": main_subjects,
            "other_subjects": other_subjects
        }
    
    @staticmethod
    def format_period_string(grade: int, semester: int) -> str:
        """학기 문자열 포맷"""
        return f"{grade}학년 {semester}학기"


class ResponseHelper:
    """응답 생성 헬퍼"""
    
    @staticmethod
    def create_success_response(data: Dict[str, Any], message: str) -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "success": True,
            "message": message,
            **data
        }
    
    @staticmethod
    def create_analysis_summary(available_items: List[str], requested_items: List[str]) -> Dict[str, Any]:
        """분석 요약 생성"""
        return {
            "available_items": available_items,
            "missing_items": [item for item in requested_items if item not in available_items],
            "found_count": len([item for item in requested_items if item in available_items]),
            "total_requested": len(requested_items)
        }