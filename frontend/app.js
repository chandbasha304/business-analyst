// =====================================================================
// PROJECTLENS AI: FRONTEND CONTROLLER & RAG DATA CONNECTOR
// =====================================================================

const API_BASE = (window.location.origin.includes("3000") || window.location.protocol === "file:") ? "http://127.0.0.1:8085/api" : "/api";
let jwtToken = localStorage.getItem("projectlens_token") || "";
let userName = localStorage.getItem("projectlens_username") || "";
let userRole = localStorage.getItem("projectlens_role") || "";
let chatHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

// Initialize application state
function initApp() {
    if (jwtToken) {
        // User has a session cached
        showDashboard();
    } else {
        // Require authentication
        showLogin();
    }
}

// Show/Hide page layouts
function showLogin() {
    document.getElementById("login-container").classList.remove("hide");
    document.getElementById("app-container").classList.add("hide");
}

function showDashboard() {
    document.getElementById("login-container").classList.add("hide");
    document.getElementById("app-container").classList.remove("hide");
    
    // Update User Profile labels
    document.getElementById("user-display").innerText = userName;
    document.getElementById("role-display").innerText = userRole;
    document.getElementById("avatar-icon").innerText = userName.charAt(0).toUpperCase();

    // Toggle Role-based features visibility (RBAC)
    const adminElements = document.querySelectorAll(".admin-only");
    if (userRole === "Admin") {
        adminElements.forEach(el => el.classList.remove("hide"));
        // Pre-fetch admin data
        loadAdminDocuments();
        loadSecurityAudits();
    } else {
        adminElements.forEach(el => el.classList.add("hide"));
    }
    
    // Default Tab
    switchTab("chat-tab");
}

// Tab switcher logic
function switchTab(tabId) {
    // Nav links highlights
    document.querySelectorAll(".nav-item").forEach(btn => {
        if (btn.getAttribute("data-tab") === tabId) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Content container display
    document.querySelectorAll(".tab-content").forEach(section => {
        if (section.id === tabId) {
            section.classList.add("active");
        } else {
            section.classList.remove("active");
        }
    });

    // Refresh contents on entry
    if (tabId === "docs-tab" && userRole === "Admin") {
        loadAdminDocuments();
    } else if (tabId === "audits-tab" && userRole === "Admin") {
        loadSecurityAudits();
    }
}

// Event bindings
function setupEventListeners() {
    // 1. Authentication Form
    document.getElementById("login-form").addEventListener("submit", handleLogin);
    
    // 2. Terminate session logout button
    document.getElementById("logout-btn").addEventListener("click", handleLogout);
    
    // 3. Tab switching clicks
    document.querySelectorAll(".nav-item").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const tab = e.currentTarget.getAttribute("data-tab");
            switchTab(tab);
        });
    });
    
    // 4. Chat Submission
    document.getElementById("chat-form").addEventListener("submit", handleChatSubmit);
    
    // 5. Sample query clicks
    document.querySelectorAll(".sample-queries li").forEach(li => {
        li.addEventListener("click", (e) => {
            const text = e.target.innerText.replace(/"/g, "");
            document.getElementById("chat-input").value = text;
            document.getElementById("chat-form").dispatchEvent(new Event("submit"));
        });
    });

    // 6. Admin upload form
    document.getElementById("upload-form").addEventListener("submit", handleDocumentUpload);

    // 7. Refresh audits button
    document.getElementById("refresh-audits-btn").addEventListener("click", loadSecurityAudits);

    // 8. Re-index database button
    document.getElementById("reindex-btn").addEventListener("click", handleReindex);

    // 9. Forgot & Reset Password bindings
    document.getElementById("forgot-password-link").addEventListener("click", (e) => {
        e.preventDefault();
        showForgotForm();
    });
    document.getElementById("forgot-back-to-login").addEventListener("click", (e) => {
        e.preventDefault();
        showLoginForm();
    });
    document.getElementById("reset-back-to-login").addEventListener("click", (e) => {
        e.preventDefault();
        showLoginForm();
    });
    document.getElementById("forgot-form").addEventListener("submit", handleForgotSubmit);
    document.getElementById("reset-form").addEventListener("submit", handleResetSubmit);
}

