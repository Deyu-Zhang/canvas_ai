# Canvas AI Agent - Web Frontend

## 概述

这是 Canvas AI Agent 的 Web 前端界面，提供了一个现代化、用户友好的聊天界面来与 Canvas LMS 进行交互。

## 功能特点

✨ **实时聊天界面** - 美观的聊天 UI，支持用户和 Agent 之间的对话
🔍 **智能搜索** - 语义搜索课程材料和资源
📚 **快速操作** - 预设的常用查询按钮
🌐 **公网访问** - 通过 LocalTunnel 实现外网访问
📊 **系统状态** - 实时显示 Canvas、OpenAI 和 Agent 连接状态
💬 **WebSocket 支持** - 实时消息传递（可选）

## 系统架构

```
┌─────────────────┐
│  React Frontend │ (Port 3000)
│  TypeScript + CSS│
└────────┬────────┘
         │
         │ HTTP/WebSocket
         │
┌────────▼────────┐
│  FastAPI Backend│ (Port 8000)
│  Python + Uvicorn│
└────────┬────────┘
         │
         │
┌────────▼────────┐     ┌──────────────┐
│  Canvas API     │     │ OpenAI API   │
│  (LMS Data)     │     │ (Vector Store)│
└─────────────────┘     └──────────────┘
```

## 快速开始

### 1. 安装依赖

**后端依赖:**
```bash
cd agent_framework-main
pip install -r requirements.txt
```

**前端依赖:**
```bash
cd frontend
npm install
```

### 2. 配置环境变量

确保 `.env` 文件已正确配置：

```env
# Canvas Configuration
CANVAS_URL=https://your-institution.instructure.com
CANVAS_ACCESS_TOKEN=your_canvas_token

# Azure OpenAI (for GPT-5)
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# OpenAI (for Vector Stores)
OPENAI_API_KEY=your_openai_key
```

### 3. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
cd agent_framework-main
python start_server.py
```

脚本会引导你完成：
- 依赖检查
- 环境变量验证
- 是否启用 LocalTunnel
- 端口配置

**方式二：手动启动**

终端 1 - 启动后端:
```bash
cd agent_framework-main
python api_server.py
```

终端 2 - 启动前端（开发模式）:
```bash
cd frontend
npm start
```

终端 3 - 启动 LocalTunnel（可选）:
```bash
npx localtunnel --port 8000
```

### 4. 访问应用

- **本地开发**: http://localhost:3000
- **生产环境**: http://localhost:8000
- **公网访问**: LocalTunnel 提供的 URL

## 详细配置

### 前端配置

**开发环境** (`frontend/.env.development`)
```env
REACT_APP_API_URL=http://localhost:8000
```

**生产环境** (`frontend/.env.production`)
```env
REACT_APP_API_URL=
```

### 后端配置

**端口设置**
```bash
# 默认 8000
PORT=8000 python api_server.py

# 或在 .env 中设置
PORT=8000
```

## 生产部署

### 1. 构建前端

```bash
cd frontend
npm run build
```

这将创建优化的生产版本在 `frontend/build/` 目录

### 2. 启动服务器

```bash
cd agent_framework-main
python api_server.py
```

后端会自动服务前端构建文件

### 3. 使用 LocalTunnel 公开访问

```bash
# 基本用法
npx localtunnel --port 8000

# 指定子域名（需要订阅）
npx localtunnel --port 8000 --subdomain my-canvas-agent
```

输出示例：
```
your url is: https://gentle-elephant-12.loca.lt
```

## API 端点

### RESTful API

**健康检查**
```http
GET /api/health
```

**系统状态**
```http
GET /api/status
```

**聊天（POST）**
```http
POST /api/chat
Content-Type: application/json

{
  "message": "我有哪些课程？",
  "session_id": "optional-session-id"
}
```

**获取工具列表**
```http
GET /api/tools
```

**获取示例查询**
```http
GET /api/examples
```

### WebSocket API

**连接**
```
ws://localhost:8000/ws/chat
```

**发送消息**
```json
{
  "message": "我有哪些课程？"
}
```

**接收响应**
```json
{
  "type": "response",
  "message": "您当前注册了 6 门课程...",
  "timestamp": "2025-01-15T10:30:00",
  "success": true
}
```

## 使用指南

### 界面组件

**1. 头部栏**
- Logo 和应用名称
- 实时系统状态指示器（Canvas, OpenAI, Agent）

**2. 侧边栏**
- 快速操作按钮
- 示例查询
- 清空对话按钮

**3. 聊天区域**
- 消息历史
- 实时输入提示
- 时间戳显示

**4. 输入区域**
- 文本输入框
- 发送按钮
- 状态提示

### 示例查询

**课程信息**
- "我有哪些课程？"
- "显示我的课程列表"
- "我这学期上什么课？"

**作业管理**
- "本周有什么作业要交？"
- "列出所有未提交的作业"
- "密码学课程的作业列表"

**内容搜索**
- "搜索 RSA 加密的内容"
- "查找关于二叉树的资料"
- "课程大纲里说了什么？"

**文件管理**
- "下载密码学课程的教学大纲"
- "列出算法课程的所有文件"
- "查看课程资料"

## LocalTunnel 详细说明

### 什么是 LocalTunnel？

LocalTunnel 是一个将本地服务器暴露到公网的工具，无需配置防火墙或路由器。

### 优点

✅ **免费使用** - 基础功能完全免费
✅ **快速设置** - 一条命令即可启动
✅ **无需配置** - 不需要修改路由器或防火墙
✅ **临时链接** - 适合演示和测试

### 限制

⚠️ **临时 URL** - 每次重启都会生成新 URL
⚠️ **速度限制** - 可能比直接访问慢
⚠️ **安全性** - 请勿在公网暴露敏感数据
⚠️ **稳定性** - 不适合生产环境

### 高级用法

**固定子域名** (需要订阅)
```bash
npx localtunnel --port 8000 --subdomain canvas-ai-agent
```

**查看请求日志**
```bash
npx localtunnel --port 8000 --print-requests
```

**自定义主机**
```bash
npx localtunnel --port 8000 --host https://custom.tunnel.com
```

## 故障排除

### 问题 1: 前端无法连接后端

**症状**: "Network Error" 或 "Failed to fetch"

**解决方案**:
1. 确认后端正在运行: `curl http://localhost:8000/api/health`
2. 检查前端代理配置: `frontend/package.json` 中的 `proxy` 字段
3. 清除浏览器缓存
4. 检查 CORS 配置

