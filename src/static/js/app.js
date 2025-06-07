// Resume Rebuilder Web Application JavaScript

class ResumeRebuilderApp {
    constructor() {
        this.currentSession = {
            resume_content: null,
            job_description: '',
            chat_history: [],
            file_name: '',
            session_name: 'Default Session'
        };
        
        this.isLoading = false;
        this.editHistory = [];
        this.editHistoryIndex = -1;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupFileUpload();
        this.setupChat();
        this.setupEditor();
        this.updateUIState();
    }
    
    setupEventListeners() {
        // Header buttons
        document.getElementById('load-session-btn').addEventListener('click', () => this.loadSession());
        document.getElementById('save-session-btn').addEventListener('click', () => this.saveSession());
        document.getElementById('help-btn').addEventListener('click', () => this.showHelp());
        
        // Chat toggle
        document.getElementById('toggle-chat-btn').addEventListener('click', () => this.toggleChatPanel());
        
        // Quick actions
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.closest('.quick-action-btn').dataset.action;
                this.handleQuickAction(action);
            });
        });
        
        // Chat controls
        document.getElementById('send-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('clear-chat-btn').addEventListener('click', () => this.clearChat());
        document.getElementById('chat-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Preview controls
        document.getElementById('upload-btn').addEventListener('click', () => this.triggerFileUpload());
        document.getElementById('refresh-preview-btn').addEventListener('click', () => this.refreshPreview());
        document.getElementById('download-btn').addEventListener('click', () => this.downloadResume());
        
        // Editor controls
        document.getElementById('undo-btn').addEventListener('click', () => this.undo());
        document.getElementById('redo-btn').addEventListener('click', () => this.redo());
        document.getElementById('bold-btn').addEventListener('click', () => this.formatText('bold'));
        document.getElementById('italic-btn').addEventListener('click', () => this.formatText('italic'));
        document.getElementById('find-btn').addEventListener('click', () => this.showFindDialog());
        
        // Content editor changes
        const editor = document.getElementById('content-editor');
        editor.addEventListener('input', () => {
            this.onContentChange();
            this.updateEditorStats();
        });
        
        editor.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'z':
                        e.preventDefault();
                        if (e.shiftKey) this.redo();
                        else this.undo();
                        break;
                    case 'y':
                        e.preventDefault();
                        this.redo();
                        break;
                    case 's':
                        e.preventDefault();
                        this.saveSession();
                        break;
                    case 'f':
                        e.preventDefault();
                        this.showFindDialog();
                        break;
                }
            }
        });
    }
    
    setupFileUpload() {
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadFile(e.target.files[0]);
            }
        });
    }
    
    setupChat() {
        // Initialize chat with welcome message
        this.updateChatHistory();
    }
    
    setupEditor() {
        this.updateEditorStats();
    }
    
    // File Operations
    triggerFileUpload() {
        document.getElementById('file-input').click();
    }
    
    async uploadFile(file) {
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentSession.resume_content = result.content;
                this.currentSession.file_name = result.filename;
                
                this.updatePreview();
                this.updateEditor();
                this.addToEditHistory();
                
                this.showToast('Resume uploaded successfully!', 'success');
            } else {
                this.showToast(result.error || 'Upload failed', 'error');
            }
        } catch (error) {
            this.showToast('Error uploading file: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
            // Reset file input to allow re-uploading the same file
            document.getElementById('file-input').value = '';
        }
    }
    
    // Chat Operations
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to history
        this.currentSession.chat_history.push({
            type: 'user',
            message: message,
            timestamp: new Date().toLocaleTimeString()
        });
        
        input.value = '';
        this.updateChatHistory();
        
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    timestamp: new Date().toLocaleTimeString()
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // AI response is automatically added by the server
                this.currentSession.chat_history.push({
                    type: 'assistant',
                    message: result.response,
                    timestamp: new Date().toLocaleTimeString()
                });
                
                this.updateChatHistory();
            } else {
                this.showToast(result.error || 'Chat failed', 'error');
            }
        } catch (error) {
            this.showToast('Error sending message: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    clearChat() {
        this.currentSession.chat_history = [];
        this.updateChatHistory();
        this.showToast('Chat cleared', 'info');
    }
    
    updateChatHistory() {
        const chatHistory = document.getElementById('chat-history');
        chatHistory.innerHTML = '';
        
        // Add welcome message if no history
        if (this.currentSession.chat_history.length === 0) {
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'message assistant-message';
            welcomeMsg.innerHTML = `
                <div class="message-content">
                    <strong>AI Assistant:</strong> Welcome to Resume Rebuilder! Upload your resume to get started, or ask me any questions about resume optimization.
                </div>
            `;
            chatHistory.appendChild(welcomeMsg);
        }
        
        // Add chat history
        this.currentSession.chat_history.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.type}-message fade-in`;
            
            const prefix = msg.type === 'user' ? 'You:' : 'AI Assistant:';
            messageDiv.innerHTML = `
                <div class="message-content">
                    <strong>${prefix}</strong> ${msg.message}
                    <div style="font-size: 0.8em; opacity: 0.7; margin-top: 0.25rem;">${msg.timestamp}</div>
                </div>
            `;
            
            chatHistory.appendChild(messageDiv);
        });
        
        // Scroll to bottom
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Quick Actions
    async handleQuickAction(action) {
        if (!this.currentSession.resume_content) {
            this.showToast('Please upload a resume first', 'error');
            return;
        }
        
        if (action === 'tailor') {
            this.showJobModal();
            return;
        }
        
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/quick-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    job_description: this.currentSession.job_description
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Add result to chat
                this.currentSession.chat_history.push({
                    type: 'assistant',
                    message: result.result,
                    timestamp: new Date().toLocaleTimeString()
                });
                
                this.updateChatHistory();
                this.showToast(`${action} completed!`, 'success');
            } else {
                this.showToast(result.error || 'Action failed', 'error');
            }
        } catch (error) {
            this.showToast('Error processing action: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }
    
    // Editor Operations
    onContentChange() {
        const editor = document.getElementById('content-editor');
        this.currentSession.resume_content = editor.value;
        
        // Update content on server
        this.updateServerContent();
        
        // Update preview
        this.updatePreview();
    }
    
    async updateServerContent() {
        if (this.isLoading) return;
        
        try {
            await fetch('/api/update-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: this.currentSession.resume_content
                })
            });
        } catch (error) {
            console.error('Error updating server content:', error);
        }
    }
    
    addToEditHistory() {
        // Remove any future history if we're not at the end
        this.editHistory = this.editHistory.slice(0, this.editHistoryIndex + 1);
        
        // Add current state
        this.editHistory.push(this.currentSession.resume_content);
        this.editHistoryIndex = this.editHistory.length - 1;
        
        // Limit history size
        if (this.editHistory.length > 50) {
            this.editHistory.shift();
            this.editHistoryIndex--;
        }
    }
    
    undo() {
        if (this.editHistoryIndex > 0) {
            this.editHistoryIndex--;
            this.currentSession.resume_content = this.editHistory[this.editHistoryIndex];
            this.updateEditor();
            this.updatePreview();
        }
    }
    
    redo() {
        if (this.editHistoryIndex < this.editHistory.length - 1) {
            this.editHistoryIndex++;
            this.currentSession.resume_content = this.editHistory[this.editHistoryIndex];
            this.updateEditor();
            this.updatePreview();
        }
    }
    
    formatText(format) {
        const editor = document.getElementById('content-editor');
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        const selectedText = editor.value.substring(start, end);
        
        if (selectedText) {
            let formattedText;
            switch (format) {
                case 'bold':
                    formattedText = `**${selectedText}**`;
                    break;
                case 'italic':
                    formattedText = `*${selectedText}*`;
                    break;
                default:
                    return;
            }
            
            editor.value = editor.value.substring(0, start) + formattedText + editor.value.substring(end);
            this.onContentChange();
            this.addToEditHistory();
        }
    }
    
    showFindDialog() {
        const searchTerm = prompt('Find text:');
        if (searchTerm) {
            const editor = document.getElementById('content-editor');
            const content = editor.value;
            const index = content.toLowerCase().indexOf(searchTerm.toLowerCase());
            
            if (index !== -1) {
                editor.focus();
                editor.setSelectionRange(index, index + searchTerm.length);
            } else {
                this.showToast('Text not found', 'info');
            }
        }
    }
    
    updateEditor() {
        const editor = document.getElementById('content-editor');
        editor.value = this.currentSession.resume_content || '';
        this.updateEditorStats();
    }
    
    updateEditorStats() {
        const editor = document.getElementById('content-editor');
        const content = editor.value;
        
        const charCount = content.length;
        const wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
        const lineCount = content.split('\n').length;
        
        document.getElementById('char-count').textContent = `${charCount} characters`;
        document.getElementById('word-count').textContent = `${wordCount} words`;
        document.getElementById('line-count').textContent = `${lineCount} lines`;
    }
    
    // Preview Operations
    updatePreview() {
        const previewDisplay = document.getElementById('preview-display');
        
        if (this.currentSession.resume_content) {
            previewDisplay.innerHTML = `
                <div class="resume-content fade-in">
                    ${this.formatPreviewContent(this.currentSession.resume_content)}
                </div>
            `;
        } else {
            previewDisplay.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-upload"></i>
                    <h4>No Resume Loaded</h4>
                    <p>Upload a PDF or text file to see your resume preview here.</p>
                    <button class="btn btn-primary" onclick="app.triggerFileUpload()">
                        <i class="fas fa-upload"></i> Upload Resume
                    </button>
                </div>
            `;
        }
    }
    
    formatPreviewContent(content) {
        // Basic formatting for preview
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    refreshPreview() {
        this.updatePreview();
        this.showToast('Preview refreshed', 'info');
    }
    
    downloadResume() {
        if (!this.currentSession.resume_content) {
            this.showToast('No resume content to download', 'error');
            return;
        }
        
        const blob = new Blob([this.currentSession.resume_content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.currentSession.file_name || 'resume.txt';
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Resume downloaded', 'success');
    }
    
    // UI Operations
    toggleChatPanel() {
        const chatPanel = document.getElementById('chat-panel');
        const toggleBtn = document.getElementById('toggle-chat-btn');
        
        chatPanel.classList.toggle('collapsed');
        
        if (chatPanel.classList.contains('collapsed')) {
            toggleBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        const overlay = document.getElementById('loading-overlay');
        
        if (loading) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }
    
    updateUIState() {
        this.updatePreview();
        this.updateEditor();
        this.updateChatHistory();
    }
    
    // Session Management
    async saveSession() {
        try {
            const response = await fetch('/api/session');
            const sessionData = await response.json();
            
            const blob = new Blob([JSON.stringify(sessionData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `resume_session_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            this.showToast('Session saved successfully', 'success');
        } catch (error) {
            this.showToast('Error saving session: ' + error.message, 'error');
        }
    }
    
    loadSession() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const sessionData = JSON.parse(text);
                
                const response = await fetch('/api/session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(sessionData)
                });
                
                if (response.ok) {
                    this.currentSession = sessionData;
                    this.updateUIState();
                    this.showToast('Session loaded successfully', 'success');
                } else {
                    this.showToast('Error loading session', 'error');
                }
            } catch (error) {
                this.showToast('Error loading session: ' + error.message, 'error');
            }
        };
        
        input.click();
    }
    
    // Job Description Modal
    showJobModal() {
        document.getElementById('job-modal').classList.add('show');
    }
    
    showHelp() {
        this.showToast('Help documentation coming soon!', 'info');
    }
}

// Modal Functions (Global)
function closeJobModal() {
    document.getElementById('job-modal').classList.remove('show');
}

async function submitJobDescription() {
    const jobDescription = document.getElementById('job-description').value.trim();
    
    if (!jobDescription) {
        app.showToast('Please enter a job description', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/job-description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_description: jobDescription
            })
        });
        
        if (response.ok) {
            app.currentSession.job_description = jobDescription;
            closeJobModal();
            app.handleQuickAction('tailor');
        } else {
            app.showToast('Error saving job description', 'error');
        }
    } catch (error) {
        app.showToast('Error: ' + error.message, 'error');
    }
}

// Initialize App
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ResumeRebuilderApp();
});