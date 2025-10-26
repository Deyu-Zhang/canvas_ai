"""
Canvas AI Agent - 服务器启动脚本
包含 API 服务器和 LocalTunnel 配置
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_dependencies():
    """检查并安装依赖"""
    print("🔍 Checking dependencies...")
    
    required_packages = {
        'fastapi': 'fastapi>=0.104.0',
        'uvicorn': 'uvicorn[standard]>=0.24.0',
        'websockets': 'websockets>=12.0'
    }
    
    missing_packages = []
    
    for package, install_name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {package} installed")
        except ImportError:
            missing_packages.append(install_name)
            print(f"  ✗ {package} not found")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages...")
        for package in missing_packages:
            print(f"   Installing {package}...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package
            ])
        print("  ✓ All packages installed")
    else:
        print("  ✓ All dependencies satisfied")

def check_env():
    """检查环境变量配置"""
    print("\n🔧 Checking environment configuration...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'CANVAS_URL': 'Canvas LMS URL',
        'CANVAS_ACCESS_TOKEN': 'Canvas Access Token',
        'AZURE_OPENAI_API_KEY': 'Azure OpenAI API Key',
        'OPENAI_API_KEY': 'OpenAI API Key'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        if os.getenv(var):
            print(f"  ✓ {description}")
        else:
            missing_vars.append(f"{var} ({description})")
            print(f"  ✗ {description}")
    
    if missing_vars:
        print("\n⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease configure these in your .env file")
        return False
    
    return True

def check_frontend():
    """检查前端是否已构建"""
    script_dir = Path(__file__).parent
    frontend_build = script_dir / "frontend" / "build"
    
    if frontend_build.exists():
        print(f"\n✓ Frontend build found")
        return True
    else:
        print(f"\n⚠️  Frontend build not found")
        print(f"   Run 'npm run build' in frontend directory")
        print(f"   (Path checked: {frontend_build})")
        return False

def check_tunnel_tool():
    """检查隧道工具"""
    print("\n🌐 Checking tunnel tool (ngrok)...")
    
    try:
        result = subprocess.run(
            ['ngrok', 'version'],
            capture_output=True,
            text=True
        )
        print(f"  ✓ ngrok available: {result.stdout.strip()}")
        return True
    except:
        print("  ⚠️  ngrok not found")
        print("     Install from: https://ngrok.com/download")
        return False

def start_backend(port=8000):
    """启动后端服务器"""
    print(f"\n🚀 Starting backend server on port {port}...")
    
    # 确保在正确的目录下运行
    script_dir = Path(__file__).parent
    api_server_path = script_dir / 'api_server.py'
    
    backend_process = subprocess.Popen(
        [sys.executable, str(api_server_path)],
        cwd=str(script_dir),
        env={**os.environ, 'PORT': str(port)}
    )
    
    # 等待服务器启动
    print("   Waiting for server to start...")
    time.sleep(3)
    
    return backend_process

def start_ngrok(port=8000):
    """启动 ngrok"""
    print(f"\n🌍 Starting ngrok for port {port}...")
    
    try:
        # 检查 ngrok 是否已安装
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        print(f"   Found ngrok: {result.stdout.strip()}")
    except:
        print("   ⚠️  ngrok not found!")
        print("   Please install ngrok:")
        print("   1. Download from: https://ngrok.com/download")
        print("   2. Or run: choco install ngrok (if you have Chocolatey)")
        print("   3. Sign up for free account at: https://ngrok.com/")
        print("   4. Run: ngrok config add-authtoken YOUR_TOKEN")
        return None
    
    try:
        # 启动 ngrok（使用 --url 参数来请求一个临时域名）
        cmd = ['ngrok', 'http', str(port), '--log=stdout']
        
        tunnel_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print("   Waiting for ngrok to establish...")
        time.sleep(5)
        
        # 尝试从 ngrok API 获取公网 URL
        try:
            import requests
            response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print(f"\n✓ Ngrok tunnel started!")
                    print(f"   Public URL: {public_url}")
                    print(f"   Local URL:  http://localhost:{port}")
                    print(f"   Web UI:     http://127.0.0.1:4040")
                    return tunnel_process
        except Exception as e:
            print(f"   ⚠️  Could not get tunnel URL from API: {e}")
        
        # 如果 API 获取失败，读取 stdout
        print("   Checking tunnel output...")
        import threading
        def read_output():
            try:
                for line in tunnel_process.stdout:
                    if 'url=' in line.lower() or 'started tunnel' in line.lower():
                        print(f"   {line.strip()}")
                        if 'url=' in line.lower():
                            break
            except:
                pass
        
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        return tunnel_process
        
    except Exception as e:
        print(f"   ⚠️  Failed to start ngrok: {e}")
        return None

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🎓 Canvas AI Agent - Server Startup")
    print("="*60)
    
    # 检查依赖
    check_dependencies()
    
    # 检查环境变量
    if not check_env():
        print("\n❌ Environment configuration incomplete")
        print("   Please configure .env file and try again")
        sys.exit(1)
    
    # 检查前端
    frontend_ready = check_frontend()
    
    # 检查隧道工具
    tunnel_available = check_tunnel_tool()
    
    # 询问是否使用 tunnel
    print("\n" + "="*60)
    print("Configuration:")
    print("="*60)
    
    # 默认不启用 ngrok，避免域名配置问题
    print("\n💡 Tip: 使用本地地址访问即可，公网访问需要额外配置")
    if tunnel_available:
        use_tunnel = input("\n🌐 Enable public access via ngrok? (需要先申请免费域名) (y/n): ").lower() == 'y'
        if use_tunnel:
            print("\n⚠️  注意: 如果出现域名错误，请先访问:")
            print("   https://dashboard.ngrok.com/domains")
            print("   申请一个免费的 static domain")
    else:
        use_tunnel = False
        print("\n⚠️  Ngrok not available, skipping public access setup")
    
    port = input("\n📡 Port (default: 8000): ").strip() or '8000'
    port = int(port)
    
    print("\n" + "="*60)
    print("Starting services...")
    print("="*60)
    
    # 启动服务
    processes = []
    
    try:
        # 启动后端
        backend = start_backend(port)
        processes.append(backend)
        
        # 启动 Ngrok（如果需要）
        if use_tunnel:
            tunnel = start_ngrok(port)
            if tunnel:
                processes.append(tunnel)
        
        print("\n" + "="*60)
        print("✅ Server is running!")
        print("="*60)
        print(f"\n📍 Access your app:")
        print(f"   🏠 Local:  http://localhost:{port}")
        
        if use_tunnel:
            print(f"   🌍 Public: Check the ngrok output above")
            print(f"              (URL format: https://xxxxx.ngrok-free.app)")
            print(f"   🎛️  Web UI: http://127.0.0.1:4040 (inspect requests)")
        
        print(f"\n📖 API Documentation:")
        print(f"   http://localhost:{port}/docs")
        
        if not frontend_ready:
            print(f"\n⚠️  Frontend not built. To build:")
            print(f"   cd frontend")
            print(f"   npm install")
            print(f"   npm run build")
        else:
            print(f"\n✅ Frontend ready at:")
            print(f"   http://localhost:{port}/")
        
        print(f"\n💡 Press Ctrl+C to stop all services")
        print("="*60 + "\n")
        
        # 保持运行
        for process in processes:
            process.wait()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping services...")
        for process in processes:
            process.terminate()
        print("✓ All services stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        for process in processes:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()