// ==========================================
// AUTHENTICATION LOGIC
// ==========================================
async function handleLogin(e) {
    e.preventDefault();
    const errorEl = document.getElementById("login-error");
    errorEl.classList.add("hide");
    
    const usernameInput = document.getElementById("username").value;
    const passwordInput = document.getElementById("password").value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Authentication Failed.");
        }
        
        const data = await response.json();
        
        // Cache credentials session
        jwtToken = data.access_token;
        userName = data.username;
        userRole = data.role;
        
        localStorage.setItem("projectlens_token", jwtToken);
        localStorage.setItem("projectlens_username", userName);
        localStorage.setItem("projectlens_role", userRole);
        
        // Clear login fields
        document.getElementById("password").value = "";
        
        showDashboard();
        appendSystemMessage("🤖 Virtual connection established. Secure RAG indexing online.");
    } catch (err) {
        errorEl.innerText = err.message;
        errorEl.classList.remove("hide");
    }
}

function handleLogout() {
    jwtToken = "";
    userName = "";
    userRole = "";
    chatHistory = [];
    localStorage.clear();
    
    // Clear chat dialog
    document.getElementById("chat-messages").innerHTML = `
        <div class="message system-msg">
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
                <p>Welcome to <strong>ProjectLens AI</strong>. I can answer questions across your 15 indexed corporate project specifications, architecture files, and SOPs.</p>
                <p class="sample-title">Try asking these sample questions:</p>
                <ul class="sample-queries">
                    <li>"Who is the lead for Helios Solar Grid?"</li>
                    <li>"What are the RTO and RPO benchmarks for Sentinel Disaster Recovery?"</li>
                    <li>"What compliance frameworks does BioHealth Clinical Engine follow?"</li>
                </ul>
            </div>
        </div>
    `;
    document.getElementById("follow-up-container").classList.add("hide");
    
    // Clear telemetry
    document.getElementById("telemetry-logs").innerHTML = `
        <div class="empty-telemetry">
            <p>Submit a query to inspect the Agent's reasoning, vector score math, and dynamic source routing steps.</p>
        </div>
    `;
    
    showLogin();
}

// ==========================================
// CHAT & AGENT INFERENCE LAYER
// ==========================================
async function handleChatSubmit(e) {
    e.preventDefault();
    const inputEl = document.getElementById("chat-input");
    const queryText = inputEl.value.trim();
    if (!queryText) return;
    
    inputEl.value = "";
    appendUserMessage(queryText);
    
    // Insert loading/thinking block
    const thinkingId = appendThinkingIndicator();
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
                query: queryText,
                history: chatHistory
            })
        });
        
        removeThinkingIndicator(thinkingId);
        
        if (response.status === 401) {
            handleLogout();
            alert("Your session has expired. Please log in again.");
            return;
        }
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Agent failed to synthesize response.");
        }
        
        const data = await response.json();
        
        // Append dynamic answers
        appendAgentMessage(data.answer, data.sources);
        
        // Update Reasoning trace logs panel
        renderReasoningTrace(data.reasoning_trace);
        
        // Render follow-ups
        renderFollowUps(data.follow_ups);
        
        // Push turns to session memory array
        chatHistory.push({
            user: queryText,
            ai: data.answer
        });
        
    } catch (err) {
        removeThinkingIndicator(thinkingId);
        appendSystemMessage(`❌ Error: ${err.message}`);
    }
}

// Message Rendering Helpers
function appendUserMessage(text) {
    const stream = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message user-msg";
    msg.innerHTML = `
        <div class="msg-avatar">👤</div>
        <div class="msg-content">
            <p>${escapeHTML(text)}</p>
        </div>
    `;
    stream.appendChild(msg);
    scrollChat();
}

