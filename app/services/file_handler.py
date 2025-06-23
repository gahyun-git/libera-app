"""
파일 처리 서비스
"""
import logging
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileHandler:
    """파일 처리 클래스"""
    
    @staticmethod
    async def read_upload_file(file: UploadFile) -> bytes:
        """업로드 파일 읽기"""
        try:
            await file.seek(0)
            content = await file.read()
            
            if not content:
                raise ValueError("파일이 비어있습니다")
            
            return content
            
        except Exception as e:
            logger.error(f"파일 읽기 실패: {file.filename} - {e}")
            raise ValueError(f"파일 읽기 실패: {e}") from e 