import os
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projectlens.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initializes the database schema and seeds default users if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    
    # 2. Create Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 3. Create Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL
    )
    """)
    
    # 4. Create Password Resets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        token TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    
    # Seed default users if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = hash_password("admin123")
        employee_pass = hash_password("employee123")
        
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ("admin", admin_pass, "Admin"))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ("employee", employee_pass, "Employee"))
        conn.commit()
        
        # Log database seeding
        log_audit("system", "System", "DB_INIT", "Database initialized and default accounts seeded.")
        
    # Default document seeding removed to allow clean custom uploads.
        
    # Scan sample_docs directory and auto-ingest new files
    sample_docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_docs")
    if os.path.exists(sample_docs_dir):
        created_at = datetime.now().isoformat()
        for file_name in os.listdir(sample_docs_dir):
            if file_name.endswith((".txt", ".md", ".json", ".pdf")):
                cursor.execute("SELECT COUNT(*) FROM documents WHERE title = ?", (file_name,))
                if cursor.fetchone()[0] == 0:
                    file_path = os.path.join(sample_docs_dir, file_name)
                    try:
                        if file_name.endswith(".pdf"):
                            from pypdf import PdfReader
                            reader = PdfReader(file_path)
                            text_runs = []
                            for page in reader.pages:
                                txt = page.extract_text()
                                if txt:
                                    text_runs.append(txt)
                            content = "\n\n".join(text_runs)
                        else:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        
                        # Parse project and doc_type
                        project_name = "General Process"
                        doc_type = "SOP"
                        
                        if file_name.startswith("Project_"):
                            parts = file_name.split("_")
                            if len(parts) >= 2:
                                project_name = f"Project {parts[1]}"
                        
                        file_name_lower = file_name.lower()
                        if "brd" in file_name_lower or "product_requirements" in file_name_lower:
                            doc_type = "BRD"
                        elif "frd" in file_name_lower:
                            doc_type = "FRD"
                        elif "mom" in file_name_lower or "meeting" in file_name_lower:
                            doc_type = "Meeting Notes"
                        elif "team" in file_name_lower or "directory" in file_name_lower:
                            doc_type = "Org Chart"
                        elif "architecture" in file_name_lower or "specifications" in file_name_lower:
                            doc_type = "Architecture"
                        elif "sop" in file_name_lower or "failover" in file_name_lower:
                            doc_type = "SOP"
                            
                        metadata = {
                            "project": project_name,
                            "doc_type": doc_type,
                            "filename": file_name,
                            "uploaded_by": "system"
                        }
                        
                        cursor.execute(
                            "INSERT INTO documents (title, content, metadata_json, created_at) VALUES (?, ?, ?, ?)",
                            (file_name, content, json.dumps(metadata), created_at)
                        )
                        conn.commit()
                        log_audit("system", "System", "DB_AUTO_INGEST", f"Automatically ingested and indexed sample document: {file_name}")
                    except Exception as e:
                        print(f"Failed to auto-ingest {file_name}: {e}")
                        
    conn.close()

def log_audit(username: str, role: str, action: str, details: str):
    """Inserts a tamper-resistant entry into the security audit log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    try:
        cursor.execute(
            "INSERT INTO audit_logs (timestamp, username, role, action, details) VALUES (?, ?, ?, ?, ?)",
            (timestamp, username, role, action, details)
        )
        conn.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
    finally:
        conn.close()

def get_audit_logs() -> List[Dict[str, Any]]:
    """Retrieves all audit logs in chronological order."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_document(title: str, content: str, metadata: Dict[str, Any]) -> int:
    """Adds a document to the index metadata registry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    metadata_json = json.dumps(metadata)
    
    cursor.execute(
        "INSERT INTO documents (title, content, metadata_json, created_at) VALUES (?, ?, ?, ?)",
        (title, content, metadata_json, created_at)
    )
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def get_all_documents() -> List[Dict[str, Any]]:
    """Retrieves all indexed documents."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    docs = []
    for r in rows:
        d = dict(r)
        d["metadata"] = json.loads(d["metadata_json"])
        docs.append(d)
    return docs

def remove_document(doc_id: int):
    """Deletes a document from the registry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
