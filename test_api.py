"""
Simple test script for NovaHR API
Run: python test_api.py
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_chat_flow():
    """Test a complete chat flow"""
    print("=" * 60)
    print("Testing Chat Flow")
    print("=" * 60)
    
    session_id = f"test-{uuid.uuid4()}"
    print(f"Session ID: {session_id}\n")
    
    # Message 1: Hello
    print("1. Sending: 'hello'")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "hello",
            "session_id": session_id,
            "role": "hr"
        }
    )
    print(f"Response: {response.json()['response']}")
    print(f"Intent: {response.json()['intent']}")
    print(f"Step: {response.json()['step']}\n")
    
    # Message 2: Leave request
    print("2. Sending: 'I want to apply for leave'")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": "I want to apply for leave",
            "session_id": session_id,
            "role": "employee",
            "employee_id": 1,
            "employee_name": "Test User"
        }
    )
    print(f"Response: {response.json()['response']}")
    print(f"Intent: {response.json()['intent']}")
    print(f"Step: {response.json()['step']}\n")
    
    # Check session
    print("3. Checking session status")
    response = requests.get(f"{BASE_URL}/api/chat/session/{session_id}")
    print(f"Session Info: {json.dumps(response.json(), indent=2)}\n")
    
    # Delete session
    print("4. Deleting session")
    response = requests.delete(f"{BASE_URL}/api/chat/session/{session_id}")
    print(f"Response: {response.json()['message']}\n")


def test_list_sessions():
    """Test list sessions endpoint"""
    print("=" * 60)
    print("Testing List Sessions")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/chat/sessions")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def main():
    print("\n" + "=" * 60)
    print("NovaHR API Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_health()
        test_chat_flow()
        test_list_sessions()
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("Make sure the server is running:")
        print("  uvicorn api.main:app --reload --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
