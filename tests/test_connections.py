"""
Test database and API connections
Run: python tests/test_connections.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.db_connection import get_db
from dotenv import load_dotenv

load_dotenv()


def test_mysql_connection():
    """Test MySQL database connection"""
    print("Testing MySQL connection...")
    try:
        db = get_db()
        if db.connection and db.connection.is_connected():
            print("✓ MySQL connection successful")
            
            # Test query
            result = db.execute_query("SELECT COUNT(*) as count FROM employees")
            if result:
                print(f"✓ Found {result[0]['count']} employees in database")
            return True
        else:
            print("✗ MySQL connection failed")
            return False
    except Exception as e:
        print(f"✗ MySQL error: {e}")
        return False


def test_groq_api():
    """Test Groq API key"""
    print("\nTesting Groq API...")
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and len(groq_key) > 20:
            print(f"✓ Groq API key found (length: {len(groq_key)})")
            return True
        else:
            print("✗ Groq API key not found or invalid")
            return False
    except Exception as e:
        print(f"✗ Groq API error: {e}")
        return False


def test_email_config():
    """Test email configuration"""
    print("\nTesting Email configuration...")
    try:
        email = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_APP_PASSWORD")
        if email and password:
            print(f"✓ Email configured: {email}")
            return True
        else:
            print("✗ Email configuration missing")
            return False
    except Exception as e:
        print(f"✗ Email config error: {e}")
        return False


def test_chroma_db():
    """Test ChromaDB"""
    print("\nTesting ChromaDB...")
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chroma_path = os.path.join(base_dir, "data", "chroma_db")
        
        if os.path.exists(chroma_path):
            print(f"✓ ChromaDB directory found: {chroma_path}")
            return True
        else:
            print(f"✗ ChromaDB directory not found: {chroma_path}")
            print("  Run: python src/tools/embed_policy.py to create it")
            return False
    except Exception as e:
        print(f"✗ ChromaDB error: {e}")
        return False


def test_google_credentials():
    """Test Google Calendar credentials"""
    print("\nTesting Google Calendar credentials...")
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        token_path = os.path.join(base_dir, "token.json")
        creds_path = os.path.join(base_dir, "Credentials.json")
        
        if os.path.exists(token_path):
            print(f"✓ token.json found")
        else:
            print(f"✗ token.json not found")
            
        if os.path.exists(creds_path):
            print(f"✓ Credentials.json found")
        else:
            print(f"✗ Credentials.json not found")
            
        return os.path.exists(token_path) and os.path.exists(creds_path)
    except Exception as e:
        print(f"✗ Google credentials error: {e}")
        return False


def main():
    print("=" * 50)
    print("NovaHR Connection Tests")
    print("=" * 50)
    
    results = []
    results.append(("MySQL", test_mysql_connection()))
    results.append(("Groq API", test_groq_api()))
    results.append(("Email", test_email_config()))
    results.append(("ChromaDB", test_chroma_db()))
    results.append(("Google Calendar", test_google_credentials()))
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    for name, status in results:
        symbol = "✓" if status else "✗"
        print(f"{symbol} {name}: {'PASS' if status else 'FAIL'}")
    
    total = len(results)
    passed = sum(1 for _, status in results if status)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System ready.")
    else:
        print("\n✗ Some tests failed. Please fix configuration.")


if __name__ == "__main__":
    main()
