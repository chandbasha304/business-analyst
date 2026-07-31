import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional

from backend.config import JWT_SECRET, JWT_ALGORITHM
from backend.database import get_db_connection, hash_password

security_bearer = HTTPBearer()

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Validates user credentials against SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
        
    hashed_input = hash_password(password)
    if hashed_input == user["password_hash"]:
        return {
            "username": user["username"],
            "role": user["role"]
        }
    return None

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = timedelta(hours=2)) -> str:
    """Generates a secure JWT token containing the username and user role."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> Dict[str, Any]:
    """Dependency to extract user info from JWT header and authorize API access."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("username")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token payload parameters.")
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid credentials session signature.")

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Dependency to restrict route execution exclusively to Administrators."""
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Access Denied: Administrative privileges required.")
    return current_user
