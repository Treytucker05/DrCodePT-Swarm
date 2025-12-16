"""
Verify Anki integration is set up correctly
Run this before starting Phase 7
"""

import os
import sys
import requests
from pathlib import Path

def check_backend_env():
    """Check if backend .env exists and has Anki credentials"""
    print("✓ Checking backend configuration...")
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("  ❌ .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        has_api = 'ANTHROPIC_API_KEY=' in content
        has_anki = 'ANKI_EMAIL=' in content and 'ANKI_PASSWORD=' in content
    
    if not has_api:
        print("  ⚠️  ANTHROPIC_API_KEY not in .env")
    if not has_anki:
        print("  ⚠️  ANKI credentials not in .env")
    
    if has_api and has_anki:
        print("  ✅ Backend .env configured")
        return True
    return False

def check_anki_connect():
    """Check if AnkiConnect (Anki desktop) is running"""
    print("✓ Checking AnkiConnect (Anki desktop)...")
    try:
        response = requests.post(
            'http://localhost:8765',
            json={'action': 'version', 'version': 6},
            timeout=2
        )
        if response.status_code == 200:
            print("  ✅ AnkiConnect detected (Anki desktop is running)")
            return True
    except:
        pass
    
    print("  ⚠️  AnkiConnect not responding")
    print("     → Start Anki desktop app")
    print("     → Ensure AnkiConnect addon is installed (2055492159)")
    return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print("✓ Checking Python dependencies...")
    required = ['flask', 'flask_cors', 'anthropic', 'requests', 'dotenv']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('_', '-'))
        except ImportError:
            missing.append(package)
    
    if not missing:
        print("  ✅ All dependencies installed")
        return True
    else:
        print(f"  ❌ Missing: {', '.join(missing)}")
        print("  → Run: pip install -r requirements.txt")
        return False

def check_backend_file():
    """Check if backend app.py exists and has Anki handler"""
    print("✓ Checking backend implementation...")
    app_file = Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print("  ❌ app.py not found")
        return False
    
    with open(app_file, 'r') as f:
        content = f.read()
        has_anki = 'anki_handler' in content
        has_endpoints = '/api/anki' in content
    
    if has_anki and has_endpoints:
        print("  ✅ Backend has Anki integration")
        return True
    else:
        print("  ❌ Backend missing Anki integration")
        return False

def main():
    print("\n" + "="*50)
    print("🔍 ANKI API INTEGRATION - VERIFICATION CHECK")
    print("="*50 + "\n")
    
    checks = [
        check_backend_env(),
        check_dependencies(),
        check_backend_file(),
        check_anki_connect()
    ]
    
    print("\n" + "="*50)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🚀 Ready to start Phase 7!")
        print("   Terminal 1: python backend/app.py")
        print("   Terminal 2: npm start (from frontend/)")
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("\n💡 Fix issues above, then try again")
    
    print("="*50 + "\n")
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