### 问题 2: Agent 初始化失败

**症状**: "Agent not initialized" 错误

**解决方案**:
1. 检查 `.env` 文件中的所有 API keys
2. 查看后端控制台的错误信息
3. 验证 Canvas 和 OpenAI 连接
4. 重启后端服务器

### 问题 3: LocalTunnel 连接失败

**症状**: Tunnel 无法启动或频繁断开

**解决方案**:
1. 更新 localtunnel: `npm install -g localtunnel`
2. 尝试不同的端口
3. 检查防火墙设置
4. 使用备选工具: ngrok, serveo

### 问题 4: 前端构建错误

**症状**: `npm run build` 失败

**解决方案**:
1. 删除 `node_modules` 和 `package-lock.json`
2. 重新安装: `npm install`
3. 更新 Node.js 到最新 LTS 版本
4. 检查 TypeScript 错误

### 问题 5: 样式显示异常

**症状**: 界面布局混乱

**解决方案**:
1. 清除浏览器缓存
2. 强制刷新: Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)
3. 检查 CSS 文件是否正确加载
4. 确认浏览器兼容性

## 开发指南

### 项目结构

```
agent_framework-main/
├── frontend/                    # React 前端
│   ├── public/                 # 静态资源
│   ├── src/
│   │   ├── App.tsx            # 主组件
│   │   ├── App.css            # 样式
│   │   └── index.tsx          # 入口
│   ├── package.json           # 前端依赖
│   └── tsconfig.json          # TypeScript 配置
│
├── api_server.py              # FastAPI 后端
├── start_server.py            # 启动脚本
├── requirements.txt           # 后端依赖
└── .env                       # 环境变量
```

### 添加新功能

**1. 添加新的 API 端点**

在 `api_server.py` 中:
```python
@app.get("/api/my-endpoint")
async def my_endpoint():
    return {"data": "value"}
```

**2. 添加新的前端组件**

在 `frontend/src/` 中创建新组件:
```typescript
// MyComponent.tsx
import React from 'react';

const MyComponent: React.FC = () => {
  return <div>My Component</div>;
};

export default MyComponent;
```

**3. 调用新 API**

在组件中:
```typescript
const fetchData = async () => {
  const response = await fetch('/api/my-endpoint');
  const data = await response.json();
  console.log(data);
};
```

### 测试

**前端测试**
```bash
cd frontend
npm test
```

**后端测试**
```bash
cd agent_framework-main
pytest
```

**集成测试**
```bash
# 启动服务器
python start_server.py

# 在浏览器中访问
open http://localhost:8000
```

## 性能优化

### 前端优化

1. **代码分割**: React.lazy 和 Suspense
2. **缓存**: Service Worker
3. **压缩**: 生产构建自动处理
4. **CDN**: 部署静态资源到 CDN

### 后端优化

1. **异步处理**: 所有 I/O 操作使用 async/await
2. **连接池**: 复用 API 连接
3. **缓存**: Redis 缓存常用数据
4. **负载均衡**: 多实例部署

## 安全建议

⚠️ **重要**：在生产环境中：

1. **HTTPS**: 使用 HTTPS 加密传输
2. **认证**: 添加用户认证系统
3. **CORS**: 限制允许的域名
4. **速率限制**: 防止 API 滥用
5. **环境变量**: 不要提交 `.env` 文件
6. **Token 管理**: 定期轮换 API tokens
7. **日志**: 记录所有 API 访问

## 部署选项

### 选项 1: Vercel (推荐用于前端)

```bash
cd frontend
npm install -g vercel
vercel
```

### 选项 2: Heroku (全栈)

```bash
# 安装 Heroku CLI
heroku create my-canvas-agent
git push heroku main
```

### 选项 3: Docker

创建 `Dockerfile`:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

构建和运行:
```bash
docker build -t canvas-agent .
docker run -p 8000:8000 canvas-agent
```

### 选项 4: 云服务器 (AWS, GCP, Azure)

1. 创建虚拟机
2. 安装 Python 和 Node.js
3. 克隆项目
4. 配置环境变量
5. 使用 systemd 或 PM2 管理进程
6. 配置 Nginx 反向代理

## 更新日志

### v1.0.0 (2025-01-15)
- ✨ 初始版本发布
- 🎨 现代化聊天界面
- 🚀 FastAPI 后端
- 🌐 LocalTunnel 集成
- 📱 响应式设计
- 💬 WebSocket 支持

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/my-feature`
3. 提交更改: `git commit -am 'Add my feature'`
4. 推送分支: `git push origin feature/my-feature`
5. 提交 Pull Request

## 许可证

本项目为教育用途开发。

## 联系方式

- **Developer**: Deyu Zhang
- **Repository**: https://github.com/Deyu-Zhang/canvas_ai
- **Institution**: Washington University in St. Louis

---

**Made with ❤️ for students**

