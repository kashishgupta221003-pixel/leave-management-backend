# Backend Setup Guide

## FastAPI Backend Configuration

This backend handles authentication, leave requests, and BigQuery integration.

## Files in Backend

```
leave-management-backend/
├── main.py                 # FastAPI application with all endpoints
├── auth.py                # Firebase authentication logic
├── models.py              # Pydantic models for request/response validation
├── bigquery_client.py     # BigQuery operations
├── firebase_config.py     # Firebase initialization
├── firebase_key.json      # Firebase service account credentials
└── requirements.txt       # Python dependencies
```

## Installation

### 1. Create Virtual Environment

```bash
cd C:\Users\Kashish_G\Desktop\leave-management-backend
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install fastapi uvicorn firebase-admin google-cloud-bigquery python-dotenv
```

### 3. Setup Firebase Service Account

1. Go to Firebase Console → Project Settings → Service Accounts
2. Download the JSON key file
3. Save as `firebase_key.json` in backend directory

### 4. Setup BigQuery

Create the dataset and table in BigQuery:

```sql
-- Run in BigQuery Console

-- Create dataset
CREATE SCHEMA leave_management;

-- Create leave_requests table
CREATE TABLE leave_management.leave_requests (
  leave_id STRING NOT NULL,
  employee_id STRING NOT NULL,
  start_date STRING NOT NULL,
  end_date STRING NOT NULL,
  reason STRING,
  leave_type STRING,
  status STRING DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP,
  deleted_at TIMESTAMP,
  is_deleted BOOL DEFAULT FALSE
);
```

### 5. Configure BigQuery Client

In `bigquery_client.py`, ensure your Google Cloud project ID is set:

```python
client = bigquery.Client(project='your-gcp-project-id')
```

## API Endpoints

### Public Endpoints

- `GET /` - Health check
- Returns: `{"message": "Leave Management Backend Running"}`

### Protected Endpoints (Require Firebase Token)

#### Employee Endpoints

1. **Get Employee Dashboard**
   ```
   GET /employee-dashboard
   Headers: Authorization: Bearer {token}
   Returns: {"message": "Welcome Employee", "email": "user@example.com"}
   ```

2. **Submit Leave Request**
   ```
   POST /leaves/submit
   Headers: Authorization: Bearer {token}
   Body: {
     "leave_type": "Sick",
     "start_date": "2026-03-01",
     "end_date": "2026-03-05",
     "reason": "Personal reasons for leave request"
   }
   Returns: {"leave_id": "uuid", "status": "Pending"}
   ```

3. **Get My Leaves**
   ```
   GET /leaves/my-leaves
   Headers: Authorization: Bearer {token}
   Returns: {"leaves": [...]}
   ```

4. **Delete Leave**
   ```
   DELETE /leaves/{leave_id}
   Headers: Authorization: Bearer {token}
   Returns: {"message": "Leave deleted"}
   Note: Performs soft delete (sets is_deleted flag to True)
   ```

#### Manager Endpoints

1. **Get Manager Dashboard**
   ```
   GET /manager-dashboard
   Headers: Authorization: Bearer {token}
   Returns: {"message": "Welcome Manager", "email": "manager@example.com"}
   ```

2. **Get All Leaves**
   ```
   GET /leaves/all-leaves
   Headers: Authorization: Bearer {token}
   Returns: {"leaves": [...]}
   ```

3. **Update Leave Status**
   ```
   PUT /leaves/{leave_id}/status?status=Approved
   Headers: Authorization: Bearer {token}
   Query Params: status=Approved|Rejected|Pending
   Returns: {"message": "Status updated"}
   ```

4. **Get Pending Leaves**
   ```
   GET /leaves/pending
   Headers: Authorization: Bearer {token}
   Returns: {"leaves": [...]}
   Note: Used for Cloud Scheduler notifications
   ```

## Authentication Flow

1. Frontend sends email/password to Firebase
2. Firebase returns ID token
3. Frontend sends ID token in Authorization header: `Bearer {token}`
4. Backend verifies token using Firebase Admin SDK
5. Backend extracts user role from token claims
6. Role-based access control applied to endpoints

## User Creation

Create users in Firebase using:

```bash
firebase auth:import users.json --hash-algo=bcrypt
```

Or manually in Firebase Console:

1. Go to Firebase Console → Authentication → Users
2. Click "Add User"
3. Enter email and password
4. After creation, set custom claims for role:

```python
# Use admin SDK to set role claim
from firebase_admin import auth

def set_user_role(uid, role):
    auth.set_custom_user_claims(uid, {'role': role})
```

## Testing the APIs

### Using curl

```bash
# Get token from Frontend first, then:

# Get employee leaves
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/leaves/my-leaves

# Submit leave
curl -X POST http://localhost:8000/leaves/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type": "Sick",
    "start_date": "2026-03-01",
    "end_date": "2026-03-05",
    "reason": "Medical appointment required"
  }'
```

### Using Postman

1. Import the backend URL: `http://localhost:8000`
2. Get token from frontend login
3. Add Authorization header: `Bearer {token}`
4. Test endpoints

## Run Backend

```bash
# Development mode
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --port 8000
```

Backend will run at `http://localhost:8000`

## CORS Configuration

Backend already has CORS enabled for all origins. If you need to restrict:

Update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://your-frontend-url.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Database Notes

### Leave Request Fields

- `leave_id`: Auto-generated UUID
- `employee_id`: User's Firebase UID
- `start_date`: YYYY-MM-DD format
- `end_date`: YYYY-MM-DD format
- `reason`: Text reason for leave
- `leave_type`: Parental, Sick, Paid, Casual, Earned
- `status`: Pending, Approved, Rejected
- `is_deleted`: Soft delete flag (True = not shown)

### Query Examples

```sql
-- Get all pending leaves
SELECT * FROM `project.leave_management.leave_requests`
WHERE status = 'Pending' AND is_deleted = False;

-- Get employee's leaves
SELECT * FROM `project.leave_management.leave_requests`
WHERE employee_id = 'xxx' AND is_deleted = False;

-- Get approval statistics
SELECT status, COUNT(*) as count
FROM `project.leave_management.leave_requests`
WHERE is_deleted = False
GROUP BY status;
```

## Deployment

### Docker Setup

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deploy to Cloud Run

```bash
# Build and push
docker build -t gcr.io/your-project/leave-backend .
docker push gcr.io/your-project/leave-backend

# Deploy
gcloud run deploy leave-backend \
  --image gcr.io/your-project/leave-backend \
  --platform managed \
  --memory 512Mi \
  --timeout 3600
```

## Environment Variables (if needed)

Create `.env` file:

```
GCP_PROJECT_ID=your-project-id
BIGQUERY_DATASET=leave_management
FIREBASE_PROJECT_ID=your-firebase-project
```

Load in Python if needed:

```python
from dotenv import load_dotenv
import os

load_dotenv()
project_id = os.getenv('GCP_PROJECT_ID')
```

---

## Troubleshooting

### Firebase Authentication Errors
- Verify `firebase_key.json` is in correct directory
- Check Firebase project ID in key file
- Ensure user has `email` and `password` verification

### BigQuery Connection Errors
- Check service account permissions
- Verify table name and dataset name
- Ensure Google Cloud project ID is correct
- Check network connectivity

### CORS Errors
- Backend should automatically accept requests
- Verify frontend URL in request headers
- Check browser console for detailed error

### Port Already in Use
```bash
# Find process using port 8000
netstat -a -n -o | find ":8000"

# Kill the process (Windows)
taskkill /PID {process_id} /F
```
