# 🌐 Canvas AI Agent - Web Frontend 完整指南

## 目录
- [功能特点](#功能特点)
- [快速开始](#快速开始)
- [界面预览](#界面预览)
- [详细使用](#详细使用)
- [LocalTunnel 配置](#localtunnel-配置)
- [部署指南](#部署指南)

---

## 功能特点

### 🎨 现代化 UI
- 响应式设计，支持桌面和移动设备
- 渐变背景，毛玻璃效果
- 流畅的动画和过渡效果
- 深色/浅色主题（可扩展）

### 💬 实时聊天
- WebSocket 支持（实时双向通信）
- HTTP REST API（传统请求-响应）
- 消息历史记录
- 打字指示器
- 时间戳显示

### 📊 系统监控
- Canvas API 连接状态
- OpenAI API 连接状态
- Agent 就绪状态
- 实时更新（10秒间隔）

### 🚀 快速操作
- 预设常用查询
- 一键快速提问
- 示例查询展开
- 清空对话功能

---

## 快速开始

### 1. 环境准备

**系统要求：**
- Python 3.10+
- Node.js 16+
- npm 或 yarn

**检查版本：**
```bash
python --version   # 应该 >= 3.10
node --version     # 应该 >= 16.0
npm --version      # 应该 >= 8.0
```

### 2. 安装依赖

```bash
# 进入项目目录
cd agent_framework-main

# 安装 Python 依赖
pip install -r requirements.txt

# 进入前端目录
cd frontend

# 安装前端依赖
npm install

# 返回主目录
cd ..
```

### 3. 配置环境变量

创建 `.env` 文件（如果还没有）：

```bash
# 复制示例配置
cp env_example.txt .env

# 编辑 .env 文件
nano .env
```

必须配置：
```env
CANVAS_URL=https://your-institution.instructure.com
CANVAS_ACCESS_TOKEN=your_canvas_access_token
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
OPENAI_API_KEY=your_openai_api_key
```

### 4. 启动应用

**方式 A - 使用启动脚本（推荐）：**

Windows:
```bash
start_app.bat
```

Mac/Linux:
```bash
chmod +x start_app.sh
./start_app.sh
```

**方式 B - 使用 Python 脚本：**
```bash
python start_server.py
```

脚本会引导你：
1. 检查依赖
2. 验证配置
3. 选择是否启用 LocalTunnel
4. 配置端口
5. 启动服务

**方式 C - 手动启动（开发模式）：**

终端 1 - 后端:
```bash
python api_server.py
```

终端 2 - 前端:
```bash
cd frontend
npm start
```

终端 3 - LocalTunnel (可选):
```bash
npx localtunnel --port 8000
```

### 5. 访问应用

- **开发模式**: http://localhost:3000 (前端) + http://localhost:8000 (后端)
- **生产模式**: http://localhost:8000 (构建后的前端+后端)
- **公网访问**: LocalTunnel 提供的 URL

---

## 界面预览

### 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│  🎓 Canvas AI Agent        [Canvas] [OpenAI] [Agent]   │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  📚 Quick    │         💬 Chat Messages                 │
│   Actions    │                                          │
│              │  🤖: 您好！我可以帮你查询课程信息...     │
│  • 我的课程  │                                          │
│  • 本周作业  │  👤: 我有哪些课程？                      │
│  • 未提交    │                                          │
│              │  🤖: 您当前注册了 6 门课程：              │
│  💡 Examples │     1. CSE 4402 - Cryptography          │
│              │     2. CSE 5100 - Deep RL               │
│  🗑️ Clear    │     ...                                  │
│              │                                          │
│              ├──────────────────────────────────────────┤
│              │  [输入你的问题...]            [发送]     │
└──────────────┴──────────────────────────────────────────┘
```

### 组件说明

**1. 头部导航栏**
- Logo 和标题
- 系统状态指示器（实时更新）
  - 🟢 绿色：已连接
  - 🔴 红色：未连接
  - 🟡 黄色：连接中

**2. 侧边栏（左侧）**
- **快速操作**: 常用查询快捷按钮
- **示例查询**: 分类示例（可展开/收起）
  - 课程信息
  - 作业管理
  - 内容搜索
- **清空对话**: 重置聊天历史

**3. 聊天区域（中央）**
- **欢迎界面**: 首次访问显示欢迎消息
- **消息气泡**:
  - 用户消息：右侧，紫色渐变
  - Agent 消息：左侧，灰色背景
  - 错误消息：红色边框
  - 系统消息：蓝色边框
- **打字指示器**: Agent 回复时显示动画
- **时间戳**: 每条消息显示发送时间

**4. 输入区域（底部）**
- 文本输入框
- 发送按钮
- 状态提示（如 Agent 初始化中）

---

## 详细使用

### 基本对话

1. **发送消息**
   - 在输入框输入问题
   - 点击"发送"或按 Enter
   - 等待 Agent 响应

2. **查看历史**
   - 自动滚动到最新消息
   - 手动滚动查看历史记录

3. **快速查询**
   - 点击侧边栏快捷按钮
   - 问题自动填入输入框
   - 点击发送执行查询

### 高级功能

**1. 多轮对话**
```
你：我有哪些课程？
Agent：您有 6 门课程...

你：密码学课程的详情
Agent：CSE 4402 - Introduction to Cryptography...

你：这门课有什么作业？
Agent：该课程有 4 个作业...
```

**2. 复杂查询**
```
你：搜索所有课程中关于"二叉树"的内容

Agent：在 3 门课程中找到相关内容：
1. CSE 347 - 数据结构与算法
   - 第 5 讲：二叉搜索树
   - 作业 3：BST 实现
2. ...
```

**3. 文件操作**
```
你：下载算法课程的教学大纲

Agent：正在查找教学大纲...
找到文件：Syllabus_CSE347.pdf
已下载到：file_index/CSE347/Syllabus_CSE347.pdf
```

### 示例场景

**场景 1: 检查作业截止日期**
```
你：本周有哪些作业要交？

Agent：本周（10/21-10/27）有 3 个作业：

1. Assignment 3 - 算法分析
   课程：CSE 347
   截止：10/25 23:59
   状态：未提交
   
2. Homework 4 - 深度学习
   课程：CSE 5100
   截止：10/26 23:59
   状态：已提交
   
3. ...
```

**场景 2: 搜索学习材料**
```
你：在密码学课程中搜索 RSA 加密

Agent：在 Introduction to Cryptography 课程中找到 5 个相关内容：

📄 Lecture 8.pdf (第 12-18 页)
RSA (Rivest-Shamir-Adleman) 是一种非对称加密算法...
密钥生成：
1. 选择两个大质数 p 和 q
2. 计算 n = p × q
...

📄 Assignment 2.pdf
问题 3：实现 RSA 加密和解密...

...
```

**场景 3: 课程概览**
```
你：给我一个密码学课程的概览

Agent：CSE 4402 - Introduction to Cryptography

📚 课程信息：
- 学期：Fall 2025
- 教授：[Name]
- 学分：3

📝 作业情况：
- 总共：4 个作业
- 已完成：2 个
- 进行中：1 个
- 未开始：1 个

📅 重要日期：
- Assignment 3：10/25
- Assignment 4：10/30
- 期中考试：11/08

📊 成绩：
- Assignment 1: 95/100
- Assignment 2: 90/100
- 当前平均：92.5%
```

---

## LocalTunnel 配置

### 什么是 LocalTunnel？

LocalTunnel 允许你将本地运行的服务器暴露到互联网，无需配置路由器或防火墙。

### 基础使用

**启动 LocalTunnel：**

```bash
# 方式 1: 通过启动脚本
python start_server.py
# 选择 "Enable public access via localtunnel"

# 方式 2: 手动启动
npx localtunnel --port 8000
```

**输出示例：**
```
your url is: https://gentle-elephant-12.loca.lt
```

**访问你的应用：**
- 本地：http://localhost:8000
- 公网：https://gentle-elephant-12.loca.lt

### 高级配置

**1. 自定义子域名**（需要 LocalTunnel 订阅）
```bash
npx localtunnel --port 8000 --subdomain my-canvas-agent
# URL: https://my-canvas-agent.loca.lt
```

**2. 查看请求日志**
```bash
npx localtunnel --port 8000 --print-requests
```

**3. 使用自定义主机**
```bash
npx localtunnel --port 8000 --host https://custom.tunnel.com
```

### 安全建议

⚠️ **使用 LocalTunnel 时注意：**

1. **不要暴露敏感数据**
   - 不要在公网上使用生产数据库
   - 不要暴露管理员功能

2. **使用认证**
   ```python
   # 在 api_server.py 中添加认证
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @app.post("/api/chat")
   async def chat(request: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
       # 验证 token
       if credentials.credentials != "your-secret-token":
           raise HTTPException(status_code=401, detail="Unauthorized")
       # 处理请求
   ```

3. **限制速率**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.post("/api/chat")
   @limiter.limit("10/minute")
   async def chat(request: Request, chat_request: ChatRequest):
       # 处理请求
   ```

4. **监控访问日志**
   ```python
   @app.middleware("http")
   async def log_requests(request: Request, call_next):
       logger.info(f"Request: {request.method} {request.url}")
       response = await call_next(request)
       return response
   ```

### 替代方案

如果 LocalTunnel 不稳定，可以使用：

**1. ngrok** (推荐)
```bash
# 安装 ngrok
# 下载: https://ngrok.com/download

# 使用
ngrok http 8000
```

**2. serveo**
```bash
ssh -R 80:localhost:8000 serveo.net
```

**3. localhost.run**
```bash
ssh -R 80:localhost:8000 localhost.run
```

---

## 部署指南

### 本地部署（生产模式）

**1. 构建前端**
```bash
cd frontend
npm run build
cd ..
```

**2. 启动服务器**
```bash
python api_server.py
```

前端自动从 `frontend/build/` 目录提供服务。

访问: http://localhost:8000

### 云服务器部署

#### AWS EC2

**1. 创建实例**
- AMI: Ubuntu 22.04
- 实例类型: t3.small 或更高
- 安全组：开放 8000 端口

**2. 连接并配置**
```bash
# SSH 连接
ssh -i your-key.pem ubuntu@your-instance-ip

# 安装依赖
sudo apt update
sudo apt install -y python3-pip nodejs npm git

# 克隆项目
git clone https://github.com/Deyu-Zhang/canvas_ai.git
cd canvas_ai/agent_framework-main

# 安装 Python 依赖
pip3 install -r requirements.txt

# 构建前端
cd frontend
npm install
npm run build
cd ..

# 配置环境变量
nano .env
```

**3. 使用 systemd 管理**

创建 `/etc/systemd/system/canvas-agent.service`:
```ini
[Unit]
Description=Canvas AI Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/canvas_ai/agent_framework-main
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
ExecStart=/usr/bin/python3 api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl start canvas-agent
sudo systemctl enable canvas-agent
sudo systemctl status canvas-agent
```

**4. 配置 Nginx 反向代理**

安装 Nginx:
```bash
sudo apt install -y nginx
```

创建配置 `/etc/nginx/sites-available/canvas-agent`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/canvas-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. 配置 HTTPS (Let's Encrypt)**
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### Docker 部署

**1. 创建 Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Node.js
RUN apt-get update && apt-get install -y nodejs npm

# 复制文件
COPY requirements.txt .
COPY frontend/package*.json ./frontend/

# 安装依赖
RUN pip install -r requirements.txt
RUN cd frontend && npm install

# 复制源代码
COPY . .

# 构建前端
RUN cd frontend && npm run build

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "api_server.py"]
```

**2. 创建 docker-compose.yml**
```yaml
version: '3.8'

services:
  canvas-agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./file_index:/app/file_index
```

**3. 构建和运行**
```bash
docker-compose up -d
```

#### Vercel 部署（仅前端）

**1. 安装 Vercel CLI**
```bash
npm install -g vercel
```

**2. 部署前端**
```bash
cd frontend
vercel
```

**3. 配置环境变量**
在 Vercel Dashboard 中设置 `REACT_APP_API_URL`

---

## 维护与监控

### 日志管理

**查看日志：**
```bash
# 后端日志
tail -f logs/api_server.log

# Systemd 服务日志
sudo journalctl -u canvas-agent -f
```

### 性能监控

**使用 htop 监控资源：**
```bash
sudo apt install htop
htop
```

**监控 API 响应时间：**
```python
# 在 api_server.py 中添加
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request took {process_time:.2f}s")
    return response
```

### 备份

**备份配置和数据：**
```bash
# 创建备份
tar -czf backup_$(date +%Y%m%d).tar.gz \
    .env \
    file_index/ \
    frontend/build/

# 恢复备份
tar -xzf backup_20250115.tar.gz
```

---

## 总结

现在你已经拥有了一个功能完整的 Canvas AI Agent Web 前端！

**关键特性回顾：**
- ✅ 现代化聊天界面
- ✅ FastAPI 后端
- ✅ LocalTunnel 公网访问
- ✅ 完整的部署指南
- ✅ 生产级配置示例

**下一步建议：**
1. 自定义 UI 主题和样式
2. 添加用户认证系统
3. 实现对话历史持久化
4. 添加文件上传功能
5. 集成更多 Canvas API 功能

**获取帮助：**
- 📖 [完整文档](FRONTEND_README.md)
- 🚀 [快速开始](QUICKSTART.md)
- 🔧 [技术文档](TECHNICAL_DOCUMENTATION.md)

---

**Made with ❤️ for education**

