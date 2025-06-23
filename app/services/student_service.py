"""
Student 관련 서비스
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.student import Student
from app.models.score import Score
from app.schemas.converters import StudentConverter, ScoreConverter
from app.utils.score_utils import ScoreUtils
from app.utils.student_utils import StudentUtils
from app.core.constants import ScoreConstants


class StudentService:    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_student_profile(self, student_id: int) -> Optional[Student]:
        """학생 기본 프로필 조회"""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()
    
    async def list_students(
        self, 
        name: Optional[str] = None, 
        school: Optional[str] = None, 
        grade: Optional[int] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """학생 목록 조회"""
        
        query = select(Student)
        
        if name:
            query = query.where(Student.name.ilike(f"%{name}%"))
        
        if school:
            # current_school_name 필드가 없으므로 임시로 주석 처리 @TODO: 학교 정보 추가 예정
            pass
        
        if grade:
            if grade not in ScoreConstants.VALID_GRADES:
                raise ValueError(f"학년은 {ScoreConstants.VALID_GRADES} 중 하나여야 합니다.")
        
        # 총 개수 조회
        count_result = await self.db.execute(select(func.count(Student.id)))
        total = count_result.scalar_one()
        
        # 페이지네이션 적용
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        students = result.scalars().all()
        
        student_summaries = []
        for student in students:
            # 성적 개수 조회
            score_count_result = await self.db.execute(
                select(func.count(Score.id)).where(Score.student_id == student.id)
            )
            has_scores = score_count_result.scalar_one() > 0
            has_attendance = False  # 출결 모델이 없으므로 False @TODO: 출결 모델 추가 예정
            
            # 변환기 사용
            summary = StudentConverter.to_search_result(student, has_scores, has_attendance)
            student_summaries.append(summary)
        
        return {
            "total": total,
            "students": student_summaries,
            "filters": {"name": name, "school": school, "grade": grade}
        }
    
    async def get_student_statistics(self) -> Dict[str, Any]:
        """학생 통계 계산"""
        
        total_students = await self.db.execute(select(func.count(Student.id)))
        total_students = total_students.scalar_one()
        
        if total_students == 0:
            return {
                "total_students": 0,
                "data_completeness": {
                    "with_scores": 0,
                    "with_attendance": 0,
                    "with_academic_details": 0,
                    "with_school_history": 0,
                    "complete_profile": 0
                },
                "by_school": {},
                "by_grade": {1: 0, 2: 0, 3: 0},
                "by_gender": {"M": 0, "F": 0, "기타": 0},
                "data_coverage": {
                    "scores_coverage": 0.0,
                    "attendance_coverage": 0.0,
                    "details_coverage": 0.0,
                    "history_coverage": 0.0
                }
            }
        
        students = await self.db.execute(select(Student))
        students = students.scalars().all()
        
        school_stats = {}
        grade_stats = {1: 0, 2: 0, 3: 0}
        gender_stats = {"M": 0, "F": 0, "기타": 0}
        
        with_scores = 0
        
        for student in students:
            # 학교별 통계는 해당 필드가 없으므로 임시로 "-"으로 처리 @TODO: 학교 정보 추가 예정
            school_name = "-"
            if school_name not in school_stats:
                school_stats[school_name] = 0
            school_stats[school_name] += 1
            
            current_grade = 1
            if current_grade in grade_stats:
                grade_stats[current_grade] += 1
            
            student_gender = StudentUtils.normalize_gender(student.gender)
            if student_gender in ["M", "F"]:
                gender_stats[student_gender] += 1
            else:
                gender_stats["기타"] += 1
            
            if await self.db.execute(select(Score).where(Score.student_id == student.id)):
                with_scores += 1
        
        top_schools = sorted(school_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_students": total_students,
            "data_completeness": {
                "with_scores": with_scores,
                "with_attendance": 0,
                "with_academic_details": 0,
                "with_school_history": 0,
                "complete_profile": 0
            },
            "by_school": dict(top_schools),
            "by_grade": grade_stats,
            "by_gender": gender_stats,
            "data_coverage": {
                "scores_coverage": round(with_scores / total_students * 100, 2),
                "attendance_coverage": 0.0,
                "details_coverage": 0.0,
                "history_coverage": 0.0
            }
        }
    
    async def get_scores_by_grade(self, student_id: int, grades: Optional[List[int]] = None) -> Dict[str, List]:
        """학년별 성적 조회"""
        query = select(Score).where(Score.student_id == student_id)
        
        if grades:
            query = query.where(Score.grade.in_(grades))
        
        result = await self.db.execute(query)
        scores = result.scalars().all()
        
        result_dict = {}
        for score in scores:
            grade_key = f"{score.grade}학년"
            if grade_key not in result_dict:
                result_dict[grade_key] = []
            result_dict[grade_key].append(ScoreConverter.to_structured_format(score))
        
        return result_dict
    
    async def get_grade_statistics(self, student_id: int) -> Optional[Dict[str, Any]]:
        """성적 통계"""
        result = await self.db.execute(
            select(Score).where(Score.student_id == student_id)
        )
        scores = result.scalars().all()
        
        if not scores:
            return None
        
        total_subjects = len(scores)
        
        numeric_scores = []
        for score in scores:
            numeric_score = ScoreUtils.parse_numeric_score(score.raw_score)
            if numeric_score is not None:
                numeric_scores.append(numeric_score)
        
        if not numeric_scores:
            return {
                "total_subjects": total_subjects,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "numeric_scores_available": 0
            }
        
        total_score = sum(numeric_scores)
        avg_score = round(total_score / len(numeric_scores), 2)
        
        return {
            "total_subjects": total_subjects,
            "average_score": avg_score,
            "highest_score": max(numeric_scores),
            "lowest_score": min(numeric_scores),
            "numeric_scores_available": len(numeric_scores)
        }
    
    async def get_complete_profile(self, student_id: int) -> Dict[str, Any]:
        """학생 전체 프로필 (모든 정보 통합)"""
        student = await self.get_student_profile(student_id)
        if not student:
            return {"error": "학생을 찾을 수 없습니다."}
        
        # 변환기 사용
        basic_info = StudentConverter.to_basic_info(student)
        pdf_metadata = await self.get_pdf_metadata(student_id)
        scores_by_grade = await self.get_scores_by_grade(student_id)
        attendance_summary = await self.get_attendance_summary(student_id)
        grade_statistics = await self.get_grade_statistics(student_id)
        
        # 성적 데이터 변환
        all_scores = []
        for grade_scores in scores_by_grade.values():
            all_scores.extend(grade_scores)
        
        scores_data = {
            "total_records": len(all_scores),
            "records": all_scores
        }
        
        # 출결 데이터 변환 @TODO: 출결 데이터 추가 예정
        attendance_data = {
            "total_records": 0,
            "records": [],
            "summary": {"total_absence": 0, "total_tardiness": 0, "total_early_leave": 0}
        }
        
        # 세부사항과 학교 이력 @TODO: 세부사항과 학교 이력 추가 예정
        academic_details = {"total_records": 0, "records": []}
        school_history = {"total_records": 0, "records": [], "current_school": StudentUtils.get_default_school_name()}
        
        return {
            "basic_info": basic_info,
            "pdf_metadata": pdf_metadata,
            "scores": scores_data,
            "attendance": attendance_data,
            "academic_details": academic_details,
            "school_history": school_history,
            "grade_statistics": grade_statistics
        }
    
    async def get_pdf_metadata(self, student_id: int) -> Optional[Dict[str, Any]]:
        """PDF 메타데이터 조회 @TODO: PDF 메타데이터 추가 예정"""
        return None
    
    async def get_attendance_summary(self, student_id: int) -> Optional[Dict[str, Any]]:
        """출결 요약 정보 @TODO: 출결 요약 정보 추가 예정"""
        return None
    
    async def advanced_search(
        self,
        keyword: str,
        search_fields: Optional[list[str]] = None,
        min_grade: Optional[int] = None,
        max_grade: Optional[int] = None,
        has_scores: Optional[bool] = None,
        has_attendance: Optional[bool] = None,
        limit: int = 50
    ) -> dict[str, Any]:
        """고급 학생 검색"""
        
        if len(keyword.strip()) < 2:
            raise ValueError("검색 키워드는 2자 이상이어야 합니다.")
        
        if search_fields is None:
            search_fields = ["name"]  # school 필드가 없으므로 name만 @TODO: school 필드 추가 예정
        
        query = select(Student)
        
        search_conditions = []
        
        if "name" in search_fields:
            search_conditions.append(Student.name.ilike(f"%{keyword}%"))
        
        if "address" in search_fields:
            search_conditions.append(Student.address.ilike(f"%{keyword}%"))
        
        if search_conditions:
            query = query.where(or_(*search_conditions))
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        students = result.scalars().all()
        
        filtered_students = []
        
        for student in students:
            # 성적 개수 조회
            score_count_result = await self.db.execute(
                select(func.count(Score.id)).where(Score.student_id == student.id)
            )
            score_count = score_count_result.scalar_one()
            
            if has_scores is not None:
                if has_scores and score_count == 0:
                    continue
                if not has_scores and score_count > 0:
                    continue
            
            # 출결 데이터는 없으므로 항상 0 @TODO: 출결 데이터 추가 예정
            attendance_count = 0
            if has_attendance is not None:
                if has_attendance:
                    continue  # 출결 데이터가 없으므로 건너뛰기 @TODO: 출결 데이터 추가 예정
            
            result_dict = StudentConverter.to_search_result(student, score_count, attendance_count)
            filtered_students.append(result_dict)
        
        return {
            "keyword": keyword,
            "total_matches": len(filtered_students),
            "students": filtered_students,
            "search_criteria": {
                "keyword": keyword,
                "search_fields": search_fields,
                "grade_range": [min_grade, max_grade],
                "has_scores": has_scores,
                "has_attendance": has_attendance,
                "limit": limit
            }
        }
    

    async def build_student_basic_info(self, student: Student) -> Dict[str, Any]:
        """학생 기본 정보 구성"""
        return {
            "id": student.id,
            "name": student.name,
            "birth_date": str(student.birth_date) if student.birth_date else None,
            "gender": student.gender,
            "current_school_name": getattr(student, 'school_name', None)
        }
    
    async def get_scores_conditionally(self, student_id: int, include_scores: bool) -> Optional[List[Dict[str, Any]]]:
        """조건부 성적 정보 조회"""
        if not include_scores:
            return None
        
        scores_by_grade = await self.get_scores_by_grade(student_id)
        all_scores: List[Dict[str, Any]] = []
        for grade_scores in scores_by_grade.values():
            if isinstance(grade_scores, list):
                all_scores.extend(grade_scores)
        return all_scores
    
    async def get_attendance_conditionally(self, student_id: int, include_attendance: bool) -> Optional[List[Dict[str, Any]]]:
        """조건부 출결 정보 조회"""
        if not include_attendance:
            return None
        
        attendance_summary = await self.get_attendance_summary(student_id)
        # attendance_summary는 현재 None을 반환하므로 빈 리스트 반환 @TODO: 출결 데이터 추가 예정
        return [] if attendance_summary is None else [attendance_summary] if isinstance(attendance_summary, dict) else []
    
    async def get_details_conditionally(self, student_id: int, include_details: bool) -> Optional[Dict[str, Any]]:
        """조건부 세부사항 조회"""
        if not include_details:
            return None
        
        grade_statistics = await self.get_grade_statistics(student_id)
        return grade_statistics
    
    async def get_student_detailed_profile(
        self, 
        student_id: int,
        include_scores: bool = False,
        include_attendance: bool = False,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """학생 상세 프로필 조회 (조건부 데이터 포함)"""
        
        # 기본 프로필 조회
        profile_data = await self.get_student_profile(student_id)
        if not profile_data:
            raise ValueError("학생을 찾을 수 없습니다.")
        
        # 기본 정보 구성
        basic_info = await self.build_student_basic_info(profile_data)
        
        # 조건부 데이터 조회
        import asyncio
        scores_task = self.get_scores_conditionally(student_id, include_scores)
        attendance_task = self.get_attendance_conditionally(student_id, include_attendance)
        details_task = self.get_details_conditionally(student_id, include_details)
        
        scores_data, attendance_data, details_data = await asyncio.gather(
            scores_task, attendance_task, details_task
        )
        
        return {
            "student_id": student_id,
            "basic_info": basic_info,
            "scores": scores_data,
            "attendance": attendance_data,
            "academic_details": details_data
        } 