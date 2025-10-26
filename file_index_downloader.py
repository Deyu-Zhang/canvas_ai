"""
Canvas 完整文件索引下载器

自动下载所有课程的所有文件，按课程和模块组织文件夹结构
并上传到 OpenAI Vector Store
"""

import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
import json
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

try:
    from openai import OpenAI
    import openai
    OPENAI_VERSION = openai.__version__
except ImportError:
    OpenAI = None
    OPENAI_VERSION = None

# 加载环境变量
load_dotenv()

console = Console()

# 下载根目录 - 保存到项目根目录的 file_index 文件夹
# 脚本在 agent_framework-main/ 下，需要向上一级到项目根目录
DOWNLOAD_ROOT = Path(__file__).parent.parent / "file_index"

# 下载统计
stats = {
    "courses": 0,
    "modules": 0,
    "files_total": 0,
    "files_downloaded": 0,
    "files_skipped": 0,
    "files_failed": 0,
    "files_inaccessible": 0,
    "total_size": 0,
    "vector_stores_created": 0,
    "vector_stores_reused": 0,
    "files_uploaded_to_vector_store": 0,
    "files_upload_skipped": 0,
    "files_upload_failed": 0,
    "inaccessible_files": [],  # 记录无法访问的文件
    "errors": []
}

# Vector Store 配置
SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.json', '.csv'}
MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB (OpenAI limit)


def sanitize_filename(name: str) -> str:
    """清理文件名/文件夹名，移除非法字符"""
    # Windows不允许的字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        name = name.replace(char, '_')
    # 移除前后空格和点
    name = name.strip('. ')
    # 限制长度
    if len(name) > 200:
        name = name[:200]
    return name or "unnamed"


