import os
from fastapi import Request
from typing import Dict, Any, Optional

from backend.database import log_audit as db_log_audit

def log_security_event(username: str, role: str, action: str, details: str, request: Optional[Request] = None):
    """Wraps database audit calls, adding request metadata (IP, headers) if available."""
    ip_address = "unknown"
    user_agent = "unknown"
    
    if request:
        # Resolve forward headers if running behind reverse proxies
        ip_address = request.headers.get("x-forwarded-for") or request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
    full_details = f"{details} | Client IP: {ip_address} | Agent: {user_agent}"
    db_log_audit(username, role, action, full_details)
