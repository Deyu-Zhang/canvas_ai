import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  type: 'user' | 'agent' | 'system' | 'error';
  content: string;
  timestamp: string;
}

interface SystemStatus {
  status: string;
  canvas_connected: boolean;
  openai_connected: boolean;
  agent_ready: boolean;
  message: string;
  active_sessions?: number;
}

interface SessionInfo {
  session_id: string;
  username: string;
}

interface IndexStatus {
  status: string;
  index_status: string;
  message: string;
  details?: {
    canvas_courses: number;
    canvas_files_total: number;
    indexed_files_total: number;
    missing_files_count: number;
    extra_files_count: number;
    vector_stores_count: number;
    has_local_index: boolean;
    missing_by_course: { [key: string]: number };
    missing_files_sample: string[];
  };
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [showExamples, setShowExamples] = useState(false);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // 动态获取 API 地址，支持 localhost 和 localtunnel
  const API_BASE = process.env.REACT_APP_API_URL || window.location.origin;

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 检查索引状态
  const checkIndexStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/check-index-status`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setIndexStatus(data);
        
        // 如果是第一次使用或需要更新，显示对话框
        if (data.index_status === 'no_index' || data.index_status === 'partial_index') {
          setShowSyncDialog(true);
        }
      } else {
        console.error('[INDEX] Check failed:', data.error);
      }
    } catch (error) {
      console.error('[INDEX] Error checking status:', error);
    }
  };

  // 触发文件同步
  const startSync = async () => {
    try {
      setIsSyncing(true);
      setShowSyncDialog(false);
      
      const response = await fetch(`${API_BASE}/api/sync-files`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.status === 'started') {
        // 添加系统消息
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'system',
          content: 'File synchronization started. This may take a few minutes...',
          timestamp: new Date().toISOString()
        }]);
        
        // 轮询检查同步状态
        const checkInterval = setInterval(async () => {
          const statusResponse = await fetch(`${API_BASE}/api/sync-status`);
          const statusData = await statusResponse.json();
          
          if (!statusData.is_running) {
            clearInterval(checkInterval);
            setIsSyncing(false);
            
            // 重新检查索引状态
            await checkIndexStatus();
            
            setMessages(prev => [...prev, {
              id: (Date.now() + 1).toString(),
              type: 'system',
              content: 'File synchronization completed! All files are now indexed.',
              timestamp: new Date().toISOString()
            }]);
          }
        }, 5000);  // 每5秒检查一次
      }
    } catch (error) {
      console.error('[SYNC] Error:', error);
      setIsSyncing(false);
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'error',
        content: `Sync error: ${error}`,
        timestamp: new Date().toISOString()
      }]);
    }
  };

  // 自动初始化会话（从 localStorage 恢复或创建新会话）
  useEffect(() => {
    const initSession = () => {
      let savedSession = localStorage.getItem('canvas_ai_session');
      
      if (savedSession) {
        const session = JSON.parse(savedSession);
        setSessionInfo(session);
        console.log('[SESSION] Restored session:', session);
      } else {
        // 自动创建新会话
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const randomNum = Math.floor(Math.random() * 9999) + 1;
        const newSession: SessionInfo = {
          session_id: newSessionId,
          username: `User_${randomNum}`
        };
        
        setSessionInfo(newSession);
        localStorage.setItem('canvas_ai_session', JSON.stringify(newSession));
        console.log('[SESSION] Created new session:', newSession);
        
        // 添加欢迎消息
        setMessages([{
          id: Date.now().toString(),
          type: 'system',
          content: `Welcome! You are now ${newSession.username}. Each user gets their own independent agent instance.`,
          timestamp: new Date().toISOString()
        }]);
      }
    };

    initSession();
    // 初始化后检查索引状态
    checkIndexStatus();
  }, []);

  // 重置会话（清除当前会话，创建新的）
  const handleNewSession = () => {
    localStorage.removeItem('canvas_ai_session');
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const randomNum = Math.floor(Math.random() * 9999) + 1;
    const newSession: SessionInfo = {
      session_id: newSessionId,
      username: `User_${randomNum}`
    };
    
    setSessionInfo(newSession);
    localStorage.setItem('canvas_ai_session', JSON.stringify(newSession));
    setMessages([{
      id: Date.now().toString(),
      type: 'system',
      content: `New session started! You are now ${newSession.username}.`,
      timestamp: new Date().toISOString()
    }]);
    console.log('[SESSION] New session created:', newSession);
  };

  // 加载系统状态
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        setSystemStatus(data);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // 每10秒更新一次

    return () => clearInterval(interval);
  }, [API_BASE]);

  // 发送消息
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading || !sessionInfo) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      console.log('[DEBUG] Sending request to:', `${API_BASE}/api/chat`);
      console.log('[DEBUG] Message:', messageToSend);
      console.log('[DEBUG] Session:', sessionInfo);
      
      // 不设置超时限制，等待响应完成
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageToSend,
          session_id: sessionInfo.session_id,
          username: sessionInfo.username
        })
      });
      
      console.log('[DEBUG] Response received!');
      console.log('[DEBUG] Response status:', response.status);
      console.log('[DEBUG] Response ok:', response.ok);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[DEBUG] Response data:', data);
      console.log('[DEBUG] Response success:', data.success);
      console.log('[DEBUG] Response content length:', data.response?.length);

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: data.success ? 'agent' : 'error',
        content: data.response || data.error || 'No response',
        timestamp: data.timestamp
      };

      setMessages(prev => [...prev, agentMessage]);
    } catch (error) {
      console.error('[DEBUG] Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: `Error: ${error}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 发送示例查询
  const sendExampleQuery = (query: string) => {
    setInputValue(query);
    setShowExamples(false);
  };

