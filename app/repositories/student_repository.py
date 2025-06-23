"""
학생 데이터 Repository
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.student import Student

logger = logging.getLogger(__name__)


class StudentRepository:
    """학생 데이터 접근"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_name(self, name: str) -> Optional[Student]:
        """이름으로 학생 조회"""
        result = await self.db.execute(
            select(Student).where(Student.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create(self, student_data: dict) -> Student:
        """새 학생 생성"""
        student = Student(
            name=student_data.get("name", "Unknown"),
            birth_date=student_data.get("birth_date"),
            gender=student_data.get("gender"),
            address=student_data.get("address")
        )
        self.db.add(student)
        await self.db.flush()  # ID 생성
        
        logger.info(f"새 학생 생성: {student.name} (ID: {student.id})")
        return student
    
    async def get_or_create(self, student_data: dict) -> Student:
        """학생 조회 후 없으면 생성"""
        student_name = student_data.get("name", "Unknown")
        
        # 기존 학생 확인
        student = await self.find_by_name(student_name)
        
        if not student:
            student = await self.create(student_data)
        else:
            logger.info(f"기존 학생 사용: {student_name} (ID: {student.id})")
        
        return student 