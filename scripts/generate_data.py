"""
generate_data.py — Synthetic dossier generator for the FinTech Compliance Auditor.

Run this script once to populate the data/ directory with 100 client dossiers.
Each dossier is a subdirectory (data/dossier_001/ … data/dossier_100/) containing:
  - credit_bureau.pdf    : credit bureau report with score, account history, and inquiries
  - client_profile.json  : self-declared client data (income, employment, loan purpose)
  - transactions.csv     : 12 months of synthetic bank transactions (1 payroll + 8-15 debits/month)

Exactly 30 of the 100 dossiers are intentionally Non-Compliant:
  - Declared income is inflated 25–60% above actual payroll deposits
  - Credit score is set in the 480–650 range (triggers score and/or inconsistency rules)

The remaining 70 dossiers are Compliant:
  - Declared income matches actual deposits within ±10%
  - Credit score is in the 620–850 range

After generation, data/ground_truth.json is written with expected audit results
so the LLM output can be validated against known labels.

Usage:
    python generate_data.py

WARNING: Re-running this script overwrites all existing dossiers and resets
the ground truth. The random seed (42) is fixed so output is reproducible.
"""

import os
import json
import random
import pandas as pd
from datetime import date
from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

fake = Faker("es_MX")
random.seed(42)  # Fixed seed — ensures reproducible dossier content across runs

DATA_DIR = "data"


