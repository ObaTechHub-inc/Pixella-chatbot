#!/usr/bin/env python3
"""
Pixella Test Module
Simple test script to verify chatbot functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure Python 3.11+
if sys.version_info < (3, 11):
    print("❌ Error: Python 3.11 or higher is required")
    print(f"   Your version: {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

from chatbot import chatbot

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_AI_MODEL = os.environ.get("GOOGLE_AI_MODEL")
NAME = os.environ.get("USER_NAME")

# Validate environment variables are loaded
if not GOOGLE_API_KEY or not GOOGLE_AI_MODEL:
    raise ValueError(f"Missing environment variables. API Key loaded: {bool(GOOGLE_API_KEY)}, Model: {GOOGLE_AI_MODEL}")


def main():
    """Run a simple test query with the chatbot."""
    print("🤖 Running Pixella chatbot test...")
    print(f"Model: {GOOGLE_AI_MODEL}")
    print("-" * 50)
    
    try:
        result = chatbot.chat(f"say 'hello {NAME}, i'm pixella'.")
        print("✓ Test successful!")
        print(f"Response: {result}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
