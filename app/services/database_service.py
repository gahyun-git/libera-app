"""
데이터베이스 저장 서비스
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.student_repository import StudentRepository
from app.repositories.score_repository import ScoreRepository
from app.core.pdf_processor import ExtractedData

logger = logging.getLogger(__name__)


class DatabaseService:
   
    def __init__(self, db: AsyncSession):
        self.db = db
        self.student_repo = StudentRepository(db)
        self.score_repo = ScoreRepository(db)
    
    async def save_extracted_data(self, data: ExtractedData) -> int:
        """추출된 데이터를 데이터베이스에 저장"""
        try:
            # 학생 정보 저장/조회
            student = await self.student_repo.get_or_create(data.student_info)
            
            # 성적 데이터 저장
            scores_saved = await self.score_repo.batch_create(student.id, data.scores)
            
            # 커밋
            await self.db.commit()
            
            logger.info(f"데이터 저장 완료: 학생 ID {student.id}, 성적 {scores_saved}개")
            return student.id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"데이터베이스 저장 실패: {e}")
            raise Exception(f"데이터베이스 저장 실패: {str(e)}") 