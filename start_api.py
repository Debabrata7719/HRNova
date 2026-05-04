"""Start the NovaHR API server — run from project root: python start_api.py"""
import os
import sys
import subprocess

# Ensure we're running from project root
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)
sys.path.insert(0, project_root)

print("Starting NovaHR API server...")
print(f"Working directory: {project_root}")
print("API docs: http://localhost:8000/docs\n")

subprocess.run([
    sys.executable, "-m", "uvicorn",
    "api.main:app",
    "--reload",
    "--port", "8000",
    "--host", "0.0.0.0"
])
