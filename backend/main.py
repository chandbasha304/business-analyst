import os
import shutil
from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException, Security
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.database import (
    init_db, log_audit, get_audit_logs, add_document, 
    get_all_documents, remove_document
)
from backend.auth import authenticate_user, create_access_token, get_current_user, require_admin
from backend.agent import run_agent_pipeline, build_agent_index

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

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

# --- Authentication Endpoint ---
@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        # Failed login audits are critical for security compliance
        log_audit(req.username, "Unknown", "LOGIN_FAILED", "Failed authentication attempt.")
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    token = create_access_token({"username": user["username"], "role": user["role"]})
    log_audit(user["username"], user["role"], "LOGIN_SUCCESS", "Successfully logged into system.")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }

# --- Conversational Agent API ---
@app.post("/api/chat")
def chat(req: ChatRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    username = current_user["username"]
    role = current_user["role"]
    
    if not req.query.strip():
         raise HTTPException(status_code=400, detail="Query text cannot be blank.")
         
    try:
        response = run_agent_pipeline(req.query, req.history, username, role)
        return response
    except Exception as e:
        log_audit(username, role, "CHAT_ERROR", f"Exception raised: {e}")
        raise HTTPException(status_code=500, detail=f"Inference pipeline execution error: {str(e)}")

# --- Document Management (Admin Only) ---
@app.get("/api/admin/documents")
def get_documents(current_user: Dict[str, Any] = Depends(require_admin)):
    return get_all_documents()

@app.post("/api/admin/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    doc_type: str = Form(...),
    current_user: Dict[str, Any] = Depends(require_admin)
):
    # Restrict extensions to txt, md, json
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".txt", ".md", ".json"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .txt, .md, and .json are supported.")
        
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file text: {e}")
        
    metadata = {
        "project": project_name,
        "doc_type": doc_type,
        "filename": filename,
        "uploaded_by": current_user["username"]
    }
    
    doc_id = add_document(filename, content, metadata)
    log_audit(current_user["username"], current_user["role"], "DOC_UPLOAD", f"Uploaded document: {filename} for Project: {project_name}")
    
    return {"message": "Document registered successfully.", "doc_id": doc_id}

@app.delete("/api/admin/documents/{doc_id}")
def delete_document(doc_id: int, current_user: Dict[str, Any] = Depends(require_admin)):
    remove_document(doc_id)
    log_audit(current_user["username"], current_user["role"], "DOC_DELETE", f"Removed document ID: {doc_id}")
    return {"message": "Document removed from database repository."}

@app.post("/api/admin/reindex")
def reindex_kb(current_user: Dict[str, Any] = Depends(require_admin)):
    try:
        build_agent_index()
        log_audit(current_user["username"], current_user["role"], "REINDEX_KB", "Rebuilt vector search spaces indexes.")
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
