from google.cloud import bigquery
from datetime import datetime
import uuid

# Initialize BigQuery client using Cloud Run default service account
client = bigquery.Client(project="kasishgupta-project")

# Dataset and table configuration
DATASET_ID = "leave_management"
TABLE_ID = "leave_requests"
TABLE_REF = f"{client.project}.{DATASET_ID}.{TABLE_ID}"


def create_leave_request(employee_id: str, start_date: str, end_date: str, reason: str, leave_type: str):
    """Submit a new leave request to BigQuery"""

    leave_id = str(uuid.uuid4())

    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or DD-MM-YYYY")

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

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

    client.query(query, job_config=job_config).result()

    return {"leave_id": leave_id, "status": "Pending"}


def get_employee_leaves(employee_id: str):
    query = f"""
        SELECT *
        FROM `{TABLE_REF}`
        WHERE employee_id = @employee_id AND is_deleted = FALSE
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
    query = f"""
        SELECT *
        FROM `{TABLE_REF}`
        WHERE is_deleted = FALSE
        ORDER BY created_at DESC
    """

    results = client.query(query).result()
    return [dict(row) for row in results]


def update_leave_status(leave_id: str, status: str):
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
    return {"status": "updated"}


def update_leave_request(leave_id: str, employee_id: str, start_date: str, end_date: str, reason: str, leave_type: str):
    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_str}")

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    query = f"""
        UPDATE `{TABLE_REF}`
        SET start_date = @start_date,
            end_date = @end_date,
            reason = @reason,
            leave_type = @leave_type
        WHERE leave_id = @leave_id
        AND employee_id = @employee_id
        AND status = 'Pending'
        AND is_deleted = FALSE
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

    client.query(query, job_config=job_config).result()
    return {"status": "updated"}


def soft_delete_leave(leave_id: str, employee_id: str):
    query = f"""
        UPDATE `{TABLE_REF}`
        SET is_deleted = TRUE,
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

    client.query(query, job_config=job_config).result()
    return {"status": "withdrawn"}


def get_pending_leaves():
    query = f"""
        SELECT *
        FROM `{TABLE_REF}`
        WHERE status = 'Pending' AND is_deleted = FALSE
    """

    results = client.query(query).result()
    return [dict(row) for row in results]