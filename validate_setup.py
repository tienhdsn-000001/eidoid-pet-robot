#!/usr/bin/env python3
"""
Validate the Eidoid Pet Robot setup
Checks dependencies, configuration, and basic functionality
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.9+"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.9+)")
        return False


def check_dependencies():
    """Check required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    required = [
        ("google.generativeai", "google-generativeai"),
        ("datetime", "datetime (built-in)"),
    ]
    
    all_ok = True
    for module_name, package_name in required:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - Run: pip install {package_name}")
            all_ok = False
    
    return all_ok


def check_api_key():
    """Check if GOOGLE_API_KEY is set"""
    print("\n🔍 Checking API key...")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"   ✅ GOOGLE_API_KEY is set ({masked_key})")
        return True
    else:
        print("   ❌ GOOGLE_API_KEY not set")
        print("      Set it with: export GOOGLE_API_KEY='your-key-here'")
        return False


def check_files():
    """Check all required files exist"""
    print("\n🔍 Checking project files...")
    
    required_files = [
        "config.py",
        "memory_cache.py",
        "persona.py",
        "main.py",
        "example_usage.py",
        "requirements.txt",
        "README.md",
        ".env.example",
    ]
    
    all_ok = True
    for filename in required_files:
        filepath = Path(filename)
        if filepath.exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} missing")
            all_ok = False
    
    return all_ok


def check_data_directory():
    """Check data directory structure"""
    print("\n🔍 Checking data directories...")
    
    from config import DATA_DIR, MEMORY_DIR
    
    if DATA_DIR.exists():
        print(f"   ✅ {DATA_DIR}")
    else:
        print(f"   ℹ️  {DATA_DIR} will be created on first run")
    
    if MEMORY_DIR.exists():
        print(f"   ✅ {MEMORY_DIR}")
    else:
        print(f"   ℹ️  {MEMORY_DIR} will be created on first run")
    
    return True


def test_imports():
    """Test importing all modules"""
    print("\n🔍 Testing module imports...")
    
    modules = [
        "config",
        "memory_cache",
        "persona",
        "main",
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"   ✅ {module}.py")
        except Exception as e:
            print(f"   ❌ {module}.py - {str(e)}")
            all_ok = False
    
    return all_ok


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("🤖 Eidoid Pet Robot - Setup Validation")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("API Key", check_api_key),
        ("Project Files", check_files),
        ("Data Directories", check_data_directory),
        ("Module Imports", test_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Ready to run.")
        print("\nNext steps:")
        print("  1. Make sure GOOGLE_API_KEY is set:")
        print("     export GOOGLE_API_KEY='your-key-here'")
        print("  2. Run the example:")
        print("     python example_usage.py")
        print("  3. Or start the main loop:")
        print("     python main.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Set API key: export GOOGLE_API_KEY='your-key-here'")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
