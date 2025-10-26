# 🚀 Canvas AI Agent - Quick Start Guide

## 5分钟快速启动

### 步骤 1: 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖（可选，如果需要开发前端）
cd frontend
npm install
cd ..
```

### 步骤 2: 配置环境

创建 `.env` 文件：

```env
CANVAS_URL=https://your-institution.instructure.com
CANVAS_ACCESS_TOKEN=your_canvas_token
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
OPENAI_API_KEY=your_openai_key
```

### 步骤 3: 启动服务

**Windows:**
```bash
start_app.bat
```

**Mac/Linux:**
```bash
chmod +x start_app.sh
./start_app.sh
```

**或手动启动:**
```bash
python start_server.py
```

### 步骤 4: 访问应用

打开浏览器访问:
- **本地**: http://localhost:8000
- **公网**: 选择 LocalTunnel 选项后会显示公网 URL

---

## 三种使用方式

### 方式 1: Web 界面（推荐） 🌐

```bash
python start_server.py
# 在浏览器中打开 http://localhost:8000
```

**功能：**
- 美观的聊天界面
- 实时状态显示
- 快速操作按钮
- 示例查询

### 方式 2: 命令行界面 💻

```bash
python canvas_chat.py
```

**功能：**
- 终端交互式对话
- 彩色输出
- 进度显示

### 方式 3: API 调用 🔧

```python
import requests

response = requests.post('http://localhost:8000/api/chat', json={
    "message": "我有哪些课程？"
})

print(response.json())
```

---

## 常用命令

### 下载所有课程文件

```bash
python file_index_downloader.py
```

### 下载特定课程

```bash
python file_index_downloader.py --course-id 154630
```

### 只上传到 Vector Store

```bash
python file_index_downloader.py --upload-only
```

### 启动开发服务器（前端）

```bash
cd frontend
npm start
```

### 构建生产版本（前端）

```bash
cd frontend
npm run build
```

---

## 示例查询

### 📚 课程信息
```
"我有哪些课程？"
"显示密码学课程的详情"
```

### 📝 作业管理
```
"本周有什么作业要交？"
"列出所有未提交的作业"
```

### 🔍 内容搜索
```
"搜索 RSA 加密的内容"
"查找关于二叉树的资料"
```

### 📁 文件管理
```
"列出算法课程的所有文件"
"下载密码学课程的教学大纲"
```

---

## LocalTunnel 公网访问

### 启用 LocalTunnel

运行 `python start_server.py`，选择 "Enable public access via localtunnel"

或手动启动：

```bash
# 终端 1: 启动服务器
python api_server.py

# 终端 2: 启动 tunnel
npx localtunnel --port 8000
```

### 输出示例

```
your url is: https://gentle-elephant-12.loca.lt
```

分享这个 URL 给其他人，他们就可以访问你的应用！

---

## 故障排除

### 问题：Agent 初始化失败

**检查：**
1. `.env` 文件是否存在
2. 所有 API keys 是否正确配置
3. 网络连接是否正常

```bash
# 验证配置
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Canvas:', os.getenv('CANVAS_URL'))"
```

### 问题：前端无法连接后端

**解决：**
1. 确认后端正在运行: http://localhost:8000/api/health
2. 清除浏览器缓存
3. 检查防火墙设置

### 问题：依赖安装失败

**解决：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 重新安装
pip install -r requirements.txt --force-reinstall
```

---

## 架构概览

```
┌──────────────┐
│   Browser    │ ← 用户界面
└──────┬───────┘
       │
       │ HTTP/WebSocket
       │
┌──────▼────────┐
│ FastAPI Server│ ← Python 后端
└──────┬────────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌─────┐  ┌──────┐
│Canvas│  │OpenAI│ ← 外部服务
└─────┘  └──────┘
```

---

## 下一步

✅ **完成基础设置后：**

1. 📥 [下载课程文件](FRONTEND_README.md#文件下载系统)
2. 🔍 [搜索课程内容](FRONTEND_README.md#内容搜索)
3. 🌐 [公网分享](FRONTEND_README.md#localtunnel-详细说明)
4. 📖 [阅读完整文档](FRONTEND_README.md)

---

## 需要帮助？

- 📖 [完整文档](FRONTEND_README.md)
- 🔧 [技术文档](TECHNICAL_DOCUMENTATION.md)
- 💬 [GitHub Issues](https://github.com/Deyu-Zhang/canvas_ai/issues)

---

**享受你的 Canvas AI Agent！** 🎓✨