function appendAgentMessage(text, sources) {
    const stream = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message system-msg";
    
    let citationsHTML = "";
    if (sources && sources.length > 0) {
        citationsHTML = `<div class="msg-citations"><span>Sources Cited:</span>`;
        sources.forEach(src => {
            citationsHTML += `<span class="citation-badge">${escapeHTML(src)}</span>`;
        });
        citationsHTML += `</div>`;
    }
    
    msg.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
            <p>${formatMarkdownBold(escapeHTML(text))}</p>
            ${citationsHTML}
        </div>
    `;
    stream.appendChild(msg);
    scrollChat();
}

function appendSystemMessage(text) {
    const stream = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message system-msg";
    msg.style.background = "rgba(99, 102, 241, 0.05)";
    msg.innerHTML = `
        <div class="msg-avatar">⚙️</div>
        <div class="msg-content">
            <p><em>${escapeHTML(text)}</em></p>
        </div>
    `;
    stream.appendChild(msg);
    scrollChat();
}

function appendThinkingIndicator() {
    const stream = document.getElementById("chat-messages");
    const id = "think-" + Date.now();
    const msg = document.createElement("div");
    msg.id = id;
    msg.className = "message system-msg";
    msg.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
            <p><em>Agentic reasoning running, scanning sources...</em></p>
        </div>
    `;
    stream.appendChild(msg);
    scrollChat();
    return id;
}

function removeThinkingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollChat() {
    const stream = document.getElementById("chat-messages");
    stream.scrollTop = stream.scrollHeight;
}

// Telemetry visualizer rendering
function renderReasoningTrace(trace) {
    const container = document.getElementById("telemetry-logs");
    container.innerHTML = "";
    
    if (!trace || trace.length === 0) {
        container.innerHTML = `<div class="empty-telemetry"><p>No traces.</p></div>`;
        return;
    }
    
    trace.forEach(step => {
        const stepEl = document.createElement("div");
        stepEl.className = "trace-step";
        
        if (step.includes("[LangGraph Node:")) {
            stepEl.classList.add("accent");
            const formatted = step.replace("[LangGraph Node:", "<span class='badge' style='background:rgba(99,102,241,0.25); color:#818cf8; font-size:10px; padding:2px 6px; border-radius:4px; margin-right:4px;'>NODE</span>");
            stepEl.innerHTML = formatted;
        } else if (step.includes("Intent Classified") || step.includes("Retrieved") || step.includes("Gemini Step")) {
            stepEl.classList.add("success");
            stepEl.innerText = step;
        } else if (step.includes("Cosine similarity")) {
            const parts = step.split("|");
            stepEl.innerHTML = `<div>${escapeHTML(parts[0])}</div><div class="trace-math">${escapeHTML(parts[1] || "")}</div>`;
        } else {
            stepEl.innerText = step;
        }
        
        container.appendChild(stepEl);
    });
    
    container.scrollTop = container.scrollHeight;
}

// Suggested Follow-up buttons compiler
function renderFollowUps(questions) {
    const container = document.getElementById("follow-up-container");
    const list = document.getElementById("follow-up-list");
    list.innerHTML = "";
    
    if (!questions || questions.length === 0) {
        container.classList.add("hide");
        return;
    }
    
    questions.forEach(q => {
        const btn = document.createElement("button");
        btn.className = "follow-up-btn";
        btn.innerText = q;
        btn.addEventListener("click", () => {
            document.getElementById("chat-input").value = q;
            document.getElementById("chat-form").dispatchEvent(new Event("submit"));
        });
        list.appendChild(btn);
    });
    
    container.classList.remove("hide");
}

