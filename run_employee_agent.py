"""
NovaHR Employee Agent - Employee Portal
Run: python run_employee_agent.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main_agent.agents.employee.executor import run_employee_agent

if __name__ == "__main__":
    run_employee_agent()
