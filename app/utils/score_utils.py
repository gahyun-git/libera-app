"""
Score 관련 유틸리티 static 함수들
"""
from typing import Optional
from app.core.constants import ScoreConstants


class ScoreUtils:
    """점수 관련 유틸리티"""
    
    @staticmethod
    def parse_numeric_score(raw_score: Optional[str]) -> Optional[float]:
        """숫자형 점수 추출"""
        if not raw_score:
            return None
        
        try:
            # "82/71.5(14.1)" 형태에서 첫 번째 숫자만 추출
            score_str = str(raw_score).split('/')[0].split('(')[0].strip()
            if not score_str:
                return None
            
            return float(score_str) if score_str.replace('.', '').isdigit() else None
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def is_main_subject(curriculum: str) -> bool:
        """주요 과목 여부 판단"""
        return curriculum in ScoreConstants.MAIN_SUBJECTS
    