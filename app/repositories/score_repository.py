"""
성적 데이터 Repository
"""
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import Score

logger = logging.getLogger(__name__)


class ScoreRepository:
    """성적 데이터 접근 전담"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, student_id: int, score_data: dict) -> Score:
        """새 성적 생성"""
        score = Score(
            student_id=student_id,
            grade=score_data.get("grade"),
            semester=score_data.get("semester"),
            curriculum=score_data.get("curriculum"),
            subject=score_data.get("subject"),
            subject_type=score_data.get("subject_type"),
            original_subject_name=score_data.get("original_subject_name"),
            raw_score=score_data.get("raw_score"),
            subject_average=score_data.get("subject_average"),
            standard_deviation=score_data.get("standard_deviation"),
            achievement_level=score_data.get("achievement_level"),
            student_count=score_data.get("student_count"),
            grade_rank=score_data.get("grade_rank"),
            credit_hours=score_data.get("credit_hours")
        )
        self.db.add(score)
        return score
    
    async def batch_create(self, student_id: int, scores_data: List[dict]) -> int:
        """성적 배치 생성"""
        saved_count = 0
        
        for score_data in scores_data:
            try:
                await self.create(student_id, score_data)
                saved_count += 1
            except Exception as e:
                logger.warning(f"성적 저장 실패: {e}")
                continue
        
        return saved_count 