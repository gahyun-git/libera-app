"""
PDF 메타데이터 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class PDFMetadata(BaseModel):
    """PDF 파일 메타데이터"""
    __tablename__ = "pdf_metadata"

    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    
    # 파일 정보
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256
    file_size = Column(BigInteger, nullable=False)
    page_count = Column(Integer, default=0)
    
    # 처리 정보
    upload_timestamp = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime, default=datetime.now)
    processing_version = Column(String(20), default="1.0.0")
    
    # 관계
    student = relationship("Student", back_populates="pdf_metadata") 