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
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [showExamples, setShowExamples] = useState(false);
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

  // 加载系统状态
  useEffect(() => {
    const fetchStatus = async () => {
      // 在等待 Agent 响应时暂停状态轮询，避免阻塞 chat 请求
      if (isLoading) {
        console.log('[DEBUG] Skipping status check while loading...');
        return;
      }
      
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
  }, [API_BASE, isLoading]); // 添加 isLoading 依赖

  // 发送消息
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      console.log('[DEBUG] Sending request to:', `${API_BASE}/api/chat`);
      console.log('[DEBUG] Message:', inputValue);
      
      // 创建一个带超时的 AbortController
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时
      
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          session_id: Date.now().toString()
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      
      console.log('[DEBUG] Response received!');
      console.log('[DEBUG] Response status:', response.status);
      console.log('[DEBUG] Response ok:', response.ok);
      console.log('[DEBUG] Response headers:', {
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length')
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      console.log('[DEBUG] Starting to parse JSON...');
      
      // 添加 JSON 解析超时
      const jsonTimeout = setTimeout(() => {
        console.error('[DEBUG] JSON parsing timeout!');
      }, 30000);
      
      const data = await response.json();
      clearTimeout(jsonTimeout);
      
      console.log('[DEBUG] JSON parsed successfully!');
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
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="app-container">
        {/* 侧边栏 */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>📚 Quick Actions</h3>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("我有哪些课程？")}
            >
              我的课程
            </button>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("本周有什么作业要交？")}
            >
              本周作业
            </button>
            <button 
              className="sidebar-button"
              onClick={() => sendExampleQuery("列出所有未提交的作业")}
            >
              未提交作业
            </button>
            <button 
              className="sidebar-button"
              onClick={() => setShowExamples(!showExamples)}
            >
              {showExamples ? '隐藏' : '显示'}更多示例
            </button>
          </div>

          {showExamples && (
            <div className="sidebar-section examples">
              <h4>💡 示例查询</h4>
              
              <div className="example-category">
                <h5>课程信息</h5>
                <button onClick={() => sendExampleQuery("显示我的课程列表")}>
                  显示我的课程列表
                </button>
                <button onClick={() => sendExampleQuery("我这学期上什么课？")}>
                  我这学期上什么课？
                </button>
              </div>

              <div className="example-category">
                <h5>作业管理</h5>
                <button onClick={() => sendExampleQuery("密码学课程的作业列表")}>
                  密码学课程的作业列表
                </button>
                <button onClick={() => sendExampleQuery("我有哪些未提交的作业？")}>
                  我有哪些未提交的作业？
                </button>
              </div>

              <div className="example-category">
                <h5>内容搜索</h5>
                <button onClick={() => sendExampleQuery("搜索 RSA 加密的内容")}>
                  搜索 RSA 加密的内容
                </button>
                <button onClick={() => sendExampleQuery("查找关于二叉树的资料")}>
                  查找关于二叉树的资料
                </button>
              </div>
            </div>
          )}

          <div className="sidebar-section">
            <button 
              className="sidebar-button danger"
              onClick={clearMessages}
            >
              🗑️ 清空对话
            </button>
          </div>

          <div className="sidebar-footer">
            <p className="sidebar-info">
              💡 提示：尝试用自然语言询问关于课程、作业或学习材料的问题
            </p>
          </div>
        </aside>

        {/* 聊天区域 */}
        <main className="chat-container">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h1>👋 欢迎使用 Canvas AI Agent</h1>
                <p>我可以帮你查询课程信息、管理作业、搜索学习资料等。</p>
                <p>试着问我一些问题吧！</p>
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
                placeholder="输入你的问题..."
                className="message-input"
                disabled={isLoading || !systemStatus?.agent_ready}
              />
              <button
                type="submit"
                className="send-button"
                disabled={isLoading || !inputValue.trim() || !systemStatus?.agent_ready}
              >
                {isLoading ? '发送中...' : '发送'}
              </button>
            </form>
            
            {!systemStatus?.agent_ready && (
              <div className="input-warning">
                ⚠️ Agent 初始化中，请稍候...
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
