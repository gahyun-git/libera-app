# Libera App - AI 기반 PDF 성적 분석 시스템
이 내용은 cursor가 코드기반으로 작성해준것입니다..
테스트는 http://34.64.69.99:8001/docs
여기서 15번 학생 조회를 해보시면 됩니다!
다만.. 아직 구현이 덜 된 부분이 있어서 모두 동작하지는 않습니다.

## 📋 목차

- [시스템 개요](#시스템-개요)
- [기술 스택](#기술-스택)
- [데이터베이스 구조](#데이터베이스-구조)
- [API 아키텍처](#api-아키텍처)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [프로젝트 구조](#프로젝트-구조)
- [개발 가이드](#개발-가이드)
- [배포 가이드](#배포-가이드)

## 🎯 시스템 개요

### 주요 기능

#### 📄 PDF 처리 및 분석
- **멀티 포맷 PDF 지원**: 다양한 형태의 PDF 문서 업로드 및 파싱
- **AI 기반 데이터 추출**: Google Generative AI를 활용한 지능형 텍스트 분석
- **자동 데이터 분류**: 학생 정보, 성적, 출석 데이터 자동 분류 및 정규화
- **비동기 PDF 처리**: 대용량 PDF 파일의 효율적인 병렬 처리

#### 👥 학생 정보 관리
- **개인정보 관리**: 학번, 이름, 생년월일, 연락처 등 기본 정보
- **학급/학교 이력**: 재학 학교 및 학급 정보 관리
- **통합 검색**: 다양한 조건을 통한 학생 검색 및 필터링

#### 📊 성적 분석 및 관리
- **과목별 성적 추적**: 교과, 과목명, 원점수, 성취도 등 상세 정보
- **학기별 성적 비교**: 시간에 따른 성적 변화 추이 분석
- **통계 및 리포트**: 개별/전체 성적 통계 및 분석 리포트
- **데이터 내보내기**: Excel, CSV 형태로 성적 데이터 내보내기

#### 🔐 보안 및 인증
- **JWT 기반 인증**: 안전한 토큰 기반 사용자 인증
- **역할 기반 접근 제어**: 사용자 권한에 따른 세분화된 접근 제어
- **데이터 암호화**: 민감한 개인정보 보호

## 🛠 기술 스택

### Backend Framework
- **FastAPI** (0.109.0) - 고성능 비동기 API 프레임워크
- **Python** (3.11+) - 주 개발 언어
- **Uvicorn** - ASGI 서버

### Database & ORM
- **PostgreSQL** (13+) - 주 데이터베이스 (운영환경)
- **SQLite** - 개발/테스트 환경
- **SQLAlchemy 2.0** - ORM (비동기 지원)
- **AsyncPG** - PostgreSQL 비동기 드라이버
- **Alembic** - 데이터베이스 마이그레이션

### AI & Document Processing
- **Google Generative AI** - 텍스트 분석 및 데이터 추출
- **PDFPlumber** - PDF 텍스트 추출
- **PyMuPDF** - PDF 문서 처리
- **OpenAI GPT** - 보조 AI 분석

### Data Processing
- **Pandas** - 데이터 분석 및 처리
- **NumPy** - 수치 계산
- **OpenPyXL** - Excel 파일 처리

### Development & Testing
- **pytest** - 테스트 프레임워크
- **Black** - 코드 포맷터
- **MyPy** - 타입 체크

## 🗄 데이터베이스 구조

### ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    Student ||--o{ Score : has
    Student ||--o{ Attendance : has
    Student ||--o{ AcademicDetail : has
    Student ||--o{ SchoolHistory : has
    Student ||--o{ PDFMetadata : uploaded_by
    
    Student {
        int id PK
        string name
        date birth_date
        string gender
        string address
        string current_school_name
        string current_class_info
        datetime created_at
        datetime updated_at
    }
    
    Score {
        int id PK
        int student_id FK
        int grade
        int semester
        string curriculum
        string subject
        string subject_type
        string original_subject_name
        string raw_score
        string subject_average
        string standard_deviation
        string achievement_level
        string student_count
        string grade_rank
        int credit_hours
        datetime created_at
        datetime updated_at
    }
    
    Attendance {
        int id PK
        int student_id FK
        int grade
        int semester
        int absence_disease
        int absence_unexcused
        int tardiness_disease
        int tardiness_unexcused
        int early_leave_disease
        int early_leave_unexcused
        datetime created_at
        datetime updated_at
    }
    
    AcademicDetail {
        int id PK
        int student_id FK
        int grade
        int semester
        json detail_data
        datetime created_at
        datetime updated_at
    }
    
    SchoolHistory {
        int id PK
        int student_id FK
        int grade
        string school_name
        string class_info
        date start_date
        date end_date
        datetime created_at
        datetime updated_at
    }
    
    PDFMetadata {
        int id PK
        string original_filename
        string file_hash
        int file_size
        int page_count
        datetime upload_timestamp
        datetime processed_at
        string processing_version
        json extracted_data
        datetime created_at
        datetime updated_at
    }
```

### 주요 테이블 상세 설명

#### 1. Student (학생 기본 정보)
```sql
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    birth_date DATE,
    gender VARCHAR(10),
    address VARCHAR(200),
    current_school_name VARCHAR(100),
    current_class_info VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_student_name ON students(name);
CREATE INDEX idx_student_school ON students(current_school_name);
```

#### 2. Score (성적 정보)
```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 6),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 2),
    curriculum VARCHAR(20) NOT NULL,  -- 교과 (국어, 수학, 영어, 사회, 과학)
    subject VARCHAR(50) NOT NULL,     -- 과목명 (문학, 수학I, 물리학I)
    subject_type VARCHAR(20),         -- 과목 유형 (일반선택, 진로선택)
    original_subject_name VARCHAR(100), -- PDF 원본 과목명
    raw_score VARCHAR(20),            -- 원점수
    subject_average VARCHAR(20),      -- 과목평균
    standard_deviation VARCHAR(20),   -- 표준편차
    achievement_level VARCHAR(20),    -- 성취도 (A, B, C, D, E)
    student_count VARCHAR(10),        -- 수강자수
    grade_rank VARCHAR(10),           -- 석차등급 (1~9등급)
    credit_hours INTEGER,             -- 단위수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 성능 최적화 인덱스
CREATE INDEX idx_score_trend ON scores(student_id, curriculum, grade, semester);
CREATE INDEX idx_semester_scores ON scores(student_id, grade, semester);
CREATE INDEX idx_main_subjects ON scores(student_id, grade, semester, curriculum) 
    WHERE curriculum IN ('국어', '수학', '영어', '사회', '과학');
```

#### 3. 데이터 타입 및 제약조건

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `grade` | INTEGER | 1-6 | 학년 (초1~고3) |
| `semester` | INTEGER | 1-2 | 학기 |
| `curriculum` | VARCHAR(20) | NOT NULL | 교과명 |
| `achievement_level` | VARCHAR(20) | A,B,C,D,E | 성취도 |
| `grade_rank` | VARCHAR(10) | 1-9등급 | 석차등급 |

## 🏗 API 아키텍처

### 레이어 구조

```
┌─────────────────────────────────────┐
│            Router Layer             │  ← API 엔드포인트 정의
│   (health, students, scores, pdf)   │
├─────────────────────────────────────┤
│           Service Layer             │  ← 비즈니스 로직
│  (student_service, score_service,   │
│   pdf_service, database_service)    │
├─────────────────────────────────────┤
│         Repository Layer            │  ← 데이터 접근 계층
│ (student_repository, score_repository)│
├─────────────────────────────────────┤
│           Model Layer               │  ← 데이터베이스 모델
│    (Student, Score, PDFMetadata)    │
└─────────────────────────────────────┘
```

### 주요 서비스 모듈

#### 1. PDF Service (`app/services/pdf_service.py`)
- PDF 업로드 및 메타데이터 관리
- AI 기반 텍스트 추출 및 분석
- 데이터 정규화 및 검증

#### 2. Student Service (`app/services/student_service.py`)
- 학생 CRUD operations
- 검색 및 필터링
- 통계 데이터 생성

#### 3. Score Service (`app/services/score_service.py`)
- 성적 데이터 관리
- 성적 추이 분석
- 통계 및 리포트 생성

### 데이터 플로우

```mermaid
flowchart TD
    A[PDF Upload] --> B[PDF Parser]
    B --> C[AI Text Extraction]
    C --> D[Data Classification]
    D --> E{Data Type}
    
    E -->|Student Info| F[Student Service]
    E -->|Score Data| G[Score Service]
    E -->|Attendance| H[Attendance Service]
    
    F --> I[Student Repository]
    G --> J[Score Repository]
    H --> K[Attendance Repository]
    
    I --> L[(Database)]
    J --> L
    K --> L
    
    L --> M[API Response]
```

## 🚀 설치 및 실행

### 1. 시스템 요구사항
- **Python**: 3.11 이상
- **PostgreSQL**: 13 이상 (운영환경)
- **Memory**: 최소 4GB (PDF 처리용)
- **Storage**: 최소 10GB (업로드 파일용)

### 2. 환경 설정

#### 가상환경 생성
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

#### 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

#### 기본 설정 파일 복사
```bash
cp env.example .env
```

#### 필수 환경변수 설정
```bash
# .env 파일 편집
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=postgresql://user:password@localhost:5432/libera_db
GOOGLE_AI_API_KEY=your-google-ai-api-key
ENVIRONMENT=development
```

#### 환경별 설정 파일

| 환경 | 파일명 | 설명 |
|------|--------|------|
| 개발 | `.env.development` | 로컬 개발용 설정 |
| 테스트 | `.env.testing` | 테스트용 설정 |
| 운영 | `.env.production` | 운영 서버용 설정 |

### 4. 데이터베이스 설정

#### PostgreSQL 설치 및 데이터베이스 생성
```bash
# PostgreSQL 설치 (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# 데이터베이스 생성
sudo -u postgres createdb libera_db
sudo -u postgres createuser libera_user
sudo -u postgres psql -c "ALTER USER libera_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE libera_db TO libera_user;"
```

#### 데이터베이스 마이그레이션
```bash
# 마이그레이션 실행
alembic upgrade head

# 테스트 데이터 생성 (선택사항)
python -m app.core.init_db
```

### 5. 애플리케이션 실행

#### 개발 환경
```bash
ENVIRONMENT=development uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 운영 환경
```bash
ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Docker 실행 (선택사항)
```bash
# Docker 이미지 빌드
docker build -t libera-app .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env libera-app
```

### 6. 서비스 확인

| 서비스 | URL | 설명 |
|--------|-----|------|
| API 문서 | http://localhost:8000/docs | Swagger UI |
| 대안 문서 | http://localhost:8000/redoc | ReDoc |
| Health Check | http://localhost:8000/health | 서비스 상태 |

## 📚 API 문서

### 🏥 Health Check
```http
GET /health
GET /api/v1/health/database
GET /api/v1/health/ai-service
```

### 📄 PDF 관리
```http
POST   /api/v1/pdf/upload              # PDF 파일 업로드
GET    /api/v1/pdf/{pdf_id}            # PDF 메타데이터 조회
POST   /api/v1/pdf/{pdf_id}/process    # PDF 처리 및 데이터 추출
DELETE /api/v1/pdf/{pdf_id}            # PDF 삭제
GET    /api/v1/pdf/                    # PDF 목록 조회
```

### 👥 학생 관리
```http
GET    /api/v1/students                 # 학생 목록 조회
POST   /api/v1/students                 # 학생 생성
GET    /api/v1/students/{student_id}    # 학생 상세 조회
PUT    /api/v1/students/{student_id}    # 학생 정보 수정
DELETE /api/v1/students/{student_id}    # 학생 삭제
GET    /api/v1/students/search          # 학생 검색
GET    /api/v1/students/statistics      # 학생 통계
```

### 📊 성적 관리
```http
GET    /api/v1/scores                           # 성적 목록 조회
POST   /api/v1/scores                           # 성적 생성
GET    /api/v1/scores/{score_id}                # 성적 상세 조회
PUT    /api/v1/scores/{score_id}                # 성적 수정
DELETE /api/v1/scores/{score_id}                # 성적 삭제
GET    /api/v1/scores/student/{student_id}      # 학생별 성적 조회
GET    /api/v1/scores/student/{student_id}/trends  # 성적 추이 분석
GET    /api/v1/scores/export                    # 성적 데이터 내보내기
GET    /api/v1/scores/statistics                # 성적 통계
```

### API 요청/응답 예시

#### 학생 생성
```json
POST /api/v1/students
{
  "name": "홍길동",
  "birth_date": "2010-03-15",
  "gender": "남",
  "address": "서울시 강남구",
  "current_school_name": "OO중학교",
  "current_class_info": "1학년 3반"
}
```

#### 성적 조회 응답
```json
GET /api/v1/scores/student/1
{
  "student_id": 1,
  "student_name": "홍길동",
  "total_records": 24,
  "scores": [
    {
      "id": 1,
      "grade": 1,
      "semester": 1,
      "curriculum": "국어",
      "subject": "국어",
      "raw_score": "85",
      "achievement_level": "B",
      "subject_average": "78.5",
      "grade_rank": "3"
    }
  ]
}
```

## 📁 프로젝트 구조

```
libera_app/
├── app/                              # 메인 애플리케이션 
│   ├── main.py                       # FastAPI 애플리케이션 진입점
│   │
│   ├── core/                         # 핵심 기능 및 설정
│   │   ├── config.py                 # 애플리케이션 설정 관리
│   │   ├── constants.py              # 상수 정의 (학년, 교과 등)
│   │   ├── pdf_config.py             # PDF 처리 관련 설정
│   │   ├── pdf_parser.py             # PDF 파싱 엔진
│   │   ├── pdf_processor.py          # PDF 데이터 처리기
│   │   ├── attendance_extractor.py   # 출석 데이터 추출기
│   │   ├── detail_extractor.py       # 세부사항 추출기
│   │   └── grade_extractor.py        # 성적 데이터 추출기
│   │
│   ├── models/                       # SQLAlchemy 데이터베이스 모델
│   │   ├── __init__.py
│   │   ├── base.py                   # 기본 모델 클래스 (BaseModel)
│   │   ├── student.py                # 학생 모델
│   │   ├── score.py                  # 성적 모델
│   │   └── pdf_metadata.py           # PDF 메타데이터 모델
│   │
│   ├── schemas/                      # Pydantic 데이터 검증 스키마
│   │   ├── __init__.py
│   │   ├── base.py                   # 기본 스키마 클래스
│   │   ├── student.py                # 학생 관련 스키마
│   │   ├── scores.py                 # 성적 관련 스키마
│   │   ├── pdf.py                    # PDF 관련 스키마
│   │   └── converters.py             # 데이터 변환 유틸리티
│   │
│   ├── routers/                      # FastAPI 라우터 (API 엔드포인트)
│   │   ├── __init__.py
│   │   ├── health.py                 # 헬스체크 API
│   │   ├── students.py               # 학생 관리 API
│   │   ├── scores.py                 # 성적 관리 API
│   │   └── pdf.py                     # PDF 처리 API
│   │
│   ├── services/                     # 비즈니스 로직 서비스
│   │   ├── __init__.py
│   │   ├── database_service.py       # 데이터베이스 연결 관리
│   │   ├── student_service.py        # 학생 관련 비즈니스 로직
│   │   ├── score_service.py          # 성적 관련 비즈니스 로직
│   │   ├── pdf_service.py            # PDF 처리 비즈니스 로직
│   │   ├── file_handler.py           # 파일 업로드/다운로드 처리
│   │   └── job_service.py            # 비동기 작업 관리
│   │
│   ├── repositories/                 # 데이터 접근 계층
│   │   ├── __init__.py
│   │   ├── student_repository.py     # 학생 데이터 접근
│   │   └── score_repository.py       # 성적 데이터 접근
│   │
│   └── utils/                        # 유틸리티 함수
│       ├── __init__.py
│       ├── api_utils.py              # API 관련 유틸리티
│       ├── pdf_utils.py              # PDF 처리 유틸리티
│       ├── text_utils.py             # 텍스트 처리 유틸리티
│       ├── data_converter.py         # 데이터 변환 유틸리티
│       ├── validation_utils.py       # 데이터 검증 유틸리티
│       ├── student_utils.py          # 학생 데이터 유틸리티
│       └── score_utils.py            # 성적 처리 유틸리티
│
├── uploads/                          # 업로드된 파일 저장소
├── backup_student2/                  # 테스트 데이터 백업
├── requirements.txt                  # Python 의존성 패키지
├── env.example                       # 환경변수 예제 파일
├── .gitignore                        # Git 제외 파일 목록
├── run_server.py                     # 서버 실행 스크립트
└── README.md                         # 프로젝트 문서
```

### 모듈별 역할 상세 설명

#### Core 모듈 (`app/core/`)
- **config.py**: 환경변수, 데이터베이스 설정, API 설정 통합 관리
- **constants.py**: 학년(1-6), 학기(1-2), 교과목 등 시스템 상수 정의
- **pdf_parser.py**: PDF 파일 읽기, 텍스트/테이블 추출 핵심 엔진
- **extractors/**: AI 기반 데이터 분류 및 추출 모듈들

#### Models 모듈 (`app/models/`)
- SQLAlchemy 2.0 기반 비동기 ORM 모델
- 관계 설정, 인덱스, 제약조건 정의
- 데이터베이스 스키마와 1:1 매핑

#### Services 모듈 (`app/services/`)
- 비즈니스 로직의 핵심 구현
- Repository 패턴을 통한 데이터 접근
- 트랜잭션 관리 및 에러 처리

#### Routers 모듈 (`app/routers/`)
- RESTful API 엔드포인트 정의
- 요청/응답 스키마 연결
- HTTP 상태 코드 및 예외 처리

## 👨‍💻 개발 가이드

### 코드 스타일 및 품질

#### 자동 포맷팅
```bash
# 코드 포맷팅 (Black)
black app/ --line-length 88

# Import 정렬 (isort)
isort app/ --profile black

# 타입 체크 (MyPy)
mypy app/ --ignore-missing-imports
```

#### 린팅
```bash
# Flake8 (PEP8 준수)
flake8 app/ --max-line-length=88 --extend-ignore=E203,W503

# 보안 검사 (Bandit)
bandit -r app/ -f json -o security-report.json
```

### 테스트

#### 테스트 실행
```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 실행
pytest --cov=app --cov-report=html --cov-report=term

# 특정 모듈 테스트
pytest tests/test_student_service.py -v

# 병렬 테스트 실행
pytest -n auto
```

#### 테스트 구조
```
tests/
├── unit/                    # 단위 테스트
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # 통합 테스트
│   ├── test_api.py
│   └── test_database.py
└── fixtures/                # 테스트 데이터
    ├── sample_pdfs/
    └── test_data.json
```

### 데이터베이스 마이그레이션

#### 새 마이그레이션 생성
```bash
# 모델 변경 후 마이그레이션 파일 생성
alembic revision --autogenerate -m "Add attendance table"

# 빈 마이그레이션 파일 생성
alembic revision -m "Custom migration"
```

#### 마이그레이션 관리
```bash
# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 이력 확인
alembic history --verbose

# 특정 버전으로 롤백
alembic downgrade -1
alembic downgrade base

# 특정 버전으로 업그레이드
alembic upgrade head
alembic upgrade +2
```

### API 개발 가이드

#### 새 API 엔드포인트 추가
1. **스키마 정의** (`app/schemas/`)
```python
class NewFeatureCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
```

2. **모델 정의** (`app/models/`)
```python
class NewFeature(BaseModel):
    __tablename__ = "new_features"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

3. **서비스 로직** (`app/services/`)
```python
class NewFeatureService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: NewFeatureCreate) -> NewFeature:
        # 비즈니스 로직 구현
        pass
```

4. **라우터 등록** (`app/routers/`)
```python
@router.post("/", response_model=NewFeatureResponse)
async def create_feature(
    data: NewFeatureCreate,
    db: AsyncSession = Depends(get_db)
):
    service = NewFeatureService(db)
    return await service.create(data)
```

### 성능 최적화

#### 데이터베이스 최적화
- **인덱스 활용**: 자주 조회되는 컬럼에 인덱스 생성
- **N+1 쿼리 방지**: `selectinload()`, `joinedload()` 사용
- **배치 처리**: 대량 데이터 처리시 배치 단위로 분할

#### 비동기 처리
```python
# 동시 처리 예시
async def process_multiple_pdfs(pdf_files: List[UploadFile]):
    tasks = [process_pdf(pdf) for pdf in pdf_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## 🚀 배포 가이드

### Docker 배포

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/libera_db
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: libera_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 운영 환경 배포

#### 시스템 서비스 등록 (Linux)
```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/libera-app.service
```

```ini
[Unit]
Description=Libera FastAPI App
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/libera-app
Environment=PATH=/opt/libera-app/venv/bin
ExecStart=/opt/libera-app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable libera-app
sudo systemctl start libera-app
```

#### Nginx 리버스 프록시 설정
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. PDF 처리 실패
```bash
# 원인 진단
- PDF 파일 형식 확인 (지원: PDF 1.4-1.7)
- 파일 크기 확인 (권장: 50MB 이하)
- 메모리 사용량 확인
- Google AI API 키 유효성 확인
- API 할당량 확인

# 해결 방법
- PDF 파일 최적화
- 메모리 증설 또는 청크 단위 처리
- API 키 갱신
```

#### 2. 데이터베이스 연결 오류
```bash
# 원인 진단
- DATABASE_URL 환경변수 확인
- PostgreSQL 서버 상태 확인
- 네트워크 연결 확인
- 방화벽 설정 확인

# 해결 방법
psql -h localhost -U username -d database_name
sudo systemctl status postgresql
sudo ufw allow 5432
```

#### 3. AI API 오류
```bash
# 원인 진단 및 해결
- API 키 확인: echo $GOOGLE_AI_API_KEY
- 할당량 확인: Google Cloud Console
- 네트워크 확인: curl -I https://generativelanguage.googleapis.com
```

### 로그 분석

#### 애플리케이션 로그
```bash
# 실시간 로그 확인
tail -f logs/app.log

# 에러 로그만 필터링
grep "ERROR" logs/app.log | tail -20

# 특정 기간 로그 확인
journalctl -u libera-app --since "2024-01-01" --until "2024-01-02"
```

#### 성능 모니터링
```bash
# 메모리 사용량
ps aux | grep uvicorn
free -h

# CPU 사용률
top -p $(pgrep -f uvicorn)

# 데이터베이스 연결
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## 📞 지원 및 문의

- **개발팀 이메일**: dev@libera.com
- **이슈 트래킹**: GitHub Issues
- **문서 업데이트**: 개발팀원 누구나 기여 가능

---

**Last Updated**: 2024년 1월  
**Version**: 2.0.0  
**Maintainer**: Libera Development Team
