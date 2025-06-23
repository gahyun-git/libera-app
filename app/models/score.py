"""
Score 모델
"""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, CheckConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.models.base import BaseModel
from app.core.constants import ScoreConstants

if TYPE_CHECKING:
    from app.models.student import Student

class Score(BaseModel):
    """성적 정보 모델"""
    __tablename__ = "scores"
    
    # 외래키 - 타입 힌트 포함
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="학생 ID"
    )
    
    # 학년/학기 정보
    grade: Mapped[int] = mapped_column(
        nullable=False,
        comment= str(ScoreConstants.VALID_GRADES)
    )
    semester: Mapped[int] = mapped_column(
        nullable=False,
        comment= str(ScoreConstants.VALID_SEMESTERS)
    )
    
    # 과목 정보
    curriculum: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="교과 (국어, 수학, 영어, 사회, 과학, 체육, 음악 등)"
    )
    subject: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="과목명 (문학, 수학I, 물리학I 등)"
    )
    subject_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment= str(ScoreConstants.SUBJECT_TYPES)
    )
    original_subject_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="PDF에서 추출된 원본 과목명"
    )
    
    # 성적 정보 (원본 데이터 보존)
    raw_score: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="원점수"
    )
    subject_average: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="과목평균"
    )
    standard_deviation: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="표준편차"
    )
    achievement_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="성취도"
    )
    student_count: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="수강자수"
    )
    grade_rank: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="석차등급"
    )
    
    # 교육과정 정보
    credit_hours: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="단위수"
    )
    
    # 제약조건 및 인덱스
    __table_args__ = (
        CheckConstraint(f'grade >= {min(ScoreConstants.VALID_GRADES)} AND grade <= {max(ScoreConstants.VALID_GRADES)}', name='check_grade_range'),
        CheckConstraint(f'semester >= {min(ScoreConstants.VALID_SEMESTERS)} AND semester <= {max(ScoreConstants.VALID_SEMESTERS)}', name='check_semester_range'),
        CheckConstraint('credit_hours IS NULL OR credit_hours >= 1', name='check_credit_hours_positive'),
        
        # 성적 추이 분석 최적화 인덱스
        Index('idx_score_trend', 'student_id', 'curriculum', 'grade', 'semester'),
        
        # 학기별 성적 조회 최적화
        Index('idx_semester_scores', 'student_id', 'grade', 'semester'),
        
        # 주요 과목 필터링 최적화 (부분 인덱스)
        Index('idx_main_subjects', 'student_id', 'grade', 'semester', 'curriculum',
              postgresql_where=text(f"curriculum IN {tuple(ScoreConstants.MAIN_SUBJECTS)}")),
        
        # 전체 성적 조회 최적화
        Index('idx_all_scores', 'student_id', 'grade', 'semester', 'curriculum', 'subject'),
    )
    
    # 관계 설정 (문자열 참조방식 사용 - 순환참조시 오류 발생했음)
    student: Mapped["Student"] = relationship("Student", back_populates="scores")

    def __repr__(self) -> str:
        return f"<Score(student_id={self.student_id}, {self.grade}학년 {self.semester}학기, {self.curriculum}-{self.subject})>"

    @validates('grade')
    def validate_grade(self, key: str, grade: int) -> int:
        if grade not in ScoreConstants.VALID_GRADES:
            raise ValueError(f'학년은 {ScoreConstants.VALID_GRADES} 중 하나여야 합니다')
        return grade

    @validates('semester') 
    def validate_semester(self, key: str, semester: int) -> int:
        if semester not in ScoreConstants.VALID_SEMESTERS:
            raise ValueError(f'학기는 {ScoreConstants.VALID_SEMESTERS} 중 하나여야 합니다')
        return semester
    