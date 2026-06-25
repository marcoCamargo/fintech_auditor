"""
test_setup.py — Environment and dependency verification script.

Checks that all required libraries are importable and that the necessary
environment variables are set before running the main pipeline.

Run from the project root:
    python tests/test_setup.py
"""

import sys
import os

# Ensure project root is on sys.path so 'src.*' imports resolve correctly
# regardless of which directory the script is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
import langchain
import pandas
import pypdf
from dotenv import load_dotenv

load_dotenv()

print("✓ All libraries imported successfully")
print(f"✓ ANTHROPIC_API_KEY set: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'NO — add it to .env'}")
print(f"✓ LANGCHAIN_API_KEY set: {'Yes' if os.getenv('LANGCHAIN_API_KEY') else 'NO — add it to .env'}")
print(f"✓ LangSmith tracing:     {os.getenv('LANGCHAIN_TRACING_V2', 'not set')}")
