"""
애플리케이션 상수 정의
"""

# 성적 관련 상수
class ScoreConstants:
    """성적 관련 상수"""
    
    # 주요 과목 리스트
    MAIN_SUBJECTS = ['국어', '영어', '수학', '사회', '과학']
    SUBJECT_TYPES = ['일반선택', '진로선택']
    
    # 학년/학기 범위
    VALID_GRADES = [1, 2, 3]
    VALID_SEMESTERS = [1, 2]
    
    # 성취도 레벨
    ACHIEVEMENT_LEVELS = ['A', 'B', 'C', 'D', 'E']
    
    # 테이블명
    TABLE_NAME = "scores"

# 에러 메시지
class ErrorMessages:
    """에러 메시지 상수"""
    
    STUDENT_NOT_FOUND = "학생을 찾을 수 없습니다."
    NO_SCORE_DATA = "성적 데이터를 찾을 수 없습니다."
    INVALID_GRADE = "학년은 1-3 사이여야 합니다."
    INVALID_SEMESTER = "학기는 1-2 사이여야 합니다."
    INVALID_PERIOD_FORMAT = "각 기간은 'grade'와 'semester' 필드가 필요합니다."
    
    @staticmethod
    def no_semester_data(grade: int, semester: int) -> str:
        return f"{grade}학년 {semester}학기 성적 데이터를 찾을 수 없습니다."
    
    @staticmethod
    def no_subject_data(subjects: list) -> str:
        return f"해당 과목들({', '.join(subjects)})의 성적 데이터를 찾을 수 없습니다."

# 성공 메시지  
class SuccessMessages:
    """성공 메시지 상수"""
    
    @staticmethod
    def semester_scores_retrieved(grade: int, semester: int) -> str:
        return f"{grade}학년 {semester}학기 성적을 성공적으로 조회했습니다."
    
    @staticmethod
    def subjects_retrieved(grade: int, semester: int) -> str:
        return f"{grade}학년 {semester}학기 수강 과목을 성공적으로 조회했습니다."
    
    TRENDS_ANALYZED = "과목별 성적 추이를 성공적으로 분석했습니다."
    MAIN_SUBJECTS_RETRIEVED = "주요 과목 성적을 성공적으로 조회했습니다."
    COMPARISON_COMPLETED = "학기별 성적 비교를 성공적으로 완료했습니다."
    SUMMARY_RETRIEVED = "학생 성적 요약을 성공적으로 조회했습니다."
    FLEXIBLE_QUERY_COMPLETED = "유연한 성적 조회를 성공적으로 완료했습니다."

class PDFConstants:
    """PDF 처리 관련 상수"""
    
    # 파일 제한
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILES_COUNT = 10
    ALLOWED_EXTENSIONS = [".pdf"]
    
    # 처리 상태
    class ProcessingStatus:
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        ERROR = "error"
    
    # 파서 버전
    PARSER_VERSION = "2.0.0"
    ENHANCED_PARSER_VERSION = "2.0.0-enhanced"
    
    # 업로드 설정
    UPLOAD_DIR_DEFAULT = "uploads"
    TEMP_FILE_PREFIX = "libetion_"

class PDFErrorMessages:
    """PDF 관련 에러 메시지"""
    
    INVALID_FILE_TYPE = "PDF 파일만 업로드 가능합니다."
    FILE_TOO_LARGE = f"파일 크기는 {PDFConstants.MAX_FILE_SIZE // (1024*1024)}MB 이하여야 합니다."
    TOO_MANY_FILES = f"최대 {PDFConstants.MAX_FILES_COUNT}개까지만 업로드 가능합니다."
    FILE_NOT_FOUND = "파일을 찾을 수 없습니다."
    JOB_NOT_FOUND = "작업을 찾을 수 없습니다."
    PROCESSING_FAILED = "PDF 처리 중 오류가 발생했습니다."
    
    @staticmethod
    def invalid_file_in_batch(filename: str) -> str:
        return f"PDF 파일만 업로드 가능합니다. 문제 파일: {filename or '파일명 없음'}"
    
    @staticmethod
    def processing_error(filename: str, error: str) -> str:
        return f"파일 처리 중 오류 발생 ({filename}): {error}"

class PDFSuccessMessages:
    """PDF 관련 성공 메시지"""
    
    UPLOAD_COMPLETED = "PDF 처리가 완료되었습니다."
    
    @staticmethod
    def batch_upload_started(count: int) -> str:
        return f"{count}개 파일 처리를 시작했습니다."
    
    @staticmethod
    def single_upload_completed(filename: str) -> str:
        return f"파일 '{filename}' 처리가 완료되었습니다." 