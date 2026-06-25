"""
loaders.py — Multi-format document loaders for the FinTech Compliance Auditor.

Each dossier contains three source files that are loaded independently:
  - credit_bureau.pdf    → raw text extracted with pypdf
  - client_profile.json → Python dict with self-declared client data
  - transactions.csv     → statistical summary computed with pandas

The top-level load_dossier() function combines all three into a single dict
that is passed directly into the LCEL pipeline in chain.py.
"""

import json
import os
import pandas as pd
import pypdf
from src.logger import get_logger

logger = get_logger()


def load_pdf(path: str) -> str:
    """
    Extract all text from a credit bureau PDF report.

    Pages are joined with newlines. If a page yields no text (e.g. scanned
    image without OCR), an empty string is used for that page so the rest
    of the document is still returned.

    Returns an empty string on any read or parse error.
    """
    logger.info(f"  [PDF] Loading: {path}")
    try:
        reader = pypdf.PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        logger.info(f"  [PDF] Extracted {len(reader.pages)} page(s), {len(text)} characters")
        return text.strip()
    except Exception as e:
        logger.error(f"  [PDF] Failed to load {path}: {e}")
        return ""


def load_json(path: str) -> dict:
    """
    Load the client's self-declared profile from a JSON file.

    Returns an empty dict on any read or parse error so downstream
    pipeline steps can still run with missing-data defaults.
    """
    logger.info(f"  [JSON] Loading: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(
            f"  [JSON] Profile loaded: {data.get('full_name', 'N/A')} | "
            f"Declared income: ${data.get('declared_monthly_income_usd', 0):,.2f}/mo"
        )
        return data
    except Exception as e:
        logger.error(f"  [JSON] Failed to load {path}: {e}")
        return {}


def load_csv_summary(path: str) -> dict:
    """
    Load a 12-month bank transaction CSV and compute key financial metrics.

    Metrics derived:
      - avg_monthly_payroll_deposit_usd: mean of rows where type='credit'
            and description='PAYROLL DEPOSIT' — used to verify declared income
      - total_credits_usd: sum of all credit-type transactions
      - total_debits_usd: sum of all debit-type transactions
      - num_transactions: total row count
      - num_payroll_deposits: number of payroll deposit entries found

    Returns an empty dict on any read or parse error.
    """
    logger.info(f"  [CSV] Loading: {path}")
    try:
        df = pd.read_csv(path, parse_dates=["date"])

        credits = df[df["type"] == "credit"]
        payroll = credits[credits["description"] == "PAYROLL DEPOSIT"]

        avg_monthly_deposit = payroll["amount_usd"].mean() if not payroll.empty else 0.0
        total_credits       = credits["amount_usd"].sum()
        total_debits        = df[df["type"] == "debit"]["amount_usd"].sum()
        num_transactions    = len(df)
        num_payroll_deposits = len(payroll)

        summary = {
            "avg_monthly_payroll_deposit_usd": round(avg_monthly_deposit, 2),
            "total_credits_usd":               round(total_credits, 2),
            "total_debits_usd":                round(total_debits, 2),
            "num_transactions":                num_transactions,
            "num_payroll_deposits":            num_payroll_deposits,
        }

        logger.info(
            f"  [CSV] {num_transactions} transactions | "
            f"Avg payroll deposit: ${avg_monthly_deposit:,.2f}/mo"
        )
        return summary

    except Exception as e:
        logger.error(f"  [CSV] Failed to load {path}: {e}")
        return {}


def load_dossier(dossier_path: str) -> dict:
    """
    Load all three source files for a single dossier and return them as a
    combined dict ready for the audit pipeline.

    Args:
        dossier_path: Path to the dossier directory (e.g. 'data/dossier_001').

    Returns:
        {
            'credit_bureau_text': str,   # extracted PDF text
            'client_profile':     dict,  # parsed JSON profile
            'transaction_summary': dict, # computed CSV metrics
        }
    """
    pdf_path  = os.path.join(dossier_path, "credit_bureau.pdf")
    json_path = os.path.join(dossier_path, "client_profile.json")
    csv_path  = os.path.join(dossier_path, "transactions.csv")

    return {
        "credit_bureau_text":  load_pdf(pdf_path),
        "client_profile":      load_json(json_path),
        "transaction_summary": load_csv_summary(csv_path),
    }
