# Canvas AI Agent

An intelligent Canvas LMS assistant powered by Azure OpenAI, designed for students to efficiently manage their academic workflow.

## Features

- 🎓 **Student-Focused**: Tailored for student-level Canvas API access
- 🤖 **Intelligent Chat**: Natural language interaction powered by GPT-5
- 🛠️ **22+ API Tools**: Comprehensive Canvas functionality including courses, assignments, files, discussions
- 🌐 **Web Interface**: Modern React frontend with real-time chat
- 🔐 **Secure Configuration**: Environment variable management for sensitive data
- 📊 **File Indexing**: Automatic Canvas file synchronization with OpenAI Vector Store
- 👥 **Multi-User Support**: Independent agent instances for different users

## Canvas API Tools

### 📚 Course Management
- `canvas_list_courses` - List enrolled courses
- `canvas_get_modules` - Get course modules
- `canvas_get_module_items` - Get module content items

### 📝 Assignments & Submissions
- `canvas_get_assignments` - List assignments
- `canvas_submit_assignment` - Submit assignments

### 📁 File Management
- `canvas_get_files` - List course files
- `canvas_get_file_info` - Get file details
- `canvas_get_folders` - List folders
- `canvas_get_folder_files` - Get folder contents
- `canvas_search_files` - Search files

### 💬 Discussions & Announcements
- `canvas_get_discussions` - Get discussion topics
- `canvas_post_discussion` - Post discussion replies
- `canvas_get_announcements` - Get announcements

### 📖 Course Content
- `canvas_get_pages` - List course pages
- `canvas_get_page_content` - Get page content

### 📊 Grades & Calendar
- `canvas_get_grades` - Get grades
- `canvas_get_calendar_events` - Get calendar events
- `canvas_get_todo_items` - Get todo items
- `canvas_get_upcoming_events` - Get upcoming events

### 📝 Quizzes & Groups
- `canvas_get_quizzes` - List quizzes
- `canvas_get_groups` - List groups

### 🧠 Knowledge Base (Vector Store)
- `vector_store_list` - List knowledge bases
- `vector_store_search` - Search indexed content
- `vector_store_list_files` - List indexed files
- `vector_store_get_file` - Get file metadata

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Canvas LMS Configuration
CANVAS_URL=https://your-school.instructure.com
CANVAS_ACCESS_TOKEN=your-canvas-token-here

# OpenAI Configuration (for Vector Store)
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Web Application

```bash
# Start backend server and ngrok tunnel
python start_server.py
```

The application will be available at the ngrok URL provided in the terminal.

## Getting Canvas Access Token

1. Log into your Canvas account
2. Click **Account** in the left menu
3. Select **Settings**
4. Scroll to **Approved Integrations**
5. Click **+ New Access Token**
6. Fill in purpose description and expiration (optional)
7. Click **Generate Token**
8. **Copy the token immediately** (it won't be visible again)

## Usage Examples

### Web Interface

Access the web interface through the ngrok URL:

```
User: What courses do I have?
Agent: [Lists all enrolled courses]

User: Show me assignments for Data Structures
Agent: [Displays assignment list with due dates]

User: Search for PDF files in my courses
Agent: [Shows PDF files from all courses]

User: What's in the lecture notes from week 1?
Agent: [Searches Vector Store and provides relevant content]
```

### File Management

```
User: What files are in the Modules folder?
Agent: [Lists files in specified folder]

User: Search for files containing "midterm"
Agent: [Returns matching files across courses]

User: Get details for file 12345
Agent: [Shows file information and download link]
```

### Assignment Management

```
User: What are my pending assignments?
Agent: [Shows todo items and upcoming deadlines]

User: Submit assignment 1 with content...
Agent: [Submits assignment with provided content]

User: What's my current grade in CS101?
Agent: [Displays current grade information]
```

## File Indexing System

The system automatically synchronizes Canvas files with OpenAI Vector Store for intelligent content search:

- **Automatic Detection**: Scans for missing files on startup
- **Smart Upload**: Only uploads new/changed files
- **Multi-Format Support**: PDF, HTML, TXT, DOC, PPT, XLS, etc.
- **Course Organization**: Each course gets its own Vector Store
- **Status Monitoring**: Real-time indexing status in web interface

## Technical Architecture

- **Framework**: Custom Agent Framework
- **AI Model**: Azure OpenAI GPT-5
- **Frontend**: React + TypeScript
- **Backend**: FastAPI + Python
- **Async Processing**: aiohttp + asyncio
- **File Storage**: OpenAI Vector Store
- **Public Access**: ngrok tunneling
- **Configuration**: python-dotenv

## Project Structure

```
agent_framework-main/
├── src/
│   ├── agent/           # Agent core logic
│   ├── tools/           # Canvas API tools
│   ├── models/          # AI model management
│   ├── config/          # Configuration management
│   └── utils/           # Utility functions
├── configs/
│   └── canvas_agent_config.py  # Agent configuration
├── frontend/            # React web interface
│   ├── src/
│   └── build/
├── file_index/          # Downloaded Canvas files
├── api_server.py        # FastAPI backend
├── file_index_downloader.py  # File sync script
├── start_server.py      # Application launcher
├── requirements.txt     # Dependencies
└── .env                 # Environment variables
```

## Key Components

### Backend (`api_server.py`)
- FastAPI server with WebSocket support
- Multi-user session management
- Canvas API integration
- Vector Store synchronization
- File indexing status API

### Frontend (`frontend/`)
- React TypeScript application
- Real-time chat interface
- File indexing status bar
- Responsive design
- Session management

### File Downloader (`file_index_downloader.py`)
- Downloads Canvas course materials
- Handles files, modules, assignments, pages
- Uploads to OpenAI Vector Store
- Tracks inaccessible files (403 errors)
- Prevents duplicate uploads

## Important Notes

1. **Student Permissions**: All tools support student-level Canvas access only
2. **Token Security**: Never commit `.env` file to version control
3. **API Limits**: Respect Canvas API rate limits
4. **File Access**: Some files may require direct Canvas web access
5. **ngrok Domain**: Free ngrok requires domain claiming for stability

## Troubleshooting

### Q: How do I find my Canvas URL?
A: Use the domain from your Canvas login page, e.g., `https://canvas.university.edu`

### Q: What if my token expires?
A: Generate a new Access Token in Canvas settings and update your `.env` file

### Q: Why can't I download some files?
A: Some files have restricted permissions and require direct Canvas web access

### Q: Why is the frontend showing "no signal"?
A: This may be due to ngrok timeout limits. Consider upgrading to a paid ngrok plan for longer responses

### Q: How do I update the file index?
A: The system automatically detects missing files. Click "Start Sync" in the web interface to update

## License

This project is for educational use only.

## Contact

- GitHub: [@Deyu-Zhang](https://github.com/Deyu-Zhang)
- Email: zdy286004316@gmail.com