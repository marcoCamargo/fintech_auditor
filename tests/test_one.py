"""
test_one.py — Single-dossier smoke test for the audit pipeline.

Loads dossier_001 and runs it through the full LCEL chain to verify
that the end-to-end pipeline works before running the full 100-dossier batch.

Run from the project root:
    python tests/test_one.py
"""

import sys
import os

# Ensure project root is on sys.path so 'src.*' imports resolve correctly
# regardless of which directory the script is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.loaders import load_dossier
from src.chain import run_audit

load_dotenv()

dossier = load_dossier("data/dossier_001")
result = run_audit(dossier, "DOS-001")

if result is None:
    print("\n[ERROR] Audit failed — check output/langchain_demo.log for details")
else:
    print(f"\nStatus  : {result.compliance_status}")
    print(f"Findings: {result.findings_count}")
    print(f"Summary : {result.executive_summary}")
