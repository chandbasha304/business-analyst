import jwt
import uuid
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

def create_password_reset_token(username: str) -> Optional[str]:
    """Generates a secure temporary reset token for the given user, saving it to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Verify user exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
        
    # 2. Generate token and expiration date (15 mins from now)
    token = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
    
    # 3. Save to database
    cursor.execute(
        "INSERT INTO password_resets (username, token, expires_at) VALUES (?, ?, ?)",
        (username, token, expires_at)
    )
    conn.commit()
    conn.close()
    return token

def verify_and_use_reset_token(username: str, token: str, new_password: str) -> None:
    """Verifies a reset token and updates the user's password. Prevents password reuse."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check if token exists, is not used, and matches username
    cursor.execute(
        "SELECT id, expires_at FROM password_resets WHERE username = ? AND token = ? AND used = 0",
        (username, token)
    )
    reset_entry = cursor.fetchone()
    if not reset_entry:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid, used, or unauthorized reset token.")
        
    # 2. Check expiration
    expires_at_dt = datetime.fromisoformat(reset_entry["expires_at"])
    if expires_at_dt < datetime.utcnow():
        conn.close()
        raise HTTPException(status_code=400, detail="Password reset token has expired.")
        
    # 3. Retrieve user's current password hash to check for reuse
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    user_entry = cursor.fetchone()
    if not user_entry:
        conn.close()
        raise HTTPException(status_code=404, detail="User account not found.")
        
    new_hash = hash_password(new_password)
    if new_hash == user_entry["password_hash"]:
        conn.close()
        raise HTTPException(status_code=400, detail="New password cannot be the same as your old password.")
        
    # 4. Perform the update and mark token as used
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
    cursor.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset_entry["id"],))
    conn.commit()
    conn.close()
