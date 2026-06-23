import anthropic
import langchain
import pandas
import pypdf
from dotenv import load_dotenv
import os

load_dotenv()

print("✓ Todas las librerías importadas correctamente")
print(f"✓ ANTHROPIC_API_KEY configurada: {'Sí' if os.getenv('ANTHROPIC_API_KEY') else 'NO'}")
print(f"✓ LANGSMITH_API_KEY configurada: {'Sí' if os.getenv('LANGCHAIN_API_KEY') else 'NO'}")
print(f"✓ LangSmith tracing activo: {os.getenv('LANGCHAIN_TRACING_V2')}")