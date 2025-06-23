"""
데이터 변환 유틸리티
타입 변환 및 검증 static 함수들
"""
from datetime import datetime, date
from typing import Any, Optional, Union, Dict
import logging

logger = logging.getLogger(__name__)


class DataConverter:
    @staticmethod
    def to_safe_string(value: Any, max_length: Optional[int] = None) -> Optional[str]:
        """안전한 문자열 변환"""
        if value is None:
            return None
        
        try:
            # 숫자형을 문자열로 변환
            if isinstance(value, (int, float)):
                str_value = str(value)
            else:
                str_value = str(value).strip()
            
            # 길이 제한 적용
            if max_length and len(str_value) > max_length:
                str_value = str_value[:max_length]
                logger.warning(f"문자열 길이 초과로 잘림: {len(str_value)} -> {max_length}")
            
            return str_value if str_value else None
            
        except Exception as e:
            logger.warning(f"문자열 변환 실패: {value} -> {e}")
            return None
    
    @staticmethod
    def to_safe_date(value: Any) -> Optional[date]:
        """날짜 변환"""
        if value is None:
            return None
        
        try:
            # 이미 date 객체인 경우
            if isinstance(value, date):
                return value
            
            # datetime 객체인 경우
            if isinstance(value, datetime):
                return value.date()
            
            # 문자열인 경우
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                
                # 일반적인 날짜 형식들 시도
                formats = [
                    "%Y-%m-%d",
                    "%Y/%m/%d", 
                    "%Y.%m.%d",
                    "%Y년 %m월 %d일"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                
                logger.warning(f"지원하지 않는 날짜 형식: {value}")
                return None
            
            logger.warning(f"날짜 변환 불가능한 타입: {type(value)}")
            return None
            
        except Exception as e:
            logger.warning(f"날짜 변환 실패: {value} -> {e}")
            return None
    
    @staticmethod
    def to_safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
        """정수 변환"""
        if value is None:
            return default
        
        try:
            # 이미 정수인 경우
            if isinstance(value, int):
                return value
            
            # 실수인 경우
            if isinstance(value, float):
                return int(value)
            
            # 문자열인 경우
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return default
                
                # 숫자가 아닌 문자 제거 (예: "B(190)" -> "190")
                import re
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
                else:
                    return default
            
            return default
            
        except Exception as e:
            logger.warning(f"정수 변환 실패: {value} -> {e}")
            return default
    
    @staticmethod
    def clean_text(text: Any) -> Optional[str]:
        """텍스트 정리 - 개행문자, 공백 등 제거"""
        if text is None:
            return None
        
        try:
            cleaned = str(text).strip()
            # 개행문자를 공백으로 변경
            cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
            # 연속된 공백을 단일 공백으로
            cleaned = ' '.join(cleaned.split())
            
            return cleaned if cleaned else None
            
        except Exception as e:
            logger.warning(f"텍스트 정리 실패: {text} -> {e}")
            return None


class StudentDataConverter:
    """학생 데이터 전용 변환기"""
    
    @staticmethod
    def convert_student_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """학생 정보 변환"""
        return {
            "name": DataConverter.to_safe_string(raw_data.get("name"), 50),
            "birth_date": DataConverter.to_safe_date(raw_data.get("birth_date")),
            "gender": DataConverter.to_safe_string(raw_data.get("gender"), 10),
            "address": DataConverter.to_safe_string(raw_data.get("address"), 200)
        }


class ScoreDataConverter:
    """성적 데이터 전용 변환기"""
    
    @staticmethod
    def convert_score_record(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """성적 레코드 변환"""
        return {
            "grade": DataConverter.to_safe_int(raw_data.get("grade"), 1),
            "semester": DataConverter.to_safe_int(raw_data.get("semester"), 1),
            "curriculum": DataConverter.clean_text(raw_data.get("curriculum")) or "",
            "subject": DataConverter.clean_text(raw_data.get("subject")) or "",
            "subject_type": DataConverter.to_safe_string(raw_data.get("subject_type"), 20),
            "original_subject_name": DataConverter.to_safe_string(raw_data.get("original_subject_name"), 100),
            "raw_score": DataConverter.to_safe_string(raw_data.get("raw_score"), 20),
            "subject_average": DataConverter.to_safe_string(raw_data.get("subject_average"), 20),
            "standard_deviation": DataConverter.to_safe_string(raw_data.get("standard_deviation"), 20),
            "achievement_level": DataConverter.to_safe_string(raw_data.get("achievement_level"), 20),
            "student_count": DataConverter.to_safe_string(raw_data.get("student_count"), 10),
            "grade_rank": DataConverter.to_safe_string(raw_data.get("grade_rank"), 10),
            "credit_hours": DataConverter.to_safe_int(raw_data.get("credit_hours"))
        }
    
    @staticmethod
    def batch_convert_scores(raw_scores: list) -> list:
        """성적 배치 변환"""
        converted_scores = []
        
        for i, raw_score in enumerate(raw_scores):
            try:
                converted = ScoreDataConverter.convert_score_record(raw_score)
                converted_scores.append(converted)
            except Exception as e:
                logger.warning(f"성적 {i+1} 변환 실패: {e}")
                continue
        
        return converted_scores 