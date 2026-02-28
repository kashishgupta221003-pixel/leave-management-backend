from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
import uuid
import os

# Load credentials from firebase_key.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(BASE_DIR, "firebase_key.json")

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    print("✅ BigQuery credentials loaded successfully")
except Exception as e:
    print(f"❌ Error loading BigQuery credentials: {e}")
    raise

# Initialize BigQuery client
try:
    client = bigquery.Client(project='kasishgupta-project', credentials=credentials)
    print("✅ BigQuery client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing BigQuery client: {e}")
    raise
# Dataset and table configuration
DATASET_ID = "leave_management"
TABLE_ID = "leave_requests"
TABLE_REF = f"{client.project}.{DATASET_ID}.{TABLE_ID}"

def create_leave_request(employee_id: str, start_date: str, end_date: str, reason: str, leave_type: str):
    """Submit a new leave request to BigQuery"""
    leave_id = str(uuid.uuid4())
    
    # Handle date format - accept both YYYY-MM-DD and DD-MM-YYYY
    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or DD-MM-YYYY")
    
    try:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    except ValueError as e:
        print(f"❌ Date parsing error: {e}")
        raise
    print("Received leave_type:", leave_type)
    query = f"""
            INSERT INTO `{TABLE_REF}`
            (leave_id, employee_id, start_date, end_date, reason, leave_type, status, created_at, is_deleted)
            VALUES
            (@leave_id, @employee_id, @start_date, @end_date, @reason, @leave_type, 'Pending', CURRENT_TIMESTAMP(), FALSE)
            """

    job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("leave_id", "STRING", leave_id),
                    bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                    bigquery.ScalarQueryParameter("reason", "STRING", reason),
                    bigquery.ScalarQueryParameter("leave_type", "STRING", leave_type),
                ]
            )

    try:
        client.query(query, job_config=job_config).result()
    except Exception as e:
        print("🔥 INSERT ERROR:", e)
        raise Exception(str(e))

    return {"leave_id": leave_id, "status": "Pending"}
    # rows_to_insert = [
    #     {
    #         "leave_id": leave_id,
    #         "employee_id": employee_id,
    #         "start_date": start_date,
    #         "end_date": end_date,
    #         "reason": reason,
    #         "leave_type": leave_type,
    #         "status": "Pending",
    #         "created_at": datetime.utcnow().isoformat(),
    #         "is_deleted": False,
    #     }
    # ]
    
    # errors = client.insert_rows_json(TABLE_REF, rows_to_insert)
    # if errors:
    #     print("🔥 INSERT ERRORS:", errors)
    #     raise Exception(f"Error inserting rows: {errors}")
    
    # return {"leave_id": leave_id, "status": "Pending"}

# def get_employee_leaves(employee_id: str):
#     """Get all leaves for a specific employee"""
#     query = f"""
#     SELECT * FROM `{TABLE_REF}`
#     WHERE employee_id = @employee_id AND is_deleted = False
#     ORDER BY created_at DESC
#     """
    
#     job_config = bigquery.QueryJobConfig(
#         query_parameters=[
#             bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
#         ]
#     )
    
#     results = client.query(query, job_config=job_config).result()
#     return [dict(row) for row in results]
def get_employee_leaves(employee_id: str):
    """Get all leaves for a specific employee"""
    query = f"""
    SELECT * FROM `{TABLE_REF}`
    WHERE employee_id = @employee_id AND is_deleted = False
    ORDER BY created_at DESC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
        ]
    )

    results = client.query(query, job_config=job_config).result()
    return [dict(row) for row in results]

def get_all_leaves():
    """Get all leaves (for managers)"""
    query = f"""
    SELECT * FROM `{TABLE_REF}`
    WHERE is_deleted = False
    ORDER BY created_at DESC
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]

def update_leave_status(leave_id: str, status: str):
    """Update leave request status"""
    query = f"""
    UPDATE `{TABLE_REF}`
    SET status = @status
    WHERE leave_id = @leave_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("leave_id", "STRING", leave_id),
            bigquery.ScalarQueryParameter("status", "STRING", status),
        ]
    )
    client.query(query, job_config=job_config).result()
    # The result() method waits for the job to complete.
    return {"status": "updated"}

# def soft_delete_leave(leave_id: str):
#     """Soft delete a leave request"""
#     query = f"""
#     UPDATE `{TABLE_REF}`
#     SET is_deleted = True, deleted_at = CURRENT_TIMESTAMP()
#     WHERE leave_id = @leave_id
#     """
    
#     job_config = bigquery.QueryJobConfig(
#         query_parameters=[
#             bigquery.ScalarQueryParameter("leave_id", "STRING", leave_id),
#         ]
#     )
    
#     client.query(query, job_config=job_config).result()
#     return {"status": "deleted"}
def update_leave_request(leave_id: str, employee_id: str, start_date: str, end_date: str, reason: str, leave_type: str):
    """Edit an existing leave request (only if Pending and not deleted)"""

    # Handle date format (same logic as create)
    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_str}")

    try:
        start_date = parse_date(start_date)
        end_date = parse_date(end_date)
    except ValueError as e:
        print(f"❌ Date parsing error: {e}")
        raise

    query = f"""
    UPDATE `{TABLE_REF}`
    SET start_date = @start_date,
        end_date = @end_date,
        reason = @reason,
        leave_type = @leave_type
    WHERE leave_id = @leave_id
    AND employee_id = @employee_id
    AND status = 'Pending'
    AND is_deleted = False
    """


    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("leave_id", "STRING", leave_id),
            bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("reason", "STRING", reason),
            bigquery.ScalarQueryParameter("leave_type", "STRING", leave_type),
        ]
    )

    try:
        client.query(query, job_config=job_config).result()
    except Exception as e:
        print(f"🔥 Error updating leave: {e}")
        raise Exception("Error updating leave request")

    return {"status": "updated"}

def soft_delete_leave(leave_id: str, employee_id: str):
    query = f"""
    UPDATE `{TABLE_REF}`
    SET is_deleted = True,
        status = 'Withdrawn',
        deleted_at = CURRENT_TIMESTAMP()
    WHERE leave_id = @leave_id
    AND employee_id = @employee_id
    AND status = 'Pending'
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("leave_id", "STRING", leave_id),
            bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
        ]
    )
    try:
        client.query(query, job_config=job_config).result()
    except Exception as e:
        print(f"🔥 Error withdrawing leave: {e}")
        raise Exception("Error withdrawing leave request")
    return {"status": "withdrawn"}

def get_pending_leaves():
    """Get all pending leaves for notifications"""
    query = f"""
    SELECT * FROM `{TABLE_REF}`
    WHERE status = 'Pending' AND is_deleted = False
    """
    
    results = client.query(query).result()
    return [dict(row) for row in results]
