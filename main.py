"""
main.py
Entry point del FinTech Compliance Auditor.
Orquesta la carga de los 100 dossiers, el pipeline LCEL,
y genera el reporte final en output/audit_report.json
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

DATA_DIR   = "data"
OUTPUT_DIR = "output"
REPORT_PATH = os.path.join(OUTPUT_DIR, "audit_report.json")


def get_dossier_dirs() -> list[str]:
    """Retorna la lista ordenada de carpetas de dossiers."""
    dirs = []
    for name in sorted(os.listdir(DATA_DIR)):
        full_path = os.path.join(DATA_DIR, name)
        if os.path.isdir(full_path) and name.startswith("dossier_"):
            dirs.append(full_path)
    return dirs


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("=" * 60)
    logger.info("APEX CREDIT SOLUTIONS — AUTOMATED FINANCIAL AUDITOR")
    logger.info("=" * 60)

    dossier_dirs = get_dossier_dirs()
    logger.info(f"Dossiers encontrados: {len(dossier_dirs)}")

    results = []
    errors  = []

    for idx, dossier_path in enumerate(dossier_dirs, start=1):
        dossier_name = os.path.basename(dossier_path)
        logger.info(f"\n[{idx:03d}/{len(dossier_dirs)}] Procesando {dossier_name}")

        # 1. Cargar los 3 archivos
        dossier_data = load_dossier(dossier_path)
        dossier_id   = dossier_data.get("client_profile", {}).get("dossier_id", dossier_name)

        # 2. Ejecutar el pipeline LCEL
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
            logger.info(f"  [OK] {dossier_id} → {audit_result.compliance_status} "
                        f"({audit_result.findings_count} findings) [{elapsed}s]")
        else:
            errors.append(dossier_id)
            logger.error(f"  [FAIL] {dossier_id} → No se pudo auditar")

    # 3. Guardar reporte final
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

    # 4. Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("AUDITORÍA COMPLETADA")
    logger.info(f"  Total procesados : {report['total_processed']}")
    logger.info(f"  Compliant        : {report['compliant']}")
    logger.info(f"  Non-Compliant    : {report['non_compliant']}")
    logger.info(f"  Errores          : {report['total_errors']}")
    logger.info(f"  Reporte guardado : {REPORT_PATH}")
    logger.info(f"  Log guardado     : output/langchain_demo.log")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
