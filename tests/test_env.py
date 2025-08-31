#!/usr/bin/env python3
"""Test script to verify environment variables are set correctly."""

import os
import sys
import pathlib
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

def check_env_vars():
    """Check if all required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "NOTION_API_KEY", 
        "EG_NOTION_DB_ID",
        "EXA_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these variables in your .env file or environment")
        print("   See .env.example for reference")
        return False
    else:
        print("✅ All required environment variables are set!")
        return True

if __name__ == "__main__":
    if check_env_vars():
        print("🚀 Ready to run the pipeline!")
        sys.exit(0)
    else:
        print("⚠️  Please set missing environment variables before running")
        sys.exit(1)
