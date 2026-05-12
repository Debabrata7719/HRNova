"""Start the NovaHR API server — run: python scripts/start_api.py"""
import os
import sys
import subprocess

# Go up one level from scripts/ to project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)
sys.path.insert(0, project_root)

# ASCII Banner
banner = r"""
███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██╗  ██╗██████╗ 
████╗  ██║██╔═══██╗██║   ██║██╔══██╗██║  ██║██╔══██╗
██╔██╗ ██║██║   ██║██║   ██║███████║███████║██████╔╝
██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║██╔══██║██╔══██╗
██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║██║  ██║██║  ██║
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
"""

print(banner)
print("Starting NovaHR API server...")
print(f" Working directory: {project_root}")
print("API docs: http://localhost:8000/docs\n")

subprocess.run([
    sys.executable, "-m", "uvicorn",
    "api.main:app",
    "--reload",
    "--port", "8000",
    "--host", "0.0.0.0"
])