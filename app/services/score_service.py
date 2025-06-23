"""
성적 관련 서비스
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.score import Score
from app.models.student import Student
from app.utils.api_utils import ScoreAPIHelper
from app.core.constants import ScoreConstants


class ScoreService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_semester_scores_with_details(
        self, 
        student_id: int, 
        grade: int, 
        semester: int
    ) -> Dict[str, Any]:
        """
        학기별 전과목 성적 + 세부사항 통합 조회
        """
        student_task = self._get_student_info(student_id)
        scores_task = self._get_semester_scores(student_id, grade, semester)
        
        student_info, scores = await asyncio.gather(student_task, scores_task)
        
        # 성적 데이터 변환
        score_summaries = [self._create_score_summary(score) for score in scores]
        
        # 주요 과목 필터링
        main_subjects = [
            summary for summary in score_summaries 
            if summary["curriculum"] in ScoreConstants.MAIN_SUBJECTS
        ]
        
        return {
            "student_id": student_id,
            "student_name": student_info["name"],
            "grade": grade,
            "semester": semester,
            "period": self._format_period(grade, semester),
            "scores": score_summaries,
            "behavioral_record": "",  # TODO: 세부사항 모델 구현 후 추가
            "summary": {
                "total_subjects": len(scores),
                "available_curriculums": list({s.curriculum for s in scores}),
                "main_subjects": main_subjects,
                "main_subjects_count": len(main_subjects)
            }
        }
    
    async def get_main_subjects_flexible(
        self, 
        student_id: int, 
        target_subjects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        주요 과목 중 실제 수강한 것만 조회
        """
        if target_subjects is None:
            target_subjects = ScoreConstants.MAIN_SUBJECTS
        
        student_task = self._get_student_info(student_id)
        scores_task = self._get_scores_by_subjects(student_id, target_subjects)
        
        student_info, scores = await asyncio.gather(student_task, scores_task)
        
        score_summaries = [self._create_detailed_score_summary(score) for score in scores]
        
        return {
            "student_id": student_id,
            "student_name": student_info["name"],
            "target_subjects": target_subjects,
            "scores": score_summaries,
            "summary": {
                "total_subjects": len(scores),
                "available_subjects": list({s.curriculum for s in scores}),
                "requested_vs_available": {
                    "requested": len(target_subjects),
                    "available": len(set(s.curriculum for s in scores)),
                    "missing": [
                        subj for subj in target_subjects 
                        if subj not in {s.curriculum for s in scores}
                    ]
                }
            }
        }
    
    async def get_available_subjects(
        self, 
        student_id: int, 
        grade: int, 
        semester: int
    ) -> Dict[str, Any]:
        """
        특정 학기에 실제 수강한 과목 목록 조회
        """
        student_task = self._get_student_info(student_id)
        subjects_task = self._get_distinct_subjects(student_id, grade, semester)
        
        student_info, subjects = await asyncio.gather(student_task, subjects_task)
        
        # 과목 분류
        categorized = ScoreAPIHelper.categorize_subjects(subjects)
        
        return {
            "student_id": student_id,
            "student_name": student_info["name"],
            "grade": grade,
            "semester": semester,
            "period": self._format_period(grade, semester),
            "available_subjects": subjects,
            "total_count": len(subjects),
            **categorized
        }
    
    async def get_student_score_summary(self, student_id: int) -> Dict[str, Any]:
        """
        학생의 전체 수강 과목 종합 요약
        """
        student_task = self._get_student_info(student_id)
        all_scores_task = self._get_all_student_scores(student_id)
        
        student_info, all_scores = await asyncio.gather(student_task, all_scores_task)
        
        if not all_scores:
            return {
                "message": "수강 데이터가 없습니다.", 
                "total_subjects": 0,
                "student_id": student_id,
                "student_name": student_info["name"]
            }
        
        # 데이터 분석
        by_curriculum = self._group_by_curriculum(all_scores)
        by_period = self._group_by_period(all_scores)
        main_subjects_taken = [
            curr for curr in by_curriculum.keys() 
            if curr in ScoreConstants.MAIN_SUBJECTS
        ]
        
        return {
            "student_id": student_id,
            "student_name": student_info["name"],
            "total_subjects": len(all_scores),
            "unique_curriculums": list(by_curriculum.keys()),
            "main_subjects_taken": main_subjects_taken,
            "by_curriculum": by_curriculum,
            "by_period": by_period,
            "periods_studied": list(by_period.keys()),
            "statistics": {
                "main_subjects_percentage": round(
                    len(main_subjects_taken) / len(by_curriculum) * 100, 1
                ) if by_curriculum else 0,
                "total_periods": len(by_period),
                "avg_subjects_per_period": round(
                    len(all_scores) / len(by_period), 1
                ) if by_period else 0
            }
        }
    
    async def _get_student_info(self, student_id: int) -> Dict[str, Any]:
        """학생 기본 정보 조회"""
        result = await self.db.execute(
            select(Student.id, Student.name).filter(Student.id == student_id)
        )
        student = result.first()
        
        if not student:
            return {"id": student_id, "name": "Unknown Student"}
        
        return {"id": student.id, "name": student.name}
    
    async def _get_semester_scores(
        self, 
        student_id: int, 
        grade: int, 
        semester: int
    ) -> List[Score]:
        """특정 학기 성적 조회"""
        result = await self.db.execute(
            select(Score)
            .filter(
                Score.student_id == student_id,
                Score.grade == grade,
                Score.semester == semester
            )
            .order_by(Score.curriculum, Score.subject)
        )
        return list(result.scalars().all())
    
    async def _get_scores_by_subjects(
        self, 
        student_id: int, 
        subjects: List[str]
    ) -> List[Score]:
        """특정 과목들의 성적 조회"""
        result = await self.db.execute(
            select(Score)
            .filter(
                Score.student_id == student_id,
                Score.curriculum.in_(subjects)
            )
            .order_by(Score.grade, Score.semester, Score.curriculum)
        )
        return list(result.scalars().all())
    
    async def _get_distinct_subjects(
        self, 
        student_id: int, 
        grade: int, 
        semester: int
    ) -> List[str]:
        """특정 학기의 수강 과목 목록 조회"""
        result = await self.db.execute(
            select(Score.curriculum)
            .filter(
                Score.student_id == student_id,
                Score.grade == grade,
                Score.semester == semester
            )
            .distinct()
        )
        return list(result.scalars().all())
    
    async def _get_all_student_scores(self, student_id: int) -> List[Score]:
        """학생의 모든 성적 조회"""
        result = await self.db.execute(
            select(Score).filter(Score.student_id == student_id)
        )
        return list(result.scalars().all())
    
    def _create_score_summary(self, score: Score) -> Dict[str, Any]:
        """기본 성적 요약 생성"""
        return {
            "id": score.id,
            "curriculum": score.curriculum,
            "subject": score.subject,
            "raw_score": score.raw_score,
            "achievement_level": score.achievement_level,
            "grade_rank": score.grade_rank,
            "subject_average": score.subject_average,
            "credit_hours": score.credit_hours
        }
    
    def _create_detailed_score_summary(self, score: Score) -> Dict[str, Any]:
        """상세 성적 요약 생성"""
        return {
            "id": score.id,
            "grade": score.grade,
            "semester": score.semester,
            "curriculum": score.curriculum,
            "subject": score.subject,
            "subject_type": score.subject_type,
            "raw_score": score.raw_score,
            "achievement_level": score.achievement_level,
            "grade_rank": score.grade_rank,
            "subject_average": score.subject_average,
            "standard_deviation": score.standard_deviation,
            "credit_hours": score.credit_hours,
            "period": self._format_period(score.grade, score.semester)
        }
    
    def _group_by_curriculum(self, scores: List[Score]) -> Dict[str, List[Dict[str, Any]]]:
        """교과별 성적 그룹화"""
        grouped = {}
        for score in scores:
            curriculum = score.curriculum
            if curriculum not in grouped:
                grouped[curriculum] = []
            grouped[curriculum].append(self._create_detailed_score_summary(score))
        return grouped
    
    def _group_by_period(self, scores: List[Score]) -> Dict[str, List[str]]:
        """학기별 수강과목 그룹화"""
        grouped = {}
        for score in scores:
            period_key = self._format_period(score.grade, score.semester)
            if period_key not in grouped:
                grouped[period_key] = []
            grouped[period_key].append(score.curriculum)
        
        # 중복 제거
        return {k: list(set(v)) for k, v in grouped.items()}
    
    def _format_period(self, grade: int, semester: int) -> str:
        """학기 정보를 읽기 쉬운 형태로 변환"""
        return ScoreAPIHelper.format_period_string(grade, semester)