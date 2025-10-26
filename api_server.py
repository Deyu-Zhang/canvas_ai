"""
Canvas AI Agent - FastAPI Backend Server
提供 RESTful API 接口供前端调用
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
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
import uuid
from collections import defaultdict

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

# 会话管理器
class SessionManager:
    """管理多个用户的会话和 Agent 实例"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.model_manager = None
        self.base_config = None
        self.manager_initialized = False
    
    async def initialize(self):
        """初始化会话管理器（只需要初始化一次）"""
        if self.manager_initialized:
            return True
        
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
            from src.logger import logger
            from pathlib import Path
            
            # 初始化 logger
            log_dir = Path("workdir/api_server")
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.init_logger(str(log_dir / "log.txt"))
            
            # 初始化模型管理器
            model_manager.init_models()
            self.model_manager = model_manager
            self.base_config = canvas_student_agent_config
            self.manager_initialized = True
            
            print("[OK] Session Manager initialized successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Session Manager initialization failed: {e}")
            traceback.print_exc()
            return False
    
    async def get_or_create_session(self, session_id: Optional[str] = None, username: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """获取或创建用户会话"""
        # 如果没有提供 session_id，创建新的
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 如果会话已存在，返回现有会话
        if session_id in self.sessions:
            return session_id, self.sessions[session_id]
        
        # 创建新会话
        try:
            from src.registry import AGENT
            
            # 获取模型
            model = self.model_manager.registed_models[self.base_config["model_id"]]
            
            # 准备 Agent 构建配置
            agent_build_config = dict(
                type=self.base_config["type"],
                config=self.base_config,
                model=model,
                tools=self.base_config["tools"],
                max_steps=self.base_config.get("max_steps", 10),
                name=self.base_config.get("name"),
                description=self.base_config.get("description"),
            )
            
            # 为该用户创建独立的 Agent 实例
            agent = AGENT.build(agent_build_config)
            
            # 存储会话信息
            session_data = {
                "session_id": session_id,
                "username": username or f"User_{session_id[:8]}",
                "agent": agent,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "message_count": 0
            }
            
            self.sessions[session_id] = session_data
            print(f"[NEW SESSION] Created session {session_id} for user '{session_data['username']}'")
            print(f"[SESSIONS] Total active sessions: {len(self.sessions)}")
            
            return session_id, session_data
            
        except Exception as e:
            print(f"[ERROR] Failed to create session: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    
    def update_session_activity(self, session_id: str):
        """更新会话的最后活动时间"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = datetime.now().isoformat()
            self.sessions[session_id]["message_count"] += 1
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息（不包含 agent 对象）"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session["session_id"],
                "username": session["username"],
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "message_count": session["message_count"]
            }
        return None
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """列出所有活动会话"""
        return [self.get_session_info(sid) for sid in self.sessions.keys()]
    
    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        if session_id in self.sessions:
            username = self.sessions[session_id]["username"]
            del self.sessions[session_id]
            print(f"[DELETE SESSION] Removed session {session_id} (user: {username})")
            print(f"[SESSIONS] Total active sessions: {len(self.sessions)}")
            return True
        return False

# 全局会话管理器
session_manager = SessionManager()

# 旧的全局 Agent（为了向后兼容，保留但不使用）
agent = None
agent_initialized = False

# 请求/响应模型
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str

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
    """应用启动时初始化 Session Manager"""
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    print("\n" + "="*60)
    print("[*] Canvas AI Agent API Server Starting...")
    print("[*] Multi-User Session Support Enabled")
    print("="*60 + "\n")
    
    success = await session_manager.initialize()
    
    if success:
        print("\n[OK] Server ready to accept requests")
        print("[OK] Multi-user support enabled - each user gets their own agent")
    else:
        print("\n[WARNING] Server started but session manager initialization failed")
        print("    Please check your .env configuration")
    
    print("\n" + "="*60 + "\n")

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": session_manager.manager_initialized,
        "active_sessions": len(session_manager.sessions)
    }

# 用户登录/创建会话
@app.post("/api/login")
async def login(request: LoginRequest):
    """用户登录或创建新会话"""
    try:
        session_id, session_data = await session_manager.get_or_create_session(
            username=request.username
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "username": session_data["username"],
            "message": f"Welcome, {session_data['username']}!",
            "created_at": session_data["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取会话信息
@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    session_info = session_manager.get_session_info(session_id)
    if not session_info:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_info

# 列出所有活动会话
@app.get("/api/sessions")
async def list_sessions():
    """列出所有活动会话（管理端点）"""
    return {
        "total_sessions": len(session_manager.sessions),
        "sessions": session_manager.list_active_sessions()
    }

# 删除会话
@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": "Session deleted"}

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
    
    status = "ready" if session_manager.manager_initialized else "initializing"
    message = f"All systems operational ({len(session_manager.sessions)} active sessions)" if session_manager.manager_initialized else "Session manager initialization in progress"
    
    return StatusResponse(
        status=status,
        canvas_connected=canvas_connected,
        openai_connected=openai_connected,
        agent_ready=session_manager.manager_initialized,
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
    """处理聊天请求（支持多用户）"""
    print(f"\n[*] Received chat request: {request.message[:50]}...")
    
    if not session_manager.manager_initialized:
        print("[!] Session manager not initialized!")
        raise HTTPException(
            status_code=503,
            detail="Session manager not initialized. Please check server configuration."
        )
    
    try:
        # 获取或创建会话
        session_id, session_data = await session_manager.get_or_create_session(
            session_id=request.session_id,
            username=request.username
        )
        
        print(f"[*] Processing with session ID: {session_id} (user: {session_data['username']})")
        
        # 获取该用户的 Agent 实例
        user_agent = session_data["agent"]
        
        # 调用 Agent 处理请求
        print(f"[*] Calling agent.run() for user '{session_data['username']}'...")
        response = await user_agent.run(request.message)
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
        
        # 更新会话活动时间
        session_manager.update_session_activity(session_id)
        
        print(f"[OK] Agent response generated ({len(response_str)} chars)")
        print(f"[DEBUG] First 200 chars: {response_str[:200]}...")
        print(f"[STATS] User '{session_data['username']}' has sent {session_data['message_count'] + 1} messages")
        
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


@app.get("/api/check-index-status")
async def check_index_status():
    """检查 Canvas 文件与 Vector Store 索引状态"""
    try:
        import aiohttp
        from pathlib import Path
        import json
        
        canvas_url = os.getenv("CANVAS_URL")
        canvas_token = os.getenv("CANVAS_ACCESS_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not canvas_url or not canvas_token:
            return {
                "status": "error",
                "error": "Canvas configuration not found",
                "details": "CANVAS_URL or CANVAS_ACCESS_TOKEN not set"
            }
        
        if not openai_api_key:
            return {
                "status": "error",
                "error": "OpenAI API key not found",
                "details": "OPENAI_API_KEY not set"
            }
        
        # 获取 Canvas 课程和文件
        headers = {
            "Authorization": f"Bearer {canvas_token}",
            "Accept": "application/json"
        }
        
        # 获取 Canvas 所有课程的所有文件（文件名列表）
        canvas_files_by_course = {}
        canvas_file_names = set()
        
        async with aiohttp.ClientSession() as session:
            # 获取所有课程
            async with session.get(
                f"{canvas_url}/api/v1/courses",
                headers=headers,
                params={"enrollment_state": "active", "per_page": 100}
            ) as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "error": "Failed to fetch Canvas courses",
                        "details": f"HTTP {response.status}"
                    }
                courses = await response.json()
            
            # 获取每个课程的所有文件
            for course in courses:
                course_id = course['id']
                course_name = course.get('name', f'Course {course_id}')
                
                # 获取该课程的所有文件（分页）
                course_files = []
                page = 1
                
                while True:
                    async with session.get(
                        f"{canvas_url}/api/v1/courses/{course_id}/files",
                        headers=headers,
                        params={"per_page": 100, "page": page}
                    ) as response:
                        if response.status == 200:
                            files = await response.json()
                            if not files:
                                break
                            
                            for file in files:
                                file_name = file.get('display_name', file.get('filename', ''))
                                if file_name:
                                    course_files.append(file_name)
                                    canvas_file_names.add(f"{course_name}::{file_name}")
                            
                            # 检查是否还有下一页
                            link_header = response.headers.get('Link', '')
                            if 'rel="next"' not in link_header:
                                break
                            page += 1
                        else:
                            # 如果遇到错误（包括 403），跳过这个课程
                            break
                
                if course_files:
                    canvas_files_by_course[course_name] = course_files
        
        total_canvas_files = len(canvas_file_names)
        
        # 检查 Vector Store 状态
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_api_key)
        
        try:
            # 从本地映射文件获取已索引的文件名
            file_index_path = Path(__file__).parent.parent / "file_index"
            
            # 确保 file_index 目录存在（第一次使用时创建）
            file_index_path.mkdir(parents=True, exist_ok=True)
            
            mapping_file = file_index_path / "vector_stores_mapping.json"
            
            indexed_file_names = set()
            has_local_index = mapping_file.exists()
            
            if has_local_index:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    
                    # 创建课程名映射：mapping中的key可能是 "课程代码_课程名"
                    # 我们需要提取实际的课程名部分（下划线后的部分）
                    for mapping_course_name, course_data in mapping.items():
                        # 尝试从mapping的课程名中提取实际课程名
                        # 格式可能是 "Fall 2025.CSE.3407.01_Fall_2025.CSE.3407.01 - Analysis of Algorithms"
                        # 我们取下划线后的部分
                        if '_' in mapping_course_name:
                            actual_course_name = mapping_course_name.split('_', 1)[1]
                        else:
                            actual_course_name = mapping_course_name
                        
                        for file_info in course_data.get('files', []):
                            # file_info['path'] 格式可能是 Windows 路径（反斜杠）或 Unix 路径（正斜杠）
                            file_path = file_info.get('path', '')
                            if file_path:
                                # 先标准化路径分隔符
                                file_path_normalized = file_path.replace('\\', '/')
                                file_name = file_path_normalized.split('/')[-1]
                                # 使用提取的实际课程名
                                indexed_file_names.add(f"{actual_course_name}::{file_name}")
            
            # 读取无法访问的文件列表
            inaccessible_files_set = set()
            inaccessible_files_file = file_index_path / "inaccessible_files.json"
            if inaccessible_files_file.exists():
                with open(inaccessible_files_file, 'r', encoding='utf-8') as f:
                    inaccessible_files_list = json.load(f)
                    for item in inaccessible_files_list:
                        course = item.get('course', '')
                        file_name = item.get('file_name', '')
                        if course and file_name:
                            inaccessible_files_set.add(f"{course}::{file_name}")
            
            # 比较文件名集合
            missing_files = canvas_file_names - indexed_file_names
            
            # 从 missing_files 中排除无法访问的文件
            missing_files = missing_files - inaccessible_files_set
            
            extra_files = indexed_file_names - canvas_file_names
            
            # 按课程组织缺失的文件
            missing_by_course = {}
            for full_name in missing_files:
                if '::' in full_name:
                    course_name, file_name = full_name.split('::', 1)
                    if course_name not in missing_by_course:
                        missing_by_course[course_name] = []
                    missing_by_course[course_name].append(file_name)
            
            # 判断状态
            total_indexed_files = len(indexed_file_names)
            missing_count = len(missing_files)
            
            if total_indexed_files == 0:
                status_type = "no_index"
                message = "No files indexed yet. First-time setup required."
            elif missing_count > 0:
                status_type = "partial_index"
                message = f"{missing_count} file(s) missing from index. Update recommended."
            else:
                status_type = "up_to_date"
                message = f"All {total_canvas_files} files are indexed."
            
            # 获取 Vector Store 信息
            vector_stores = openai_client.vector_stores.list(limit=100)
            vector_store_list = []
            for vs in vector_stores.data:
                file_count = vs.file_counts.completed if hasattr(vs, 'file_counts') else 0
                vector_store_list.append({
                    "id": vs.id,
                    "name": vs.name,
                    "file_count": file_count,
                    "created_at": vs.created_at
                })
            
            return {
                "status": "success",
                "index_status": status_type,
                "message": message,
                "details": {
                    "canvas_courses": len(canvas_files_by_course),
                    "canvas_files_total": total_canvas_files,
                    "indexed_files_total": total_indexed_files,
                    "missing_files_count": missing_count,
                    "extra_files_count": len(extra_files),
                    "vector_stores_count": len(vector_store_list),
                    "has_local_index": has_local_index,
                    "missing_by_course": {k: len(v) for k, v in missing_by_course.items()},
                    "missing_files_sample": list(missing_files)[:10],  # 显示前10个缺失文件
                    "vector_stores": vector_store_list[:5],
                    "inaccessible_files_count": len(inaccessible_files_set)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": "Failed to check Vector Stores",
                "details": str(e)
            }
            
    except Exception as e:
        print(f"[ERROR] check_index_status: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }


@app.post("/api/sync-files")
async def sync_files(background_tasks: BackgroundTasks):
    """触发文件同步：下载 Canvas 文件并上传到 Vector Store"""
    try:
        # 检查是否已经有同步任务在运行
        if hasattr(sync_files, 'is_running') and sync_files.is_running:
            return {
                "status": "already_running",
                "message": "File sync is already in progress"
            }
        
        # 启动后台任务
        sync_files.is_running = True
        background_tasks.add_task(run_file_sync)
        
        return {
            "status": "started",
            "message": "File synchronization started in background"
        }
        
    except Exception as e:
        sync_files.is_running = False
        print(f"[ERROR] sync_files: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

sync_files.is_running = False


async def run_file_sync():
    """后台运行文件同步"""
    try:
        print("[SYNC] Starting file synchronization...")
        
        # 调用 file_index_downloader 的 main 函数
        import sys
        from pathlib import Path
        
        # 添加脚本路径到 sys.path
        script_dir = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        # 导入并运行下载器（自动确认模式）
        from file_index_downloader import main as downloader_main
        await downloader_main(skip_download=False, course_id=None, auto_confirm=True)
        
        sync_files.is_running = False
        print("[SYNC] File synchronization completed!")
        
    except Exception as e:
        sync_files.is_running = False
        print(f"[SYNC ERROR] {e}")
        traceback.print_exc()


@app.get("/api/sync-status")
async def get_sync_status():
    """获取文件同步状态"""
    return {
        "is_running": getattr(sync_files, 'is_running', False),
        "timestamp": datetime.now().isoformat()
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

