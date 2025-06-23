"""
PDF API
"""

from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pdf_service import PDFService
from app.services.job_service import create_job_service
from app.schemas.pdf import (
    MultipleUploadResponse,
    ProcessingStatusResponse
)
from app.models.base import get_async_db

router = APIRouter(
    prefix="/pdf",
    tags=["pdf"],
    responses={404: {"description": "요청한 리소스를 찾을 수 없습니다"}}
)

# 작업 서비스 생성 (현재는 메모리기반이나 추후 필요시 redis 사용 가능)
job_service = create_job_service("memory")





@router.post("/upload-multiple", response_model=MultipleUploadResponse)
async def upload_multiple_pdfs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="여러 PDF 파일들"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    여러 PDF 파일 업로드 및 백그라운드 처리
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업로드할 파일이 없습니다."
        )
    
    pdf_service = PDFService(db)
    file_data_list = await pdf_service.validate_and_read_files(files)
    
    if not file_data_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="처리 가능한 PDF 파일이 없습니다."
        )
    
    job_record = await job_service.create_job(len(file_data_list))
    
    background_tasks.add_task(
        pdf_service.process_files_in_background, 
        file_data_list, 
        job_service, 
        job_record.job_id
    )
    
    return MultipleUploadResponse(
        success=True,
        message=f"{len(file_data_list)}개의 PDF 파일 처리를 시작했습니다.",
        job_id=job_record.job_id,
        total_files=len(file_data_list),
        status_url=f"/pdf/status/{job_record.job_id}"
    )


@router.get("/status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(job_id: str, db: AsyncSession = Depends(get_async_db)):
    """
    처리 상태 조회
    """
    job = await job_service.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 작업을 찾을 수 없습니다."
        )
    
    pdf_service = PDFService(db)
    results = pdf_service.build_processing_results(job.results) if job.results else []
    
    return ProcessingStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        total=job.total,
        completed=job.completed,
        failed=job.failed,
        results=results,
        start_time=job.start_time,
        end_time=job.end_time,
        error=job.error
    )


@router.delete("/status/{job_id}")
async def delete_job_status(job_id: str):
    """
    작업 상태 정보 삭제
    """
    if not await job_service.job_exists(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 작업을 찾을 수 없습니다."
        )
    
    await job_service.delete_job(job_id)
    
    return {"message": "작업 상태가 삭제되었습니다."}


@router.get("/jobs")
async def list_all_jobs():
    """
    모든 작업 목록 조회
    """
    jobs = await job_service.list_jobs()
    
    return {
        "total_jobs": len(jobs),
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status,
                "total": job.total,
                "completed": job.completed,
                "failed": job.failed,
                "start_time": job.start_time
            }
            for job in jobs
        ]
    }


 