// ==========================================
// KNOWLEDGE BASE / ADMIN OPERATIONS
// ==========================================
async function loadAdminDocuments() {
    try {
        const response = await fetch(`${API_BASE}/admin/documents`, {
            headers: { "Authorization": `Bearer ${jwtToken}` }
        });
        
        if (response.status === 401) {
            handleLogout();
            return;
        }
        
        if (!response.ok) throw new Error("Failed to fetch documents.");
        
        const docs = await response.json();
        const tbody = document.getElementById("documents-table-body");
        tbody.innerHTML = "";
        
        if (docs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No documents currently uploaded.</td></tr>`;
            return;
        }
        
        docs.forEach(doc => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHTML(doc.title)}</strong></td>
                <td>${escapeHTML(doc.metadata.project)}</td>
                <td><span class="badge" style="background:rgba(99,102,241,0.1); color:var(--text-main); font-weight:normal; border-radius:4px; font-size:12px">${escapeHTML(doc.metadata.doc_type)}</span></td>
                <td>${escapeHTML(doc.metadata.uploaded_by || "System")}</td>
                <td>
                    <button class="btn btn-danger" onclick="deleteDocument(${doc.id})">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (err) {
        console.error(err);
    }
}

async function handleDocumentUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("upload-file");
    const projInput = document.getElementById("project-name");
    const typeSelect = document.getElementById("doc-type");
    
    if (fileInput.files.length === 0) return;
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_name", projInput.value.trim());
    formData.append("doc_type", typeSelect.value);
    
    const submitBtn = document.getElementById("upload-submit-btn");
    submitBtn.innerText = "Saving Content...";
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/admin/upload`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${jwtToken}` },
            body: formData
        });
        
        if (response.status === 401) {
            handleLogout();
            alert("Your session has expired. Please log in again.");
            return;
        }
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to upload file.");
        }
        
        // Reset upload elements
        fileInput.value = "";
        projInput.value = "";
        
        alert("File registered successfully. Remember to Re-index the Knowledge Base to compile vector arrays.");
        loadAdminDocuments();
    } catch (err) {
        alert("Upload Error: " + err.message);
    } finally {
        submitBtn.innerText = "Save Document Content";
        submitBtn.disabled = false;
    }
}

async function deleteDocument(docId) {
    if (!confirm("Are you sure you want to remove this document from the indexed knowledge base?")) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/documents/${docId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${jwtToken}` }
        });
        
        if (response.status === 401) {
            handleLogout();
            alert("Your session has expired. Please log in again.");
            return;
        }
        
        if (!response.ok) throw new Error("Deletion failed.");
        
        alert("Document deleted. Remember to click Re-index Knowledge Base.");
        loadAdminDocuments();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// Trigger RAG index refresh
async function handleReindex() {
    const reindexBtn = document.getElementById("reindex-btn");
    reindexBtn.innerText = "Indexing vectors...";
    reindexBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/admin/reindex`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${jwtToken}` }
        });
        
        if (response.status === 401) {
            handleLogout();
            alert("Your session has expired. Please log in again.");
            return;
        }
        
        if (!response.ok) throw new Error("Reindexing failed.");
        
        alert("Knowledge base vector store re-indexed successfully. Ready for semantic queries.");
    } catch (err) {
        alert("Re-index error: " + err.message);
    } finally {
        reindexBtn.innerText = "Re-index Knowledge Base";
        reindexBtn.disabled = false;
    }
}

