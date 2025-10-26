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

def install_localtunnel():
    """安装 localtunnel"""
    print("\n🌐 Checking localtunnel...")
    
    try:
        result = subprocess.run(
            ['npx', 'localtunnel', '--version'],
            capture_output=True,
            text=True
        )
        print("  ✓ localtunnel available")
        return True
    except:
        print("  ℹ️  localtunnel will be installed on first use")
        return True

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

def start_localtunnel(port=8000, subdomain=None):
    """启动 localtunnel"""
    print(f"\n🌍 Starting localtunnel for port {port}...")
    
    # Windows 需要使用 shell=True 或者 .cmd 后缀
    cmd = ['npx', 'localtunnel', '--port', str(port)]
    
    if subdomain:
        cmd.extend(['--subdomain', subdomain])
    
    try:
        # 在 Windows 上使用 shell=True
        tunnel_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # 等待 tunnel 启动并显示 URL
        print("   Waiting for tunnel to establish...")
        
        # 读取并显示输出
        import threading
        def read_output():
            for line in tunnel_process.stdout:
                print(f"   {line.strip()}")
                if 'your url is:' in line.lower():
                    break
        
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        time.sleep(5)
        
        return tunnel_process
        
    except Exception as e:
        print(f"   ⚠️  Failed to start localtunnel: {e}")
        print(f"   You can start it manually in another terminal:")
        print(f"   npx localtunnel --port {port}")
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
    
    # 安装 localtunnel
    install_localtunnel()
    
    # 询问是否使用 tunnel
    print("\n" + "="*60)
    print("Configuration:")
    print("="*60)
    
    use_tunnel = input("\n🌐 Enable public access via localtunnel? (y/n): ").lower() == 'y'
    
    if use_tunnel:
        subdomain = input("   Subdomain (leave empty for random): ").strip() or None
    else:
        subdomain = None
    
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
        
        # 启动 LocalTunnel（如果需要）
        if use_tunnel:
            tunnel = start_localtunnel(port, subdomain)
            if tunnel:
                processes.append(tunnel)
        
        print("\n" + "="*60)
        print("✅ Server is running!")
        print("="*60)
        print(f"\n📍 Access your app:")
        print(f"   🏠 Local:  http://localhost:{port}")
        
        if use_tunnel:
            print(f"   🌍 Public: Check the LocalTunnel output above")
            print(f"              (URL format: https://xxxxx.loca.lt)")
            print(f"   🔑 Password: Your public IP address")
            print(f"              (Get it from: https://loca.lt/mytunnelpassword)")
        
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

