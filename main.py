"""
main.py — Entry point for the FinTech Compliance Auditor.

Orchestrates the full batch pipeline:
  1. Discovers all dossier directories under data/
  2. Loads each dossier's three source files (PDF, JSON, CSV) via loaders.py
  3. Invokes the LCEL audit chain (LLM + Pydantic parser) via chain.py
  4. Aggregates results into output/audit_report.json
  5. Writes a timestamped execution log to output/langchain_demo.log

Expected runtime: ~2–4 seconds per dossier (one LLM call each).
"""

import os
import json
import time
from dotenv import load_dotenv
from src.loaders import load_dossier
from src.chain import run_audit
from src.logger import get_logger

load_dotenv()
logger = get_logger()

# Paths — relative to the project root
DATA_DIR    = "data"
OUTPUT_DIR  = "output"
REPORT_PATH = os.path.join(OUTPUT_DIR, "audit_report.json")


def get_dossier_dirs() -> list[str]:
    """
    Return a sorted list of dossier directory paths found under DATA_DIR.

    Only directories whose names start with 'dossier_' are included,
    which excludes ground_truth.json and any other top-level files.
    """
    dirs = []
    for name in sorted(os.listdir(DATA_DIR)):
        full_path = os.path.join(DATA_DIR, name)
        if os.path.isdir(full_path) and name.startswith("dossier_"):
            dirs.append(full_path)
    return dirs


def main():
    """
    Run the full compliance audit across all dossiers.

    For each dossier the pipeline is:
      load_dossier() → run_audit() → append to results or errors list

    A final JSON report is written to REPORT_PATH regardless of individual
    dossier failures — failed dossiers are tracked in 'failed_dossiers'.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("=" * 60)
    logger.info("APEX CREDIT SOLUTIONS — AUTOMATED FINANCIAL AUDITOR")
    logger.info("=" * 60)

    dossier_dirs = get_dossier_dirs()
    total = len(dossier_dirs)
    logger.info(f"Dossiers found: {total}")

    results: list[dict] = []  # Successfully audited dossiers
    errors:  list[str]  = []  # Dossier IDs that could not be processed

    for idx, dossier_path in enumerate(dossier_dirs, start=1):
        dossier_name = os.path.basename(dossier_path)
        logger.info(f"\n[{idx:03d}/{total}] Processing {dossier_name}")

        # Step 1 — Load the three source files (PDF + JSON + CSV)
        dossier_data = load_dossier(dossier_path)
        dossier_id   = dossier_data.get("client_profile", {}).get("dossier_id", dossier_name)

        # Step 2 — Run the LCEL pipeline (prompt → LLM → Pydantic parser)
        start = time.time()
        audit_result = run_audit(dossier_data, dossier_id)
        elapsed = round(time.time() - start, 2)

        if audit_result:
            record = {
                "dossier_id":        dossier_id,
                "compliance_status": audit_result.compliance_status,
                "findings_count":    audit_result.findings_count,
                "executive_summary": audit_result.executive_summary,
                "processing_time_s": elapsed,
            }
            results.append(record)
            logger.info(
                f"  [OK] {dossier_id} → {audit_result.compliance_status} "
                f"({audit_result.findings_count} findings) [{elapsed}s]"
            )
        else:
            # run_audit() returns None on LLM or parsing failure; see chain.py
            errors.append(dossier_id)
            logger.error(f"  [FAIL] {dossier_id} → Could not be audited (see log above)")

    # Step 3 — Build and persist the final report
    report = {
        "total_processed": len(results),
        "total_errors":    len(errors),
        "compliant":       sum(1 for r in results if r["compliance_status"] == "Compliant"),
        "non_compliant":   sum(1 for r in results if r["compliance_status"] == "Non-Compliant"),
        "failed_dossiers": errors,
        "audit_results":   results,
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Step 4 — Print final summary to console and log file
    logger.info("\n" + "=" * 60)
    logger.info("AUDIT COMPLETE")
    logger.info(f"  Total processed  : {report['total_processed']}")
    logger.info(f"  Compliant        : {report['compliant']}")
    logger.info(f"  Non-Compliant    : {report['non_compliant']}")
    logger.info(f"  Errors           : {report['total_errors']}")
    logger.info(f"  Report saved to  : {REPORT_PATH}")
    logger.info(f"  Log saved to     : output/langchain_demo.log")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
