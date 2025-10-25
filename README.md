# Canvas Student Agent

一个基于 OpenAI 的 Canvas LMS 智能助手，专为学生设计。

## 功能特性

- 🎓 **学生权限**：专门针对学生级别的 Canvas API 访问权限
- 🤖 **智能对话**：基于 OpenAI GPT-4o 的自然语言交互
- 🛠️ **22+ API工具**：涵盖课程、作业、文件、讨论等核心功能
- 💬 **交互式控制台**：美观的命令行界面，支持实时对话
- 🔐 **安全配置**：使用环境变量管理敏感信息

## Canvas API 工具列表

### 📚 课程管理
- `canvas_list_courses` - 获取课程列表
- `canvas_get_modules` - 获取课程模块
- `canvas_get_module_items` - 获取模块内容项

### 📝 作业与提交
- `canvas_get_assignments` - 获取作业列表
- `canvas_submit_assignment` - 提交作业

### 📁 文件管理
- `canvas_get_files` - 获取文件列表
- `canvas_get_file_info` - 获取文件详细信息
- `canvas_download_file` - 下载文件
- `canvas_get_folders` - 获取文件夹列表
- `canvas_get_folder_files` - 获取文件夹内文件
- `canvas_search_files` - 搜索文件

### 💬 讨论与公告
- `canvas_get_discussions` - 获取讨论话题
- `canvas_post_discussion` - 发布讨论回复
- `canvas_get_announcements` - 获取公告

### 📖 课程内容
- `canvas_get_pages` - 获取页面列表
- `canvas_get_page_content` - 获取页面内容

### 📊 成绩与日程
- `canvas_get_grades` - 获取成绩
- `canvas_get_calendar_events` - 获取日历事件
- `canvas_get_todo_items` - 获取待办事项
- `canvas_get_upcoming_events` - 获取即将到来的事件

### 📝 测验与小组
- `canvas_get_quizzes` - 获取测验列表
- `canvas_get_groups` - 获取小组列表

## 快速开始

### 1. 环境配置

在项目根目录创建 `.env` 文件，并配置 OpenAI 模型：

```env
# OpenAI 官方 API
OPENAI_API_KEY=your-openai-api-key
# OPENAI_API_BASE=https://api.openai.com/v1           # 如需自定义基地址
# OPENAI_ORGANIZATION=org-id                           # 可选
# OPENAI_PROJECT=project-id                            # 可选

# Canvas LMS 配置
CANVAS_URL=https://your-school.instructure.com
CANVAS_ACCESS_TOKEN=your-canvas-token-here
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动交互式控制台

```bash
python canvas_chat.py
```

## 获取 Canvas Access Token

1. 登录您的 Canvas 账户
2. 点击左侧菜单的 **Account**（账户）
3. 选择 **Settings**（设置）
4. 滚动到页面底部，找到 **Approved Integrations**（已批准的集成）
5. 点击 **+ New Access Token**（新建访问令牌）
6. 填写用途说明，设置过期时间（可选）
7. 点击 **Generate Token**（生成令牌）
8. **立即复制令牌**（关闭窗口后将无法再次查看）

## 使用示例

### 方式 1: 交互式控制台

```bash
python canvas_chat.py
```

基础对话：
```
用户: 我有哪些课程？
助手: [列出所有课程]

用户: 帮我看看数据结构课程的作业
助手: [显示作业列表及截止日期]
```

文件操作：
```
用户: 搜索所有PDF文件
助手: [显示PDF文件列表]

用户: 下载文件 12345
助手: [下载并显示文件内容或链接]
```

作业管理：
```
用户: 我有什么待办事项？
助手: [显示待办事项列表]

用户: 提交作业1，内容是...
助手: [提交作业]
```

### 方式 2: 测试示例脚本

#### 使用 Agent 进行完整测试

```bash
# 交互式测试（推荐）
python examples/test_file_download.py

# 快速下载指定文件
python examples/test_file_download.py <file_id>
```

#### 直接测试 API 工具

```bash
# 交互式测试所有文件操作
python examples/direct_file_download_test.py

# 快速测试指定文件下载
python examples/direct_file_download_test.py <file_id>
```

**测试流程示例：**
1. 列出所有课程
2. 选择课程查看文件列表
3. 获取文件详细信息
4. 下载文件（支持文本、PDF、图片等多种格式）
5. 搜索特定关键词的文件

## 技术架构

- **框架**: 自定义 Agent Framework
- **AI 模型**: OpenAI GPT-4o / 其他兼容模型
- **异步处理**: aiohttp + asyncio
- **用户界面**: Rich (终端美化)
- **配置管理**: python-dotenv

## 项目结构

```
agent_framework-main/
├── src/
│   ├── agent/           # Agent 核心逻辑
│   ├── tools/           # Canvas API 工具集
│   ├── models/          # AI 模型管理
│   ├── config/          # 配置管理
│   └── utils/           # 工具函数
├── configs/
│   └── canvas_agent_config.py  # Agent 配置
├── canvas_chat.py       # 交互式控制台
├── requirements.txt     # 依赖包列表
└── .env                 # 环境变量（需自行创建）
```

## 注意事项

1. **权限限制**：所有工具仅支持学生权限操作
2. **Token 安全**：切勿将 `.env` 文件提交到版本控制
3. **API 限制**：注意 Canvas API 的速率限制
4. **文件下载**：某些文件可能因权限设置无法直接下载

## 常见问题

### Q: 如何找到我的 Canvas URL？
A: 您访问 Canvas 时浏览器地址栏中的域名，例如 `https://canvas.university.edu`

### Q: Token 过期了怎么办？
A: 重新在 Canvas 设置中生成新的 Access Token，并更新 `.env` 文件

### Q: 为什么无法下载某些文件？
A: 部分文件可能设置了特殊权限，需要在 Canvas 网页中直接访问

## 开源协议

本项目仅供学习使用。

## 联系方式

- GitHub: [@Deyu-Zhang](https://github.com/Deyu-Zhang)
- Email: zdy286004316@gmail.com