def ensure_dirs():
    """Create the top-level data/ directory if it does not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def generate_client_profile(dossier_id: int, declared_income: float) -> dict:
    """
    Build the client's self-declared profile as a Python dict (saved as JSON).

    Args:
        dossier_id:       Sequential dossier number (1–100).
        declared_income:  Monthly income the client claims, in USD. For Non-Compliant
                          dossiers this is intentionally inflated vs. actual payroll.

    Returns:
        Dict with personal, employment, and loan request fields.
    """
    return {
        "dossier_id": f"DOS-{dossier_id:03d}",
        "full_name": fake.name(),
        "national_id": fake.bothify(text="??######??"),
        "date_of_birth": fake.date_of_birth(minimum_age=22, maximum_age=65).isoformat(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address().replace("\n", ", "),
        "employment_status": random.choice(["employed", "self_employed", "contractor"]),
        "employer": fake.company(),
        "declared_monthly_income_usd": round(declared_income, 2),
        "credit_requested_usd": round(random.uniform(5000, 80000), 2),
        "loan_purpose": random.choice([
            "home_improvement", "debt_consolidation",
            "business_expansion", "vehicle_purchase", "education"
        ]),
        "years_at_current_job": random.randint(1, 20),
        "existing_debts_usd": round(random.uniform(0, 30000), 2),
    }


def generate_transactions_csv(dossier_id: int, actual_monthly_income: float, path: str):
    """
    Generate 12 months of bank transactions and write them to a CSV file.

    For each month the CSV contains:
      - One PAYROLL DEPOSIT credit, slightly jittered (±5%) around actual_monthly_income
        to simulate minor payroll variability. This is the value loaders.py uses to
        compute avg_monthly_payroll_deposit_usd for income verification.
      - 8–15 random debit transactions (groceries, rent, utilities, etc.)

    Args:
        dossier_id:            Sequential dossier number (unused in content, kept for symmetry).
        actual_monthly_income: True monthly payroll amount in USD (before jitter).
        path:                  Destination file path for the CSV.
    """
    rows = []
    for month in range(1, 13):
        # One payroll deposit per month — jittered ±5% to simulate real payroll variability
        rows.append({
            "date": f"2024-{month:02d}-05",
            "description": "PAYROLL DEPOSIT",
            "amount_usd": round(actual_monthly_income * random.uniform(0.95, 1.05), 2),
            "type": "credit",
            "balance_usd": round(random.uniform(1000, 15000), 2),
        })
        # Random everyday expenses for the month
        for _ in range(random.randint(8, 15)):
            rows.append({
                "date": fake.date_between(
                    start_date=date(2024, month, 1),
                    end_date=date(2024, month, 28)
                ).isoformat(),
                "description": random.choice([
                    "GROCERY STORE", "UTILITY BILL", "RENT PAYMENT",
                    "RESTAURANT", "ONLINE TRANSFER", "ATM WITHDRAWAL",
                    "INSURANCE PREMIUM", "SUBSCRIPTION SERVICE"
                ]),
                "amount_usd": round(random.uniform(20, 2500), 2),
                "type": "debit",
                "balance_usd": round(random.uniform(500, 12000), 2),
            })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(path, index=False)


def generate_credit_bureau_pdf(dossier_id: int, profile: dict, credit_score: int, path: str):
    """
    Generate a synthetic credit bureau PDF report using ReportLab.

    Sections included:
      - Credit score and rating band (Poor / Fair / Good / Excellent)
      - Credit history: 2–6 accounts with randomized balance and payment status
      - Inquiries: hard and soft inquiry counts for the last 12 months
      - Public records: 10% chance of a bankruptcy filing entry

    Args:
        dossier_id:   Sequential dossier number (used for display only).
        profile:      Client profile dict (provides name, ID, dossier_id).
        credit_score: FICO-style score (300–850). Controls the rating label.
        path:         Destination file path for the PDF.
    """
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("APEX CREDIT BUREAU — OFFICIAL CREDIT REPORT", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Report Date: {fake.date_this_year().isoformat()}", styles["Normal"]))
    story.append(Paragraph(f"Dossier ID: {profile['dossier_id']}", styles["Normal"]))
    story.append(Paragraph(f"Client Name: {profile['full_name']}", styles["Normal"]))
    story.append(Paragraph(f"National ID: {profile['national_id']}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("CREDIT SCORE SUMMARY", styles["Heading2"]))
    story.append(Paragraph(f"Credit Score: {credit_score} / 850", styles["Normal"]))
    rating = (
        "Excellent" if credit_score >= 750 else
        "Good"      if credit_score >= 670 else
        "Fair"      if credit_score >= 580 else
        "Poor"
    )
    story.append(Paragraph(f"Rating: {rating}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("CREDIT HISTORY", styles["Heading2"]))
    num_accounts = random.randint(2, 6)
    for i in range(num_accounts):
        status = random.choices(
            ["Current", "Closed", "Late (30 days)", "Late (60 days)"],
            weights=[70, 15, 10, 5]
        )[0]
        story.append(Paragraph(
            f"Account {i+1}: {fake.company()} — "
            f"{random.choice(['Credit Card', 'Auto Loan', 'Mortgage', 'Personal Loan'])} "
            f"| Balance: ${random.randint(0, 25000):,} | Status: {status}",
            styles["Normal"]
        ))

    story.append(Spacer(1, 12))
    story.append(Paragraph("INQUIRIES (Last 12 months)", styles["Heading2"]))
    story.append(Paragraph(f"Hard Inquiries: {random.randint(0, 5)}", styles["Normal"]))
    story.append(Paragraph(f"Soft Inquiries: {random.randint(0, 10)}", styles["Normal"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("PUBLIC RECORDS", styles["Heading2"]))
    has_record = random.random() < 0.1  # 10% chance of a bankruptcy entry
    story.append(Paragraph(
        "Bankruptcy filing: YES — Chapter 7, Filed 2021" if has_record
        else "No public records found.",
        styles["Normal"]
    ))

    doc.build(story)


def is_compliant(declared_income: float, actual_income: float, credit_score: int) -> tuple[bool, list[str]]:
    """
    Apply the four compliance rules and return the verdict with a list of findings.

    Rules (mirrors the system prompt in chain.py):
      1. Income discrepancy > 20% between declared and actual payroll income
      2. Credit score below 580
      3. High income claim (> $8,000/mo) paired with poor credit (< 620)
      (Rule 4 — missing data — cannot occur in generated dossiers.)

    Args:
        declared_income: Monthly income the client declared (USD).
        actual_income:   True monthly payroll amount used in the CSV (USD).
        credit_score:    FICO-style score assigned during generation.

    Returns:
        Tuple of (is_compliant: bool, findings: list[str]).
        findings is empty when is_compliant is True.
    """
    findings = []
    discrepancy_pct = abs(declared_income - actual_income) / actual_income * 100

    if discrepancy_pct > 20:
        findings.append(
            f"Income discrepancy: declared ${declared_income:,.0f}/mo vs "
            f"actual deposits ${actual_income:,.0f}/mo ({discrepancy_pct:.1f}% gap)"
        )
    if credit_score < 580:
        findings.append(f"Credit score below minimum threshold: {credit_score}/850")
    if credit_score < 620 and declared_income > 8000:
        findings.append("High income claim inconsistent with poor credit history")

    return len(findings) == 0, findings


def main():
    """
    Generate all 100 dossiers and write data/ground_truth.json.

    Generation strategy:
      - 30 dossiers are randomly selected (seeded) to be Non-Compliant.
        Their declared income is inflated 25–60% and credit score is 480–650.
      - The remaining 70 are Compliant: income within ±10% and score 620–850.
    """
    ensure_dirs()
    summary = []

    # Randomly select 30 dossier IDs to be Non-Compliant (fixed by seed=42)
    non_compliant_ids = set(random.sample(range(1, 101), 30))

    for i in range(1, 101):
        dossier_dir = os.path.join(DATA_DIR, f"dossier_{i:03d}")
        os.makedirs(dossier_dir, exist_ok=True)

        base_income = round(random.uniform(2500, 12000), 2)

        if i in non_compliant_ids:
            # Inflate declared income 25–60% to trigger the income discrepancy rule
            declared_income = round(base_income * random.uniform(1.25, 1.60), 2)
            actual_income   = base_income
            credit_score    = random.randint(480, 650)
        else:
            # Compliant: declared income closely matches actual payroll (±10%)
            declared_income = round(base_income * random.uniform(0.92, 1.08), 2)
            actual_income   = base_income
            credit_score    = random.randint(620, 850)

        # Generate the three source files for this dossier
        profile   = generate_client_profile(i, declared_income)
        pdf_path  = os.path.join(dossier_dir, "credit_bureau.pdf")
        json_path = os.path.join(dossier_dir, "client_profile.json")
        csv_path  = os.path.join(dossier_dir, "transactions.csv")

        generate_credit_bureau_pdf(i, profile, credit_score, pdf_path)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        generate_transactions_csv(i, actual_income, csv_path)

        compliant, findings = is_compliant(declared_income, actual_income, credit_score)

        summary.append({
            "dossier_id":              profile["dossier_id"],
            "expected_status":         "Compliant" if compliant else "Non-Compliant",
            "expected_findings_count": len(findings),
            "findings_detail":         findings,
        })

        print(
            f"[{'OK  ' if compliant else 'FLAG'}] Dossier {i:03d} — "
            f"{'Compliant' if compliant else 'Non-Compliant'} "
            f"({'0 findings' if not findings else str(len(findings)) + ' finding(s)'})"
        )

    # Persist ground truth for post-run LLM accuracy validation
    with open(os.path.join(DATA_DIR, "ground_truth.json"), "w") as f:
        json.dump(summary, f, indent=2)

    total_nc = sum(1 for s in summary if s["expected_status"] == "Non-Compliant")
    print(f"\n✓ 100 dossiers generated in /data")
    print(f"  Compliant:     {100 - total_nc}")
    print(f"  Non-Compliant: {total_nc}")
    print(f"  Ground truth saved to data/ground_truth.json")


if __name__ == "__main__":
    main()
