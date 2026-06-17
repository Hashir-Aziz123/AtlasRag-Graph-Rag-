from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    routed_intent: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None