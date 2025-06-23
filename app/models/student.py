"""
Student 모델
"""
from datetime import date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.score import Score


class Student(BaseModel):
    """학생 기본 정보 모델"""
    __tablename__ = "students"
    
    # 기본 개인정보
    name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        index=True,
        comment="학생 이름"
    )
    birth_date: Mapped[Optional[date]] = mapped_column(
        Date, 
        nullable=True,
        comment="생년월일"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(10), 
        nullable=True,
        comment="성별"
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(200), 
        nullable=True,
        comment="주소"
    )
    
    # Relationships (문자열 참조방식 사용 - 순환참조시 오류 발생했음)
    scores: Mapped[List["Score"]] = relationship(
        "Score", 
        back_populates="student", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name='{self.name}')>"
    