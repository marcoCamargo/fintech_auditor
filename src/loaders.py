"""
loaders.py
Carga y extrae el contenido de los 3 archivos de cada dossier:
  - credit_bureau.pdf   → texto extraído con pypdf
  - client_profile.json → diccionario Python
  - transactions.csv    → resumen estadístico con pandas
"""

import json
import os
import pandas as pd
import pypdf
from src.logger import get_logger

logger = get_logger()


def load_pdf(path: str) -> str:
    """Extrae todo el texto del PDF del buró de crédito."""
    logger.info(f"  [PDF] Cargando: {path}")
    try:
        reader = pypdf.PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        logger.info(f"  [PDF] Extraídas {len(reader.pages)} página(s), {len(text)} caracteres")
        return text.strip()
    except Exception as e:
        logger.error(f"  [PDF] Error al cargar {path}: {e}")
        return ""


def load_json(path: str) -> dict:
    """Carga el perfil declarado por el cliente."""
    logger.info(f"  [JSON] Cargando: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"  [JSON] Perfil cargado: {data.get('full_name', 'N/A')} | "
                    f"Ingreso declarado: ${data.get('declared_monthly_income_usd', 0):,.2f}/mes")
        return data
    except Exception as e:
        logger.error(f"  [JSON] Error al cargar {path}: {e}")
        return {}


def load_csv_summary(path: str) -> dict:
    """
    Carga el CSV de transacciones y calcula métricas clave:
    - Ingreso mensual promedio real (depósitos de nómina)
    - Total de débitos
    - Número de transacciones
    """
    logger.info(f"  [CSV] Cargando: {path}")
    try:
        df = pd.read_csv(path, parse_dates=["date"])

        credits = df[df["type"] == "credit"]
        payroll = credits[credits["description"] == "PAYROLL DEPOSIT"]

        avg_monthly_deposit = payroll["amount_usd"].mean() if not payroll.empty else 0.0
        total_credits = credits["amount_usd"].sum()
        total_debits = df[df["type"] == "debit"]["amount_usd"].sum()
        num_transactions = len(df)
        num_payroll_deposits = len(payroll)

        summary = {
            "avg_monthly_payroll_deposit_usd": round(avg_monthly_deposit, 2),
            "total_credits_usd": round(total_credits, 2),
            "total_debits_usd": round(total_debits, 2),
            "num_transactions": num_transactions,
            "num_payroll_deposits": num_payroll_deposits,
        }

        logger.info(f"  [CSV] {num_transactions} transacciones | "
                    f"Depósito promedio nómina: ${avg_monthly_deposit:,.2f}/mes")
        return summary

    except Exception as e:
        logger.error(f"  [CSV] Error al cargar {path}: {e}")
        return {}


def load_dossier(dossier_path: str) -> dict:
    """
    Carga los 3 archivos de un dossier y retorna un diccionario
    con todo el contenido listo para el pipeline.
    """
    pdf_path  = os.path.join(dossier_path, "credit_bureau.pdf")
    json_path = os.path.join(dossier_path, "client_profile.json")
    csv_path  = os.path.join(dossier_path, "transactions.csv")

    return {
        "credit_bureau_text": load_pdf(pdf_path),
        "client_profile":     load_json(json_path),
        "transaction_summary": load_csv_summary(csv_path),
    }
