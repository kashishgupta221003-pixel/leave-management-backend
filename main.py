from fastapi import FastAPI, Depends, HTTPException,Body
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_token, require_role
from pydantic import BaseModel
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from models import LeaveRequestCreate, LeaveResponse, LeaveListResponse
from bigquery_client import (
    create_leave_request,
    get_employee_leaves,
    get_all_leaves,  
    update_leave_status,
    soft_delete_leave,
    get_pending_leaves,
    update_leave_request,
)
import firebase_config
from firebase_admin import auth

app = FastAPI()
# 🔍 DEBUG: Check which credentials are used
# creds, project = default()
# print("Project:", project)
# print("Cred type:", type(creds))
# print("Service account:", getattr(creds, "service_account_email", "Not a service account"))

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Leave Management Backend Running"}

@app.get("/employee-dashboard")
def employee_dashboard(user=Depends(require_role("employee"))):
    return {"message": "Welcome Employee", "email": user.get("email")}

@app.get("/manager-dashboard")
def manager_dashboard(user=Depends(require_role("manager"))):
    return {"message": "Welcome Manager", "email": user.get("email")}

# ===== LEAVE MANAGEMENT ENDPOINTS =====
@app.post("/leaves/submit")
def submit_leave(
    leave_data: LeaveRequestCreate,
    user=Depends(require_role("employee"))
):
    """Submit a new leave request"""
    try:
        employee_id = user.get("uid")
        result = create_leave_request(
            employee_id=employee_id,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason,
            leave_type=leave_data.leave_type,
        )
        return result
    except Exception as e:
        print("🔥 ERROR INSIDE SUBMIT:", e)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/leaves/my-leaves", response_model=LeaveListResponse)
async def get_my_leaves(user=Depends(require_role("employee"))):
    """Get all leaves for the logged-in employee"""
    try:
        employee_id = user.get("uid")
        leaves = get_employee_leaves(employee_id)
        return {"leaves": jsonable_encoder(leaves)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaves/all-leaves")
async def get_all_leaves_manager(user=Depends(require_role("manager"))):
    """Get all leaves (manager only)"""
    try:
        leaves = get_all_leaves()
        return {"leaves": jsonable_encoder(leaves)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/leaves/{leave_id}/status")
def update_status(
    leave_id: str,
    status: str,
    user=Depends(require_role("manager"))
):
    """Update leave status (manager only)"""
    try:
        if status not in ["Pending", "Approved", "Rejected"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        result = update_leave_status(leave_id, status)
        return {"message": "Status updated", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/leaves/{leave_id}")
def delete_leave(
    leave_id: str,
    user=Depends(require_role("employee"))
):
    """Soft delete a leave request"""
    try:
        result = soft_delete_leave( leave_id=leave_id,
            employee_id=user["uid"])
        return {"message": "Leave withdrawn", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaves/pending")
def get_pending(user=Depends(require_role("manager"))):
    """Get all pending leaves for notifications"""
    try:
        leaves = get_pending_leaves()
        return {"leaves": jsonable_encoder(leaves)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/leaves/{leave_id}")
def update_leave(
    leave_id: str,
    leave: dict = Body(...),
    user=Depends(verify_token)
):
    try:
        return update_leave_request(
            leave_id=leave_id,
            employee_id=user["uid"],
            start_date=leave.get("start_date"),
            end_date=leave.get("end_date"),
            reason=leave.get("reason"),
            leave_type=leave.get("leave_type"),
        )
    except Exception as e:
        print("🔥 Update Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assign-role")
def assign_role(user=Depends(verify_token)):
    try:
        uid = user.get("uid")

        # 🔥 Assign default employee role
        auth.set_custom_user_claims(uid, {"role": "employee"})

        return {"message": "Employee role assigned successfully"}

    except Exception as e:
        print("🔥 Role assignment error:", e)
        raise HTTPException(status_code=500, detail=str(e))