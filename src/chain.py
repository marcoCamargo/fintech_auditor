"""
chain.py
Pipeline LCEL principal del auditor financiero.
Usa Claude (Anthropic) con structured output via Pydantic.
"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda
from src.schema import AuditResult
from src.logger import get_logger

load_dotenv()
logger = get_logger()

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.0,       # Determinístico — requerido por el proyecto
    max_tokens=1024,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# ── Output Parser ──────────────────────────────────────────────────────────────
parser = PydanticOutputParser(pydantic_object=AuditResult)

# ── Prompt Template ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a strict financial compliance auditor for Apex Credit Solutions.
Your role is to analyze client dossiers and detect regulatory violations.
You must be precise, objective, and conservative in your assessments.
Never fabricate findings — base everything strictly on the data provided.

COMPLIANCE RULES:
1. INCOME DISCREPANCY: Flag if declared monthly income differs from actual payroll deposits by more than 20%.
2. CREDIT SCORE: Flag if credit score is below 580.
3. INCONSISTENCY: Flag if a client claims high income (>$8,000/mo) but has a poor credit score (<620).
4. MISSING DATA: Flag if any required document section is empty or unreadable.

OUTPUT REQUIREMENTS:
{format_instructions}

IMPORTANT: executive_summary must be under 500 characters. Be concise."""

USER_PROMPT = """Analyze the following client dossier and produce a compliance audit report.

=== CREDIT BUREAU REPORT (PDF) ===
{credit_bureau_text}

=== CLIENT DECLARED PROFILE (JSON) ===
Dossier ID: {dossier_id}
Full Name: {full_name}
Employment: {employment_status} at {employer}
Declared Monthly Income: ${declared_monthly_income_usd}
Credit Requested: ${credit_requested_usd}
Existing Debts: ${existing_debts_usd}
Loan Purpose: {loan_purpose}

=== BANK TRANSACTION SUMMARY (CSV) ===
Average Monthly Payroll Deposit: ${avg_monthly_payroll_deposit_usd}
Total Credits (12 months): ${total_credits_usd}
Total Debits (12 months): ${total_debits_usd}
Total Transactions: {num_transactions}
Payroll Deposits Found: {num_payroll_deposits}

Now produce the structured audit output:"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_PROMPT),
])

# ── Preparar inputs ────────────────────────────────────────────────────────────
def prepare_inputs(dossier_data: dict) -> dict:
    """Aplana el dossier en variables planas para el prompt."""
    profile = dossier_data.get("client_profile", {})
    tx      = dossier_data.get("transaction_summary", {})
    return {
        "credit_bureau_text":            dossier_data.get("credit_bureau_text", "N/A"),
        "dossier_id":                    profile.get("dossier_id", "N/A"),
        "full_name":                     profile.get("full_name", "N/A"),
        "employment_status":             profile.get("employment_status", "N/A"),
        "employer":                      profile.get("employer", "N/A"),
        "declared_monthly_income_usd":   profile.get("declared_monthly_income_usd", 0),
        "credit_requested_usd":          profile.get("credit_requested_usd", 0),
        "existing_debts_usd":            profile.get("existing_debts_usd", 0),
        "loan_purpose":                  profile.get("loan_purpose", "N/A"),
        "avg_monthly_payroll_deposit_usd": tx.get("avg_monthly_payroll_deposit_usd", 0),
        "total_credits_usd":             tx.get("total_credits_usd", 0),
        "total_debits_usd":              tx.get("total_debits_usd", 0),
        "num_transactions":              tx.get("num_transactions", 0),
        "num_payroll_deposits":          tx.get("num_payroll_deposits", 0),
        "format_instructions":           parser.get_format_instructions(),
    }

# ── Chain LCEL ─────────────────────────────────────────────────────────────────
audit_chain = (
    RunnableLambda(prepare_inputs)
    | prompt
    | llm
    | parser
)


def run_audit(dossier_data: dict, dossier_id: str) -> AuditResult | None:
    """
    Ejecuta el pipeline completo para un dossier.
    Retorna un AuditResult validado o None si hay error.
    """
    logger.info(f"  [CHAIN] Iniciando auditoría LLM para {dossier_id}")
    try:
        result: AuditResult = audit_chain.invoke(dossier_data)
        logger.info(f"  [CHAIN] Resultado → Status: {result.compliance_status} | "
                    f"Findings: {result.findings_count} | "
                    f"Summary: {result.executive_summary[:80]}...")
        return result
    except Exception as e:
        logger.error(f"  [CHAIN] Error en auditoría de {dossier_id}: {e}")
        return None