  // 清空对话
  const clearMessages = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      {/* 头部 */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <span className="logo-icon">🎓</span>
              <span className="logo-text">Canvas AI Agent</span>
            </div>
            {sessionInfo && (
              <div className="user-info">
                <span className="user-badge">👤 {sessionInfo.username}</span>
                <button className="logout-button" onClick={handleNewSession} title="New Session">
                  🔄
                </button>
              </div>
            )}
          </div>
          
          <div className="header-right">
            {systemStatus && (
              <div className="status-indicators">
                <StatusIndicator 
                  label="Canvas" 
                  active={systemStatus.canvas_connected} 
                />
                <StatusIndicator 
                  label="OpenAI" 
                  active={systemStatus.openai_connected} 
                />
                <StatusIndicator 
                  label="Agent" 
                  active={systemStatus.agent_ready} 
                />
                {systemStatus.active_sessions !== undefined && (
                  <span className="sessions-count">
                    👥 {systemStatus.active_sessions}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 索引状态栏 */}
      {indexStatus && (
        <div className={`index-status-bar ${indexStatus.index_status}`}>
          <div className="index-status-content">
            <div className="index-status-info">
              {indexStatus.index_status === 'up_to_date' && (
                <span className="status-icon">✅</span>
              )}
              {indexStatus.index_status === 'partial_index' && (
                <span className="status-icon">⚠️</span>
              )}
              {indexStatus.index_status === 'no_index' && (
                <span className="status-icon">❌</span>
              )}
              <span className="status-message">{indexStatus.message}</span>
              {indexStatus.details && (
                <span className="status-details">
                  ({indexStatus.details.indexed_files_total} / {indexStatus.details.canvas_files_total} files)
                </span>
              )}
            </div>
            {isSyncing && (
              <div className="sync-progress">
                <div className="spinner"></div>
                <span>Synchronizing files...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 同步确认对话框 */}
      {showSyncDialog && (
        <div className="sync-dialog-overlay" onClick={() => setShowSyncDialog(false)}>
          <div className="sync-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>File Index Update Required</h3>
            <p>
              {indexStatus?.index_status === 'no_index' 
                ? 'No files have been indexed yet. Would you like to download and index all course files now?'
                : 'Some files are not indexed. Would you like to update the index?'
              }
            </p>
            {indexStatus?.details && (
              <div className="sync-details">
                <p><strong>Canvas Courses:</strong> {indexStatus.details.canvas_courses}</p>
                <p><strong>Total Files in Canvas:</strong> {indexStatus.details.canvas_files_total}</p>
                <p><strong>Currently Indexed:</strong> {indexStatus.details.indexed_files_total}</p>
                <p><strong>Missing Files:</strong> {indexStatus.details.missing_files_count}</p>
              </div>
            )}
            <div className="sync-dialog-actions">
              <button className="btn-cancel" onClick={() => setShowSyncDialog(false)}>
                Cancel
              </button>
              <button className="btn-sync" onClick={startSync}>
                Start Sync
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 主内容区 */}
      <div className="app-container">
        {/* 侧边栏 */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>📚 Quick Actions</h3>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("What courses do I have?")}
            >
              My Courses
            </button>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("What assignments are due this week?")}
            >
              This Week's Assignments
            </button>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("List all unsubmitted assignments")}
            >
              Unsubmitted Assignments
            </button>
            <button 
              className="sidebar-button"
              onClick={() => setShowExamples(!showExamples)}
            >
              {showExamples ? 'Hide' : 'Show'} More Examples
            </button>
          </div>

          {showExamples && (
            <div className="sidebar-section examples">
              <h4>💡 Example Queries</h4>
              
              <div className="example-category">
                <h5>Course Info</h5>
                <button onClick={() => sendExampleQuery("Show my course list")}>
                  Show my course list
                </button>
                <button onClick={() => sendExampleQuery("What courses am I taking this semester?")}>
                  What courses am I taking?
                </button>
              </div>

              <div className="example-category">
                <h5>Assignments</h5>
                <button onClick={() => sendExampleQuery("List assignments for cryptography course")}>
                  Cryptography assignments
                </button>
                <button onClick={() => sendExampleQuery("What assignments are due soon?")}>
                  Upcoming assignments
                </button>
              </div>

              <div className="example-category">
                <h5>Content Search</h5>
                <button onClick={() => sendExampleQuery("Search for RSA encryption content")}>
                  Search RSA encryption
                </button>
                <button onClick={() => sendExampleQuery("Find materials about binary trees")}>
                  Find binary tree resources
                </button>
              </div>
            </div>
          )}

          <div className="sidebar-section">
            <button 
              className="sidebar-button danger"
              onClick={clearMessages}
            >
              🗑️ Clear Chat
            </button>
          </div>

          <div className="sidebar-footer">
            <p className="sidebar-info">
              💡 Tip: Ask questions about courses, assignments, or learning materials in natural language
            </p>
          </div>
        </aside>

        {/* 聊天区域 */}
        <main className="chat-container">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h1>👋 Welcome to Canvas AI Agent</h1>
                <p>I can help you with course information, assignments, and searching learning materials.</p>
                <p>Try asking me a question!</p>
              </div>
            ) : (
              messages.map(message => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            
            {isLoading && (
              <div className="message agent-message">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* 输入区域 */}
          <div className="input-container">
            <form onSubmit={sendMessage} className="input-form">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your question..."
                className="message-input"
                disabled={isLoading || !systemStatus?.agent_ready}
              />
              <button
                type="submit"
                className="send-button"
                disabled={isLoading || !inputValue.trim() || !systemStatus?.agent_ready}
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </form>
            
            {!systemStatus?.agent_ready && (
              <div className="input-warning">
                ⚠️ Agent initializing, please wait...
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

// 状态指示器组件
const StatusIndicator: React.FC<{ label: string; active: boolean }> = ({ label, active }) => (
  <div className={`status-indicator ${active ? 'active' : 'inactive'}`}>
    <span className="status-dot"></span>
    <span className="status-label">{label}</span>
  </div>
);

// 消息气泡组件
const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.type === 'user';
  const isError = message.type === 'error';
  const isSystem = message.type === 'system';

  return (
    <div className={`message ${message.type}-message`}>
      {!isUser && (
        <div className="message-avatar">
          {isError ? '⚠️' : isSystem ? 'ℹ️' : '🤖'}
        </div>
      )}
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        <div className="message-time">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
      {isUser && (
        <div className="message-avatar user-avatar">👤</div>
      )}
    </div>
  );
};

export default App;