async def fetch_all_pages(session, url, headers, params=None):
    """获取所有分页数据"""
    all_data = []
    current_url = url
    
    while current_url:
        try:
            async with session.get(current_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
                    
                    # 检查是否有下一页
                    link_header = response.headers.get('Link', '')
                    current_url = None
                    if link_header:
                        for link in link_header.split(','):
                            if 'rel="next"' in link:
                                current_url = link[link.find('<')+1:link.find('>')]
                                break
                    params = None  # 后续请求不需要params
                else:
                    console.print(f"⚠️  请求失败 ({response.status}): {current_url}", style="yellow")
                    break
                    
        except Exception as e:
            console.print(f"❌ 请求异常: {e}", style="red")
            break
    
    return all_data


async def download_file(session, file_info, file_path, course_name=""):
    """下载单个文件"""
    file_url = file_info.get('url')
    file_name = file_info.get('display_name', 'unnamed')
    file_size = file_info.get('size', 0)
    file_id = file_info.get('id', '')
    
    if not file_url:
        return False, "无下载链接"
    
    # 如果文件已存在且大小匹配，跳过
    if file_path.exists() and file_path.stat().st_size == file_size:
        stats["files_skipped"] += 1
        return True, "已存在"
    
    try:
        async with session.get(file_url) as response:
            if response.status == 200:
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 下载文件
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                stats["files_downloaded"] += 1
                stats["total_size"] += file_size
                return True, "成功"
            elif response.status == 403:
                # 记录无法访问的文件
                stats["files_inaccessible"] += 1
                stats["inaccessible_files"].append({
                    "course": course_name,
                    "file_name": file_name,
                    "file_id": file_id,
                    "error": "403 Forbidden"
                })
                return False, "403 Forbidden (无权访问)"
            else:
                return False, f"HTTP {response.status}"
                
    except Exception as e:
        return False, str(e)


async def get_courses(session, canvas_url, headers):
    """获取所有课程"""
    console.print("\n📚 获取课程列表...", style="cyan bold")
    
    courses = await fetch_all_pages(
        session,
        f"{canvas_url}/api/v1/courses",
        headers,
        params={"enrollment_state": "active", "per_page": 100}
    )
    
    console.print(f"✓ 找到 {len(courses)} 个课程\n", style="green")
    return courses


async def get_course_modules(session, canvas_url, headers, course_id):
    """获取课程的所有模块"""
    modules = await fetch_all_pages(
        session,
        f"{canvas_url}/api/v1/courses/{course_id}/modules",
        headers,
        params={"include[]": "items", "per_page": 100}
    )
    return modules


async def get_module_items(session, canvas_url, headers, course_id, module_id):
    """获取模块的所有项目"""
    items = await fetch_all_pages(
        session,
        f"{canvas_url}/api/v1/courses/{course_id}/modules/{module_id}/items",
        headers,
        params={"per_page": 100}
    )
    return items


async def get_course_files(session, canvas_url, headers, course_id):
    """获取课程的所有文件（Files区域）"""
    try:
        # 尝试直接获取文件列表
        async with session.get(
            f"{canvas_url}/api/v1/courses/{course_id}/files",
            headers=headers,
            params={"per_page": 1}
        ) as response:
            if response.status == 403:
                # 403 Forbidden - 记录并返回空列表
                return None  # 返回 None 表示无权访问
            elif response.status != 200:
                return []
        
        files = await fetch_all_pages(
            session,
            f"{canvas_url}/api/v1/courses/{course_id}/files",
            headers,
            params={"per_page": 100}
        )
        return files
    except:
        # 如果直接获取失败，尝试通过文件夹方式
        try:
            folders = await fetch_all_pages(
                session,
                f"{canvas_url}/api/v1/courses/{course_id}/folders",
                headers,
                params={"per_page": 100}
            )
            
            all_files = []
            for folder in folders:
                folder_files = await fetch_all_pages(
                    session,
                    f"{canvas_url}/api/v1/folders/{folder['id']}/files",
                    headers,
                    params={"per_page": 100}
                )
                all_files.extend(folder_files)
            
            return all_files
        except:
            return []


async def get_file_info(session, canvas_url, headers, file_id):
    """获取文件详细信息"""
    try:
        async with session.get(
            f"{canvas_url}/api/v1/files/{file_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None


async def get_page_content(session, canvas_url, headers, course_id, page_url):
    """获取页面内容"""
    try:
        async with session.get(
            f"{canvas_url}/api/v1/courses/{course_id}/pages/{page_url}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None


async def get_assignment_details(session, canvas_url, headers, course_id, assignment_id):
    """获取作业详细信息"""
    try:
        async with session.get(
            f"{canvas_url}/api/v1/courses/{course_id}/assignments/{assignment_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None


def extract_files_from_html(html_content):
    """从HTML内容中提取文件链接"""
    import re
    if not html_content:
        return []
    
    # 匹配 Canvas 文件链接
    # 格式: /files/{file_id}/download 或 /courses/{course_id}/files/{file_id}
    pattern = r'/files/(\d+)(?:/download)?'
    matches = re.findall(pattern, html_content)
    
    return list(set(matches))  # 去重


def can_upload_to_vector_store(file_path: Path) -> bool:
    """检查文件是否可以上传到 Vector Store"""
    # 检查扩展名
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False
    
    # 检查文件大小
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False
    except:
        return False
    
    return True


def upload_to_vector_store(client, vector_store_id, file_path, course_name):
    """上传文件到 Vector Store"""
    try:
        with open(file_path, 'rb') as f:
            file_response = client.files.create(
                file=f,
                purpose='assistants'
            )
        
        # 将文件添加到 Vector Store（不是 beta API）
        client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_response.id
        )
        
        stats["files_uploaded_to_vector_store"] += 1
        return True, file_response.id
        
    except Exception as e:
        stats["files_upload_failed"] += 1
        stats["errors"].append({
            "course": course_name,
            "file": file_path.name,
            "error": f"Vector Store上传失败: {str(e)}"
        })
        return False, str(e)


def create_vector_store_for_course(client, course_name, course_code):
    """为课程创建 Vector Store"""
    try:
        vector_store_name = f"{course_code}_{course_name}" if course_code else course_name
        
        # 使用正确的 API 路径（不是 beta）
        vector_store = client.vector_stores.create(
            name=vector_store_name[:100]  # 限制长度
        )
        
        stats["vector_stores_created"] += 1
        return vector_store.id
        
    except AttributeError as e:
        console.print(f"❌ Vector Stores API 不可用: {e}", style="red")
        console.print("   请更新 OpenAI 库: pip install --upgrade openai", style="yellow")
        return None
    except Exception as e:
        console.print(f"❌ 创建 Vector Store 失败: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="red dim")
        return None


async def process_course(session, canvas_url, headers, course, progress, task_id):
    """处理单个课程"""
    course_id = course['id']
    course_name = sanitize_filename(course.get('name', f'Course_{course_id}'))
    course_code = course.get('course_code', '')
    
    # 创建课程文件夹
    course_path = DOWNLOAD_ROOT / f"{course_code}_{course_name}" if course_code else DOWNLOAD_ROOT / course_name
    course_path.mkdir(parents=True, exist_ok=True)
    
    progress.update(task_id, description=f"[cyan]处理课程: {course_name}")
    
    course_stats = {
        "modules": 0,
        "files_from_modules": 0,
        "files_from_files": 0,
        "files_downloaded": 0,
        "files_failed": 0
    }
    
    # ================================================
    # 1. 处理 Modules 中的文件
    # ================================================
    modules = await get_course_modules(session, canvas_url, headers, course_id)
    
    for module in modules:
        module_name = sanitize_filename(module.get('name', f'Module_{module["id"]}'))
        module_path = course_path / "Modules" / module_name
        
        course_stats["modules"] += 1
        
        # 获取模块项目
        items = module.get('items', [])
        if not items:
            items = await get_module_items(session, canvas_url, headers, course_id, module['id'])
        
        # 处理模块中的各种类型项目
        for item in items:
            item_type = item.get('type')
            item_title = item.get('title', 'unnamed')
            
            # 1. 处理 File 类型
            if item_type == 'File':
                file_id = item.get('content_id')
                if file_id:
                    file_info = await get_file_info(session, canvas_url, headers, file_id)
                    if file_info:
                        file_name = sanitize_filename(file_info.get('display_name', 'unnamed'))
                        file_path = module_path / file_name
                        
                        success, msg = await download_file(session, file_info, file_path, course_name)
                        
                        if success:
                            course_stats["files_from_modules"] += 1
                            course_stats["files_downloaded"] += 1
                        else:
                            course_stats["files_failed"] += 1
                            stats["errors"].append({
                                "course": course_name,
                                "module": module_name,
                                "file": file_name,
                                "error": msg
                            })
                    else:
                        stats["errors"].append({
                            "course": course_name,
                            "module": module_name,
                            "file": f"File ID {file_id}",
                            "error": "无法获取文件信息（可能无权限）"
                        })
            
            # 2. 处理 Page 类型（课程页面可能包含附件）
            elif item_type == 'Page':
                page_url = item.get('page_url')
                if page_url:
                    page_content = await get_page_content(session, canvas_url, headers, course_id, page_url)
                    if page_content:
                        # 保存页面 HTML 内容
                        html_content = page_content.get('body', '')
                        if html_content:
                            page_file_name = sanitize_filename(f"{item_title}.html")
                            page_file_path = module_path / page_file_name
                            page_file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(page_file_path, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            
                            course_stats["files_from_modules"] += 1
                            course_stats["files_downloaded"] += 1
                            stats["files_downloaded"] += 1
                        
                        # 提取页面中的文件链接并下载
                        file_ids = extract_files_from_html(html_content)
                        for file_id in file_ids:
                            file_info = await get_file_info(session, canvas_url, headers, file_id)
                            if file_info:
                                file_name = sanitize_filename(file_info.get('display_name', 'unnamed'))
                                file_path = module_path / file_name
                                
                                success, msg = await download_file(session, file_info, file_path, course_name)
                                if success:
                                    course_stats["files_from_modules"] += 1
                                    course_stats["files_downloaded"] += 1
            
            # 3. 处理 Assignment 类型（作业可能有附件）
            elif item_type == 'Assignment':
                assignment_id = item.get('content_id')
                if assignment_id:
                    assignment_details = await get_assignment_details(
                        session, canvas_url, headers, course_id, assignment_id
                    )
                    if assignment_details:
                        # 保存作业描述为 HTML
                        description = assignment_details.get('description', '')
                        if description:
                            assignment_file_name = sanitize_filename(f"{item_title}_description.html")
                            assignment_file_path = module_path / assignment_file_name
                            assignment_file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(assignment_file_path, 'w', encoding='utf-8') as f:
                                f.write(description)
                            
                            course_stats["files_from_modules"] += 1
                            course_stats["files_downloaded"] += 1
                            stats["files_downloaded"] += 1
                        
                        # 处理作业的附件（attachments字段）
                        attachments = assignment_details.get('attachments', [])
                        for attachment in attachments:
                            # 附件就是一个文件对象
                            file_name = sanitize_filename(attachment.get('display_name', attachment.get('filename', 'unnamed')))
                            file_path = module_path / file_name
                            
                            success, msg = await download_file(session, attachment, file_path, course_name)
                            if success:
                                course_stats["files_from_modules"] += 1
                                course_stats["files_downloaded"] += 1
                            else:
                                course_stats["files_failed"] += 1
                                stats["errors"].append({
                                    "course": course_name,
                                    "module": module_name,
                                    "file": file_name,
                                    "error": f"附件下载失败: {msg}"
                                })
                        
                        # 提取描述中的文件链接
                        file_ids = extract_files_from_html(description)
                        for file_id in file_ids:
                            file_info = await get_file_info(session, canvas_url, headers, file_id)
                            if file_info:
                                file_name = sanitize_filename(file_info.get('display_name', 'unnamed'))
                                file_path = module_path / file_name
                                
                                success, msg = await download_file(session, file_info, file_path, course_name)
                                if success:
                                    course_stats["files_from_modules"] += 1
                                    course_stats["files_downloaded"] += 1
    
    # ================================================
    # 2. 处理 Files 区域的文件
    # ================================================
    files = await get_course_files(session, canvas_url, headers, course_id)
    
    # 如果返回 None，表示整个课程无权访问（极少见）
    if files is None:
        console.print(f"⚠️  课程 '{course_name}' (ID: {course_id}) 无权访问 (403 Forbidden)", style="yellow")
        return course_stats
    
    for file_info in files:
        file_name = sanitize_filename(file_info.get('display_name', 'unnamed'))
        # 将Files区域的文件放在单独的文件夹中
        file_path = course_path / "Files" / file_name
        
        success, msg = await download_file(session, file_info, file_path, course_name)
        
        if success:
            course_stats["files_from_files"] += 1
            course_stats["files_downloaded"] += 1
        else:
            course_stats["files_failed"] += 1
            stats["errors"].append({
                "course": course_name,
                "file": file_name,
                "error": msg
            })
    
    stats["courses"] += 1
    stats["modules"] += course_stats["modules"]
    stats["files_total"] += course_stats["files_from_modules"] + course_stats["files_from_files"]
    stats["files_failed"] += course_stats["files_failed"]
    
    return course_stats


async def main(skip_download=False, course_id=None, auto_confirm=False):
    """主函数
    
    Args:
        skip_download: 如果为True，跳过下载直接上传已有文件到Vector Store
        course_id: 如果指定，只下载该课程ID的文件
        auto_confirm: 如果为True，自动确认下载，不询问用户
    """
    
    # 打印欢迎信息
    console.print("\n" + "="*70, style="cyan bold")
    if skip_download:
        console.print("☁️  Canvas 文件上传到 Vector Store", style="cyan bold")
    else:
        console.print("📦 Canvas 完整文件索引下载器 + Vector Store 上传", style="cyan bold")
    console.print("="*70 + "\n", style="cyan bold")
    
    # 检查环境变量
    canvas_url = os.getenv("CANVAS_URL")
    canvas_token = os.getenv("CANVAS_ACCESS_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not canvas_url or not canvas_token:
        console.print("❌ 错误：未找到 Canvas 配置", style="red bold")
        console.print("请确保 .env 文件包含：", style="yellow")
        console.print("  - CANVAS_URL", style="yellow")
        console.print("  - CANVAS_ACCESS_TOKEN", style="yellow")
        return
    
    console.print(f"✓ Canvas URL: {canvas_url}", style="green")
    console.print(f"✓ Canvas Token 已配置", style="green")
    console.print(f"✓ 下载目录: {DOWNLOAD_ROOT.absolute()}", style="green")
    
    # 检查 OpenAI 配置
    upload_to_openai = False
    openai_client = None
    
    if openai_api_key:
        if OpenAI is None:
            console.print("⚠️  openai 库未安装，将跳过 Vector Store 上传", style="yellow")
            console.print("   安装命令: pip install 'openai>=1.20.0'", style="dim")
        else:
            try:
                # 显示当前版本
                if OPENAI_VERSION:
                    console.print(f"✓ OpenAI 库版本: {OPENAI_VERSION}", style="green")
                
                # 创建 OpenAI 客户端（需要 assistants=v2 beta header）
                openai_client = OpenAI(
                    api_key=openai_api_key,
                    default_headers={"OpenAI-Beta": "assistants=v2"}
                )
                
                console.print(f"✓ OpenAI API 已配置", style="green")
                
                # 尝试验证 Vector Stores API（通过实际调用测试）
                try:
                    # 测试是否可以访问 vector_stores API（不是 beta！）
                    test_list = openai_client.vector_stores.list(limit=1)
                    console.print(f"✓ Vector Stores API 可用", style="green")
                    upload_to_openai = True
                except AttributeError as ae:
                    console.print("❌ Vector Stores API 不可用 (API 结构问题)", style="red")
                    console.print(f"   错误: {ae}", style="yellow")
                    console.print("   请确认 OpenAI 库版本 >= 1.20.0", style="yellow")
                    openai_client = None
                except Exception as ve:
                    # API 调用失败但结构存在，可能是权限或其他问题
                    console.print(f"⚠️  Vector Stores API 测试失败: {ve}", style="yellow")
                    console.print("   将尝试继续使用（可能在实际上传时工作）", style="dim")
                    upload_to_openai = True
                    
            except Exception as e:
                console.print(f"⚠️  OpenAI 初始化失败: {e}", style="yellow")
                import traceback
                console.print(traceback.format_exc()[:500], style="red dim")
    else:
        console.print("⚠️  未配置 OpenAI API Key，将跳过 Vector Store 上传", style="yellow")
        console.print("   需要配置: OPENAI_API_KEY", style="dim")
    
    console.print()
    
    # 创建下载目录
    DOWNLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    
    # 如果只上传，检查文件夹是否存在
    if skip_download:
        if not DOWNLOAD_ROOT.exists() or not any(DOWNLOAD_ROOT.iterdir()):
            console.print("❌ 错误：file_index 文件夹不存在或为空", style="red bold")
            console.print(f"请先运行下载命令或确保文件已存在于: {DOWNLOAD_ROOT.absolute()}", style="yellow")
            return
        
        console.print(f"✓ 找到下载文件夹: {DOWNLOAD_ROOT.absolute()}", style="green")
    
    start_time = datetime.now()
    
    # ================================================
    # 下载部分（可选）
    # ================================================
    if not skip_download:
        headers = {
            "Authorization": f"Bearer {canvas_token}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # 获取所有课程
            all_courses = await get_courses(session, canvas_url, headers)
            
            if not all_courses:
                console.print("⚠️  未找到任何课程", style="yellow")
                return
            
            # 如果指定了课程ID，只处理该课程
            if course_id:
                courses = [c for c in all_courses if str(c['id']) == str(course_id)]
                if not courses:
                    console.print(f"❌ 未找到课程ID: {course_id}", style="red bold")
                    console.print("\n可用的课程:", style="yellow")
                    for i, course in enumerate(all_courses, 1):
                        console.print(f"  {i}. {course.get('name', 'N/A')} (ID: {course['id']})", style="dim")
                    return
                console.print(f"✓ 找到指定课程: {courses[0].get('name', 'N/A')} (ID: {course_id})", style="green bold")
            else:
                courses = all_courses
                # 显示课程列表
                console.print("📋 课程列表:", style="cyan bold")
                for i, course in enumerate(courses, 1):
                    console.print(f"  {i}. {course.get('name', 'N/A')} (ID: {course['id']})", style="dim")
                console.print()
                
                # 询问是否继续（除非是自动确认模式）
                if not auto_confirm:
                    console.print(f"将下载 {len(courses)} 个课程的所有文件", style="yellow bold")
                    response = console.input("是否继续? (y/n): ")
                    
                    if response.lower() != 'y':
                        console.print("已取消", style="yellow")
                        return
                else:
                    console.print(f"自动模式：检查 {len(courses)} 个课程的文件（只下载缺失的文件）", style="green bold")
            
            console.print()
            
            # 开始下载
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                main_task = progress.add_task(
                    "[cyan]总体进度",
                    total=len(courses)
                )
                
                for course in courses:
                    course_stats = await process_course(
                        session, canvas_url, headers, course, progress, main_task
                    )
                    
                    progress.update(main_task, advance=1)
    else:
        console.print("⏩ 跳过下载，直接处理已有文件\n", style="yellow")
    
    # ================================================
    # 上传到 OpenAI Vector Store
    # ================================================
    if upload_to_openai and openai_client:
        console.print("\n" + "="*70, style="magenta bold")
        console.print("☁️  上传文件到 OpenAI Vector Store", style="magenta bold")
        console.print("="*70 + "\n", style="magenta bold")
        
        # 读取现有的 vector_stores_mapping.json，获取已上传的文件
        existing_mapping = {}
        mapping_file = DOWNLOAD_ROOT / "vector_stores_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing_mapping = json.load(f)
        
        # 获取所有已下载的文件并按课程组织
        course_files = {}
        
        for course_folder in DOWNLOAD_ROOT.iterdir():
            if course_folder.is_dir() and not course_folder.name.startswith('.'):
                course_name = course_folder.name
                files_to_upload = []
                
                # 获取该课程已上传的文件路径（标准化路径分隔符）
                uploaded_files = set()
                if course_name in existing_mapping:
                    for file_info in existing_mapping[course_name].get('files', []):
                        file_path_in_mapping = file_info.get('path', '')
                        # 标准化路径分隔符为正斜杠进行比较
                        normalized_path = file_path_in_mapping.replace('\\', '/')
                        uploaded_files.add(normalized_path)
                
                # 收集所有可上传的文件（跳过已上传的）
                for file_path in course_folder.rglob('*'):
                    if file_path.is_file() and can_upload_to_vector_store(file_path):
                        # 计算相对路径并标准化为正斜杠
                        relative_path = str(file_path.relative_to(DOWNLOAD_ROOT)).replace('\\', '/')
                        # 如果文件还没上传，添加到列表
                        if relative_path not in uploaded_files:
                            files_to_upload.append(file_path)
                        else:
                            stats["files_upload_skipped"] += 1
                
                if files_to_upload:
                    course_files[course_name] = files_to_upload
        
        total_new_files = sum(len(files) for files in course_files.values())
        
        if total_new_files > 0:
            console.print(f"找到 {len(course_files)} 个课程，共 {total_new_files} 个新文件需要上传\n", style="green")
        else:
            console.print("✓ 所有文件都已上传到 Vector Store\n", style="green")
        
        if course_files:
            
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                upload_task = progress.add_task(
                    "[magenta]上传到 Vector Store",
                    total=len(course_files)
                )
                
                # 保存 Vector Store 信息
                vector_stores_info = {}
                
                for course_name, files in course_files.items():
                    progress.update(upload_task, description=f"[magenta]处理: {course_name[:40]}")
                    
                    # 检查是否已经有 Vector Store，如果有就使用现有的
                    if course_name in existing_mapping and 'vector_store_id' in existing_mapping[course_name]:
                        vector_store_id = existing_mapping[course_name]['vector_store_id']
                        console.print(f"  使用现有 Vector Store: {vector_store_id}", style="dim")
                        stats["vector_stores_reused"] += 1
                        
                        # 保留现有的文件列表
                        vector_stores_info[course_name] = {
                            "vector_store_id": vector_store_id,
                            "files": existing_mapping[course_name].get('files', [])
                        }
                    else:
                        # 为每个课程创建一个新的 Vector Store
                        vector_store_id = create_vector_store_for_course(openai_client, course_name, "")
                        
                        if vector_store_id:
                            vector_stores_info[course_name] = {
                                "vector_store_id": vector_store_id,
                                "files": []
                            }
                        else:
                            vector_store_id = None
                    
                    if vector_store_id:
                        # 上传新文件
                        for file_path in files:
                            success, file_id = upload_to_vector_store(
                                openai_client,
                                vector_store_id,
                                file_path,
                                course_name
                            )
                            
                            if success:
                                vector_stores_info[course_name]["files"].append({
                                    "path": str(file_path.relative_to(DOWNLOAD_ROOT)),
                                    "file_id": file_id
                                })
                            
                            # 避免速率限制
                            await asyncio.sleep(0.1)
                    
                    progress.update(upload_task, advance=1)
                
                # 合并现有的mapping（保留没有新文件上传的课程）
                for course_name, course_data in existing_mapping.items():
                    if course_name not in vector_stores_info:
                        vector_stores_info[course_name] = course_data
                
                # 保存 Vector Store 映射
                vector_store_mapping_path = DOWNLOAD_ROOT / "vector_stores_mapping.json"
                with open(vector_store_mapping_path, 'w', encoding='utf-8') as f:
                    json.dump(vector_stores_info, f, indent=2, ensure_ascii=False)
                
                console.print(f"\n✓ Vector Store 映射已保存: {vector_store_mapping_path}", style="green")
        elif existing_mapping:
            console.print("✓ 没有新文件需要上传，保持现有 Vector Store 配置", style="green")
        else:
            console.print("⚠️  没有找到可上传到 Vector Store 的文件", style="yellow")
    
    # 完成
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    console.print("\n" + "="*70, style="green bold")
    console.print("✅ 同步完成！", style="green bold")
    console.print("="*70 + "\n", style="green bold")
    
    # 显示实际操作的文件数
    actual_downloaded = stats["files_downloaded"]
    actual_skipped = stats["files_skipped"]
    console.print(f"📊 实际新下载: {actual_downloaded} 个文件", style="cyan")
    console.print(f"📊 跳过已存在: {actual_skipped} 个文件", style="dim")
    
    # 统计表格
    table = Table(title="下载与上传统计", show_header=True)
    table.add_column("项目", style="cyan", width=30)
    table.add_column("数量", style="green", justify="right", width=15)
    
    table.add_row("━━━━ 下载统计 ━━━━", "", style="bold cyan")
    table.add_row("课程总数", str(stats["courses"]))
    table.add_row("模块总数", str(stats["modules"]))
    table.add_row("文件总数", str(stats["files_total"]))
    table.add_row("成功下载", str(stats["files_downloaded"]))
    table.add_row("已跳过（已存在）", str(stats["files_skipped"]))
    table.add_row("下载失败", str(stats["files_failed"]))
    if stats["files_inaccessible"] > 0:
        table.add_row("无法访问（403）", str(stats["files_inaccessible"]), style="yellow")
    table.add_row("总大小", f"{stats['total_size'] / (1024*1024):.2f} MB")
    
    if upload_to_openai:
        table.add_row("━━━━ Vector Store ━━━━", "", style="bold magenta")
        table.add_row("Vector Stores 创建", str(stats["vector_stores_created"]))
        table.add_row("Vector Stores 重用", str(stats["vector_stores_reused"]))
        table.add_row("文件上传成功", str(stats["files_uploaded_to_vector_store"]))
        table.add_row("文件跳过（已存在）", str(stats["files_upload_skipped"]), style="dim")
        table.add_row("文件上传失败", str(stats["files_upload_failed"]))
    
    table.add_row("━━━━━━━━━━━━", "", style="bold")
    table.add_row("总用时", f"{duration:.1f} 秒")
    
    console.print(table)
    console.print()
    
    # 保存下载报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "canvas_url": canvas_url,
        "statistics": stats,
        "duration_seconds": duration
    }
    
    report_path = DOWNLOAD_ROOT / "download_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    console.print(f"📄 下载报告已保存: {report_path}", style="dim")
    
    # 如果有错误，显示错误列表
    if stats["errors"]:
        console.print(f"\n⚠️  {len(stats['errors'])} 个文件下载失败:", style="yellow bold")
        error_table = Table(show_header=True)
        error_table.add_column("课程", style="cyan")
        error_table.add_column("文件", style="white")
        error_table.add_column("错误", style="red")
        
        for error in stats["errors"][:20]:  # 只显示前20个
            error_table.add_row(
                error.get("course", "N/A"),
                error.get("file", "N/A"),
                error.get("error", "N/A")[:50]
            )
        
        console.print(error_table)
        
        if len(stats["errors"]) > 20:
            console.print(f"\n... 还有 {len(stats['errors']) - 20} 个错误未显示", style="dim")
    
    console.print(f"\n📁 文件保存位置: {DOWNLOAD_ROOT.absolute()}", style="green bold")
    
    # 保存无法访问的文件列表
    if stats["inaccessible_files"]:
        inaccessible_file = DOWNLOAD_ROOT / "inaccessible_files.json"
        with open(inaccessible_file, 'w', encoding='utf-8') as f:
            json.dump(stats["inaccessible_files"], f, indent=2, ensure_ascii=False)
        console.print(f"\n⚠️  {len(stats['inaccessible_files'])} 个文件无法访问（已记录到 inaccessible_files.json）", style="yellow")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Canvas 文件下载器和 Vector Store 上传工具"
    )
    parser.add_argument(
        "--upload-only",
        action="store_true",
        help="只上传已下载的文件到 Vector Store，跳过下载步骤"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="同 --upload-only（别名）"
    )
    parser.add_argument(
        "--course-id",
        type=str,
        help="只下载指定课程ID的文件（例如：--course-id 154630）"
    )
    
    args = parser.parse_args()
    skip_download = args.upload_only or args.skip_download
    course_id = args.course_id
    
    try:
        asyncio.run(main(skip_download=skip_download, course_id=course_id))
    except KeyboardInterrupt:
        console.print("\n\n⚠️  用户中断操作", style="yellow")
        if stats['files_downloaded'] > 0:
            console.print(f"已下载: {stats['files_downloaded']} 个文件", style="dim")
        if stats['files_uploaded_to_vector_store'] > 0:
            console.print(f"已上传: {stats['files_uploaded_to_vector_store']} 个文件", style="dim")
    except Exception as e:
        console.print(f"\n❌ 发生错误: {e}", style="red bold")
        import traceback
        console.print(traceback.format_exc(), style="red dim")

