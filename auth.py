from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
import firebase_admin

security = HTTPBearer()

# def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     try:
#         token = credentials.credentials
#         decoded_token = auth.verify_id_token(token)
#         print("🔥 Decoded token:", decoded_token) 
#         return decoded_token
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")
def verify_token(authorization: str = Header(None)):
    print("HEADER RECEIVED:", authorization)

    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        # print("TOKEN:", token)

        decoded = auth.verify_id_token(token)
        # print("DECODED:", decoded)

        return decoded
    except Exception as e:
        print("VERIFY ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    def role_checker(user=Depends(verify_token)):
        user_role = user.get("role")

        # 🔥 If checking for employee → allow any authenticated user
        if required_role == "employee":
            return user

        # 🔥 Only enforce role for manager
        if user_role != required_role:
            raise HTTPException(status_code=403, detail="Access denied")

        return user

    return role_checker
