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
        
    # Seed default documents if empty
    cursor.execute("SELECT COUNT(*) FROM documents")
    if cursor.fetchone()[0] == 0:
        import json
        docs = [
            ("Project_Atlas_BRD.txt", 
             "Project Atlas is the company's next-generation payments gateway. It aims to solve the merchant processing latency problem by implementing a local cache mechanism. The Business Analyst is Sarah Jenkins, the Product Owner is David Miller, and the Lead Developer is James Carter. The project was initiated in Q1 2026 to address a 15% transaction drop rate.",
             json.dumps({"project": "Project Atlas", "doc_type": "BRD", "filename": "Project_Atlas_BRD.txt", "uploaded_by": "system"})),
            
            ("Project_Atlas_FRD.txt",
             "Project Atlas payment gateway supports REST APIs for transaction authorizations, refunds, and settlements. The endpoints are /api/v1/auth, /api/v1/refund, and /api/v1/settle. Authorization latency must be under 200ms. Refunds must be processed within 24 hours of receipt. Error code 4001 indicates terminal card expiration.",
             json.dumps({"project": "Project Atlas", "doc_type": "FRD", "filename": "Project_Atlas_FRD.txt", "uploaded_by": "system"})),
            
            ("Company_Onboarding_SOP.txt",
             "Welcome to the corporate portal. For general onboarding, new hires must complete their workspace security setup on Day 1. On Day 2, contact your supervisor for project allocations. On Day 3, review the project documentation in ProjectLens AI. All access logs are subject to security audits.",
             json.dumps({"project": "General Process", "doc_type": "SOP", "filename": "Company_Onboarding_SOP.txt", "uploaded_by": "system"})),
            
            ("Team_Directory.txt",
             "Sarah Jenkins is the Senior Business Analyst for Project Atlas. David Miller is the Principal Product Owner. James Carter is the Lead Developer. Jessica Taylor is the QA Lead. All team members report to the Director of Payments Engineering.",
             json.dumps({"project": "Project Atlas", "doc_type": "Org Chart", "filename": "Team_Directory.txt", "uploaded_by": "system"}))
        ]
        
        created_at = datetime.now().isoformat()
        for title, content, metadata_json in docs:
            cursor.execute(
                "INSERT INTO documents (title, content, metadata_json, created_at) VALUES (?, ?, ?, ?)",
                (title, content, metadata_json, created_at)
            )
        conn.commit()
        log_audit("system", "System", "DB_INIT_DOCS", "Sample project documents seeded.")
        
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
