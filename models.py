from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LeaveRequestCreate(BaseModel):
    start_date: str
    end_date: str
    reason: str
    leave_type: str

class LeaveResponse(BaseModel):
    leave_id: str
    employee_id: str
    start_date: str
    end_date: str
    reason: str
    leave_type: str
    status: str
    created_at: Optional[str]
    is_deleted: bool = False

class LeaveListResponse(BaseModel):
    leaves: List[LeaveResponse]
