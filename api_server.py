"""
Canvas AI Agent - FastAPI Backend Server
提供 RESTful API 接口供前端调用
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import traceback

# 导入 Agent 相关模块
from configs.canvas_agent_config import canvas_student_agent_config
from src.agent.general_agent import GeneralAgent

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="Canvas AI Agent API",
    description="Intelligent assistant for Canvas LMS",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
agent = None
agent_initialized = False

# 请求/响应模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    success: bool
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    canvas_connected: bool
    openai_connected: bool
    agent_ready: bool
    message: str

class ToolInfo(BaseModel):
    name: str
    description: str
    category: str

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# 初始化 Agent
async def initialize_agent():
    """初始化 Canvas AI Agent"""
    global agent, agent_initialized
    
    try:
        # 检查环境变量
        canvas_url = os.getenv("CANVAS_URL")
        canvas_token = os.getenv("CANVAS_ACCESS_TOKEN")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not all([canvas_url, canvas_token, azure_key, openai_key]):
            raise Exception("Missing required environment variables")
        
        # 导入必要的模块
        from src.models import model_manager
        from src.registry import AGENT
        from src.logger import logger
        from pathlib import Path
        
        # 初始化 logger
        log_dir = Path("workdir/api_server")
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.init_logger(str(log_dir / "log.txt"))
        
        # 初始化模型管理器
        model_manager.init_models()
        
        # 获取模型
        model = model_manager.registed_models[canvas_student_agent_config["model_id"]]
        
        # 准备 Agent 构建配置
        agent_build_config = dict(
            type=canvas_student_agent_config["type"],
            config=canvas_student_agent_config,
            model=model,
            tools=canvas_student_agent_config["tools"],
            max_steps=canvas_student_agent_config.get("max_steps", 10),
            name=canvas_student_agent_config.get("name"),
            description=canvas_student_agent_config.get("description"),
        )
        
        # 使用 Registry 创建 Agent
        agent = AGENT.build(agent_build_config)
        agent_initialized = True
        
        print("[OK] Agent initialized successfully")
        print(f"[OK] Loaded {len(canvas_student_agent_config['tools'])} Canvas API tools")
        return True
        
    except Exception as e:
        print(f"[ERROR] Agent initialization failed: {e}")
        traceback.print_exc()
        return False

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 Agent"""
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("\n" + "="*60)
    print("[*] Canvas AI Agent API Server Starting...")
    print("="*60 + "\n")
    
    success = await initialize_agent()
    
    if success:
        print("\n[OK] Server ready to accept requests")
    else:
        print("\n[WARNING] Server started but agent initialization failed")
        print("    Please check your .env configuration")
    
    print("\n" + "="*60 + "\n")

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": agent_initialized
    }

# 系统状态
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取系统状态"""
    canvas_url = os.getenv("CANVAS_URL")
    canvas_token = os.getenv("CANVAS_ACCESS_TOKEN")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    canvas_connected = bool(canvas_url and canvas_token)
    openai_connected = bool(azure_key and openai_key)
    
    status = "ready" if agent_initialized else "initializing"
    message = "All systems operational" if agent_initialized else "Agent initialization in progress"
    
    return StatusResponse(
        status=status,
        canvas_connected=canvas_connected,
        openai_connected=openai_connected,
        agent_ready=agent_initialized,
        message=message
    )

# 测试端点
@app.post("/api/test")
async def test_endpoint(request: ChatRequest):
    """测试 POST 请求是否正常"""
    print(f"[TEST] Received test request: {request.message}")
    return {"status": "ok", "message": f"Echo: {request.message}"}

# 聊天端点（HTTP）
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理聊天请求"""
    print(f"\n[*] Received chat request: {request.message[:50]}...")
    
    if not agent_initialized:
        print("[!] Agent not initialized!")
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized. Please check server configuration."
        )
    
    try:
        # 生成会话 ID
        session_id = request.session_id or datetime.now().strftime("%Y%m%d%H%M%S")
        print(f"[*] Processing with session ID: {session_id}")
        
        # 调用 Agent 处理请求
        print("[*] Calling agent.run()...")
        response = await agent.run(request.message)
        print(f"[DEBUG] Response type: {type(response)}")
        
        # 处理 ToolResult 对象
        from src.tools.tools import ToolResult
        if isinstance(response, ToolResult):
            print("[DEBUG] Response is ToolResult, extracting output...")
            response_str = str(response.output) if response.output is not None else "No output"
        elif response is None:
            response_str = "Agent returned no response"
        else:
            response_str = str(response)
        
        print(f"[OK] Agent response generated ({len(response_str)} chars)")
        print(f"[DEBUG] First 200 chars: {response_str[:200]}...")
        
        chat_response = ChatResponse(
            response=response_str,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            success=True
        )
        
        print(f"[DEBUG] ChatResponse object: success={chat_response.success}, response_len={len(chat_response.response)}")
        
        return chat_response
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        print(f"✗ {error_msg}")
        traceback.print_exc()
        
        return ChatResponse(
            response="",
            session_id=request.session_id or "",
            timestamp=datetime.now().isoformat(),
            success=False,
            error=error_msg
        )

