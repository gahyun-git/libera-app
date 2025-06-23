#!/usr/bin/env python3
"""
Libetion PDF Extractor Server
PostgreSQL 하이브리드 구조 기반 서버 실행
"""

import uvicorn
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def main():
    """서버 실행"""
    print("🚀 Libetion PDF Extractor 서버 시작")
    print(f"📊 데이터베이스: PostgreSQL 하이브리드 구조")
    print(f"📍 서버 주소: http://localhost:8000")
    print(f"📚 API 문서: http://localhost:8000/docs")
    print("-" * 50)
    
    # 업로드 디렉토리 생성
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # 서버 실행
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="debug"
    )


if __name__ == "__main__":
    main() 