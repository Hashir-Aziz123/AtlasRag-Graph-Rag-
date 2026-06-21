import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from celery.result import AsyncResult

from config.settings import settings
from src.workers.workers import celery_app
from src.workers.tasks import process_pdf_task
from src.models.api_schemas import TaskStatusResponse

router = APIRouter()

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF document and dispatches it to the asynchronous parsing queue.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(settings.RAW_DATA_DIR, exist_ok=True)
    file_path = settings.RAW_DATA_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()
        
    task = process_pdf_task.delay(str(file_path))

    return {"message": "Document accepted for processing", "task_id": task.id}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Polls the Celery backend for the current status of an ingestion job.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
    }
    
    if task_result.ready():
        if task_result.successful():
            response["result"] = task_result.result.get("message")
        else:
            response["result"] = str(task_result.info)
            
    return response