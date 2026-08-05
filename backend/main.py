import os
import shutil
from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, Security, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.database import (
    init_db, log_audit, get_audit_logs, add_document, 
    get_all_documents, remove_document
)
from backend.auth import (
    authenticate_user, create_access_token, get_current_user, require_admin,
    create_password_reset_token, verify_and_use_reset_token
)
from backend.agent import run_agent_pipeline, build_agent_index
from backend.audit import log_security_event

# Initialize FastAPI app
app = FastAPI(title="ProjectLens AI API", version="1.0.0")

# Enable CORS for local cross-origin connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema on startup
@app.on_event("startup")
def startup_event():
    init_db()
    try:
        build_agent_index()
    except Exception as e:
        print(f"Error rebuilding vector space index: {e}")

# Base models for requests
class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    username: str
    token: str
    new_password: str

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

# --- Authentication Endpoint ---
@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    user = authenticate_user(req.username, req.password)
    if not user:
        # Failed login audits are critical for security compliance
        log_security_event(req.username, "Unknown", "LOGIN_FAILED", "Failed authentication attempt.", request)
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    token = create_access_token({"username": user["username"], "role": user["role"]})
    log_security_event(user["username"], user["role"], "LOGIN_SUCCESS", "Successfully logged into system.", request)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }

# --- Password Resets (Forgot / Reset Password) ---
@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, request: Request):
    token = create_password_reset_token(req.username)
    if not token:
        log_security_event(req.username, "Unknown", "PASSWORD_RESET_REQUEST_FAILED", "Failed reset attempt - user not found.", request)
        raise HTTPException(status_code=404, detail="Username not found.")
        
    log_security_event(req.username, "Unknown", "PASSWORD_RESET_REQUESTED", f"Successfully generated reset token.", request)
    return {
        "message": "Password reset token generated successfully.",
        "token": token
    }

@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordRequest, request: Request):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
        
    try:
        verify_and_use_reset_token(req.username, req.token, req.new_password)
        log_security_event(req.username, "Unknown", "PASSWORD_RESET_SUCCESS", "Successfully reset password.", request)
        return {"message": "Password has been reset successfully."}
    except HTTPException as e:
        log_security_event(req.username, "Unknown", "PASSWORD_RESET_FAILED", f"Reset failed: {e.detail}", request)
        raise e
    except Exception as e:
        log_security_event(req.username, "Unknown", "PASSWORD_RESET_ERROR", f"Reset error: {str(e)}", request)
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")

# --- Conversational Agent API ---
@app.post("/api/chat")
def chat(req: ChatRequest, request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    username = current_user["username"]
    role = current_user["role"]
    
    if not req.query.strip():
         raise HTTPException(status_code=400, detail="Query text cannot be blank.")
         
    try:
        response = run_agent_pipeline(req.query, req.history, username, role, request)
        return response
    except Exception as e:
        log_security_event(username, role, "CHAT_ERROR", f"Exception raised: {e}", request)
        raise HTTPException(status_code=500, detail=f"Inference pipeline execution error: {str(e)}")

# --- Document Management (Admin Only) ---
@app.get("/api/admin/documents")
def get_documents(current_user: Dict[str, Any] = Depends(require_admin)):
    return get_all_documents()

@app.post("/api/admin/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    project_name: str = Form(...),
    doc_type: str = Form(...),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    # Restrict extensions to txt, md, json, pdf
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".txt", ".md", ".json", ".pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .txt, .md, .json, and .pdf are supported.")
        
    try:
        content_bytes = await file.read()
        if ext == ".pdf":
            import io
            from pypdf import PdfReader
            pdf_file = io.BytesIO(content_bytes)
            reader = PdfReader(pdf_file)
            text_runs = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_runs.append(text)
            content = "\n".join(text_runs)
            if not content.strip():
                raise ValueError("PDF file is empty or contains no extractable text.")
        else:
            content = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
    metadata = {
        "project": project_name,
        "doc_type": doc_type,
        "filename": filename,
        "uploaded_by": current_user["username"]
    }
    
    doc_id = add_document(filename, content, metadata)
    log_security_event(current_user["username"], current_user["role"], "DOC_UPLOAD", f"Uploaded document: {filename} for Project: {project_name}", request)
    
    try:
        build_agent_index()
    except Exception as e:
        print(f"[Warning] Failed to automatically rebuild index on upload: {e}")
        
    return {"message": "Document registered successfully.", "doc_id": doc_id}

@app.delete("/api/admin/documents/{doc_id}")
def delete_document(doc_id: int, request: Request, current_user: Dict[str, Any] = Depends(require_admin)):
    remove_document(doc_id)
    log_security_event(current_user["username"], current_user["role"], "DOC_DELETE", f"Removed document ID: {doc_id}", request)
    
    try:
        build_agent_index()
    except Exception as e:
        print(f"[Warning] Failed to automatically rebuild index on delete: {e}")
        
    return {"message": "Document removed from database repository."}

@app.post("/api/admin/reindex")
def reindex_kb(request: Request, current_user: Dict[str, Any] = Depends(require_admin)):
    try:
        build_agent_index()
        log_security_event(current_user["username"], current_user["role"], "REINDEX_KB", "Rebuilt vector search spaces indexes.", request)
        return {"message": "Knowledge base vector index rebuilt successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile vectors: {e}")

# --- Security Audits View (Admin Only) ---
@app.get("/api/admin/audits")
def get_audits(current_user: Dict[str, Any] = Depends(require_admin)):
    return get_audit_logs()

# --- Serve Static Frontend Files ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"message": "Frontend static templates not found."})

# Mount the remaining assets (style.css, app.js, images etc.)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
