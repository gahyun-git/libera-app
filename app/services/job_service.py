"""
작업 관리 서비스
"""

import uuid
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class JobRecord:
    """작업 레코드 데이터 클래스"""
    job_id: str
    status: str = "processing"
    progress: int = 0
    total: int = 0
    completed: int = 0
    failed: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobRecord":
        """딕셔너리에서 생성"""
        return cls(**data)


class JobStorage(ABC):
    """작업 저장소 추상 인터페이스"""
    
    @abstractmethod
    async def create_job(self, job_id: str, total_files: int) -> JobRecord:
        """작업 생성"""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[JobRecord]:
        """작업 조회"""
        pass
    
    @abstractmethod
    async def update_job(self, job_id: str, **updates) -> bool:
        """작업 업데이트"""
        pass
    
    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """작업 삭제"""
        pass
    
    @abstractmethod
    async def list_jobs(self) -> List[JobRecord]:
        """모든 작업 목록"""
        pass


class InMemoryJobStorage(JobStorage):
    """메모리 기반 작업 저장소"""
    
    def __init__(self):
        self._storage: Dict[str, JobRecord] = {}
    
    async def create_job(self, job_id: str, total_files: int) -> JobRecord:
        """작업 생성"""
        job_record = JobRecord(
            job_id=job_id,
            total=total_files
        )
        self._storage[job_id] = job_record
        return job_record
    
    async def get_job(self, job_id: str) -> Optional[JobRecord]:
        """작업 조회"""
        return self._storage.get(job_id)
    
    async def update_job(self, job_id: str, **updates) -> bool:
        """작업 업데이트"""
        if job_id not in self._storage:
            return False
        
        job = self._storage[job_id]
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        return True
    
    async def delete_job(self, job_id: str) -> bool:
        """작업 삭제"""
        if job_id in self._storage:
            del self._storage[job_id]
            return True
        return False
    
    async def list_jobs(self) -> List[JobRecord]:
        """모든 작업 목록"""
        return list(self._storage.values())


class RedisJobStorage(JobStorage):
    """Redis 기반 작업 저장소 (추후 구현시 사용)"""
    
    def __init__(self, redis_client, key_prefix: str = "job:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _get_key(self, job_id: str) -> str:
        """Redis 키 생성"""
        return f"{self.key_prefix}{job_id}"
    
    async def create_job(self, job_id: str, total_files: int) -> JobRecord:
        """작업 생성"""
        job_record = JobRecord(
            job_id=job_id,
            total=total_files
        )
        
        key = self._get_key(job_id)
        await self.redis.set(key, json.dumps(job_record.to_dict()))
        await self.redis.expire(key, 86400)  # 24시간 TTL
        
        return job_record
    
    async def get_job(self, job_id: str) -> Optional[JobRecord]:
        """작업 조회"""
        key = self._get_key(job_id)
        data = await self.redis.get(key)
        
        if data is None:
            return None
        
        return JobRecord.from_dict(json.loads(data))
    
    async def update_job(self, job_id: str, **updates) -> bool:
        """작업 업데이트"""
        job = await self.get_job(job_id)
        if job is None:
            return False
        
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        redis_key = self._get_key(job_id)
        await self.redis.set(redis_key, json.dumps(job.to_dict()))
        
        return True
    
    async def delete_job(self, job_id: str) -> bool:
        """작업 삭제"""
        key = self._get_key(job_id)
        result = await self.redis.delete(key)
        return result > 0
    
    async def list_jobs(self) -> List[JobRecord]:
        """모든 작업 목록"""
        pattern = f"{self.key_prefix}*"
        keys = await self.redis.keys(pattern)
        
        jobs = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                jobs.append(JobRecord.from_dict(json.loads(data)))
        
        return jobs


class JobService:
    """작업 관리 서비스"""
    
    def __init__(self, storage: JobStorage):
        self.storage = storage
    
    def generate_job_id(self) -> str:
        """고유한 작업 ID 생성"""
        return str(uuid.uuid4())
    
    async def create_job(self, total_files: int) -> JobRecord:
        """새 작업 생성"""
        job_id = self.generate_job_id()
        return await self.storage.create_job(job_id, total_files)
    
    async def get_job(self, job_id: str) -> Optional[JobRecord]:
        """작업 조회"""
        return await self.storage.get_job(job_id)
    
    async def complete_job(self, job_id: str, results: List[Dict[str, Any]]) -> bool:
        """작업 완료 처리"""
        completed_count = sum(1 for r in results if r["success"])
        failed_count = sum(1 for r in results if not r["success"])
        
        return await self.storage.update_job(
            job_id,
            status="completed",
            progress=100,
            completed=completed_count,
            failed=failed_count,
            results=results,
            end_time=datetime.now().isoformat()
        )
    
    async def fail_job(self, job_id: str, error: str) -> bool:
        """작업 실패 처리"""
        return await self.storage.update_job(
            job_id,
            status="failed",
            error=error,
            end_time=datetime.now().isoformat()
        )
    
    async def delete_job(self, job_id: str) -> bool:
        """작업 삭제"""
        return await self.storage.delete_job(job_id)
    
    async def list_jobs(self) -> List[JobRecord]:
        """모든 작업 목록"""
        return await self.storage.list_jobs()
    
    async def job_exists(self, job_id: str) -> bool:
        """작업 존재 여부 확인"""
        job = await self.get_job(job_id)
        return job is not None


def create_job_service(storage_type: str = "memory") -> JobService:
    """JobService 팩토리 함수"""
    if storage_type == "memory":
        return JobService(InMemoryJobStorage())
    elif storage_type == "redis":
        # 추후 구현시 사용
        # Redis 클라이언트 초기화가 필요
        # redis_client = aioredis.from_url("redis://localhost")
        # return JobService(RedisJobStorage(redis_client))
        raise NotImplementedError("Redis 클라이언트 설정이 필요합니다")
    else:
        raise ValueError(f"지원하지 않는 저장소 타입: {storage_type}") 