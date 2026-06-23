from dotenv import load_dotenv
from src.loaders import load_dossier
from src.chain import run_audit

load_dotenv()

dossier = load_dossier("data/dossier_001")
result = run_audit(dossier, "DOS-001")

print(f"\nStatus  : {result.compliance_status}")
print(f"Findings: {result.findings_count}")
print(f"Summary : {result.executive_summary}")