# WebSocket 聊天端点
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天连接"""
    await manager.connect(websocket)
    
    try:
        # 发送欢迎消息
        await manager.send_message({
            "type": "system",
            "message": "Connected to Canvas AI Agent",
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        while True:
            # 接收消息
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                continue
            
            # 发送处理中状态
            await manager.send_message({
                "type": "status",
                "message": "Processing...",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
            try:
                # 调用 Agent 处理
                if agent_initialized:
                    response = await agent.run(message)
                    
                    # 发送响应
                    await manager.send_message({
                        "type": "response",
                        "message": str(response),
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    }, websocket)
                else:
                    await manager.send_message({
                        "type": "error",
                        "message": "Agent not initialized",
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    }, websocket)
                    
            except Exception as e:
                # 发送错误消息
                await manager.send_message({
                    "type": "error",
                    "message": f"Error: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

# 获取可用工具列表
@app.get("/api/tools", response_model=List[ToolInfo])
async def get_tools():
    """获取所有可用的工具列表"""
    if not agent_initialized:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized"
        )
    
    tools = []
    
    # Canvas 工具
    canvas_tools = [
        {"name": "canvas_list_courses", "description": "列出所有课程", "category": "course"},
        {"name": "canvas_get_course", "description": "获取课程详情", "category": "course"},
        {"name": "canvas_list_assignments", "description": "列出作业", "category": "assignment"},
        {"name": "canvas_get_assignment", "description": "获取作业详情", "category": "assignment"},
        {"name": "canvas_list_course_files", "description": "列出课程文件", "category": "file"},
        {"name": "canvas_download_file", "description": "下载文件", "category": "file"},
        {"name": "canvas_list_announcements", "description": "查看公告", "category": "communication"},
        {"name": "canvas_list_discussions", "description": "查看讨论", "category": "communication"},
    ]
    
    # Vector Store 工具
    vector_tools = [
        {"name": "vector_store_list", "description": "列出所有知识库", "category": "search"},
        {"name": "vector_store_search", "description": "搜索课程内容", "category": "search"},
        {"name": "vector_store_list_files", "description": "列出知识库文件", "category": "search"},
    ]
    
    tools = [ToolInfo(**tool) for tool in canvas_tools + vector_tools]
    
    return tools

# 示例查询
@app.get("/api/examples")
async def get_examples():
    """获取示例查询"""
    return {
        "examples": [
            {
                "category": "课程信息",
                "queries": [
                    "我有哪些课程？",
                    "显示我的课程列表",
                    "我这学期上什么课？"
                ]
            },
            {
                "category": "作业管理",
                "queries": [
                    "我有哪些未提交的作业？",
                    "本周有什么作业要交？",
                    "密码学课程的作业列表"
                ]
            },
            {
                "category": "内容搜索",
                "queries": [
                    "搜索 RSA 加密的内容",
                    "查找关于二叉树的资料",
                    "课程大纲里说了什么？"
                ]
            },
            {
                "category": "文件管理",
                "queries": [
                    "下载密码学课程的教学大纲",
                    "列出算法课程的所有文件",
                    "查看课程资料"
                ]
            }
        ]
    }

# 静态文件服务（前端）
try:
    from pathlib import Path
    # 使用绝对路径，相对于 api_server.py 所在目录
    script_dir = Path(__file__).parent
    frontend_build = script_dir / "frontend" / "build"
    
    if frontend_build.exists():
        app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
        print(f"[OK] Frontend mounted from: {frontend_build}")
    else:
        print(f"[WARNING] Frontend build not found at: {frontend_build}")
        print("         Run 'npm run build' in frontend directory.")
except Exception as e:
    print(f"[WARNING] Could not mount frontend: {e}")

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # 设置编码
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    # 运行服务器
    port = int(os.getenv("PORT", 8000))
    
    print(f"\n[*] Starting server on http://localhost:{port}")
    print(f"[*] API docs: http://localhost:{port}/docs")
    print(f"[*] Frontend: http://localhost:{port}/\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