// ==========================================
// SECURITY AUDITS
// ==========================================
async function loadSecurityAudits() {
    try {
        const response = await fetch(`${API_BASE}/admin/audits`, {
            headers: { "Authorization": `Bearer ${jwtToken}` }
        });
        
        if (response.status === 401) {
            handleLogout();
            return;
        }
        
        if (!response.ok) throw new Error("Failed to fetch audits.");
        
        const logs = await response.json();
        const tbody = document.getElementById("audits-table-body");
        tbody.innerHTML = "";
        
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No actions registered in database.</td></tr>`;
            return;
        }
        
        logs.forEach(log => {
            const tr = document.createElement("tr");
            
            // Format dates
            const date = new Date(log.timestamp);
            const dateStr = date.toLocaleString();
            
            tr.innerHTML = `
                <td style="font-family:monospace; font-size:12px">${dateStr}</td>
                <td><strong>${escapeHTML(log.username)}</strong></td>
                <td><span class="user-role">${escapeHTML(log.role)}</span></td>
                <td><span class="badge" style="background:rgba(245,158,11,0.15); color:var(--color-warning); font-family:monospace">${escapeHTML(log.action)}</span></td>
                <td style="font-size:13px">${escapeHTML(log.details)}</td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (err) {
        console.error(err);
    }
}

// Global hook to support onclick deletion in elements
window.deleteDocument = deleteDocument;

// ==========================================
// UTILITIES
// ==========================================
function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

function formatMarkdownBold(text) {
    // Simple regex to parse **bold** words to html tags
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// ==========================================
// FORGOT / RESET PASSWORD CONTROLLER
// ==========================================
function showForgotForm() {
    document.getElementById("login-form").classList.add("hide");
    document.getElementById("forgot-form").classList.remove("hide");
    document.getElementById("reset-form").classList.add("hide");
    
    document.getElementById("forgot-error").classList.add("hide");
    document.getElementById("forgot-success").classList.add("hide");
    document.getElementById("forgot-username").value = "";
}

function showLoginForm() {
    document.getElementById("login-form").classList.remove("hide");
    document.getElementById("forgot-form").classList.add("hide");
    document.getElementById("reset-form").classList.add("hide");
    
    document.getElementById("login-error").classList.add("hide");
    document.getElementById("username").value = "";
    document.getElementById("password").value = "";
}

function showResetForm(username, token) {
    document.getElementById("login-form").classList.add("hide");
    document.getElementById("forgot-form").classList.add("hide");
    document.getElementById("reset-form").classList.remove("hide");
    
    document.getElementById("reset-username").value = username;
    document.getElementById("reset-token").value = token || "";
    document.getElementById("new-password").value = "";
    
    document.getElementById("reset-error").classList.add("hide");
    document.getElementById("reset-success").classList.add("hide");
}

async function handleForgotSubmit(e) {
    e.preventDefault();
    const errorEl = document.getElementById("forgot-error");
    const successEl = document.getElementById("forgot-success");
    errorEl.classList.add("hide");
    successEl.classList.add("hide");
    
    const username = document.getElementById("forgot-username").value.trim();
    if (!username) return;
    
    const submitBtn = document.getElementById("forgot-submit-btn");
    submitBtn.innerText = "Requesting...";
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to generate reset token.");
        }
        
        const data = await response.json();
        
        successEl.innerText = "Reset token generated successfully! Opening reset window...";
        successEl.classList.remove("hide");
        
        // Auto-redirect to reset password form, pre-filling token
        setTimeout(() => {
            showResetForm(username, data.token);
            successEl.classList.add("hide");
        }, 1500);
        
    } catch (err) {
        errorEl.innerText = err.message;
        errorEl.classList.remove("hide");
    } finally {
        submitBtn.innerText = "Request Reset Token";
        submitBtn.disabled = false;
    }
}

async function handleResetSubmit(e) {
    e.preventDefault();
    const errorEl = document.getElementById("reset-error");
    const successEl = document.getElementById("reset-success");
    errorEl.classList.add("hide");
    successEl.classList.add("hide");
    
    const username = document.getElementById("reset-username").value.trim();
    const token = document.getElementById("reset-token").value.trim();
    const newPassword = document.getElementById("new-password").value;
    
    if (newPassword.length < 8) {
        errorEl.innerText = "Password must be at least 8 characters long.";
        errorEl.classList.remove("hide");
        return;
    }
    
    const submitBtn = document.getElementById("reset-submit-btn");
    submitBtn.innerText = "Updating...";
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/auth/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, token, new_password: newPassword })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to reset password.");
        }
        
        successEl.innerText = "Password updated successfully! Returning to login...";
        successEl.classList.remove("hide");
        
        setTimeout(() => {
            showLoginForm();
            successEl.classList.add("hide");
        }, 2000);
        
    } catch (err) {
        errorEl.innerText = err.message;
        errorEl.classList.remove("hide");
    } finally {
        submitBtn.innerText = "Update Password";
        submitBtn.disabled = false;
    }
}
