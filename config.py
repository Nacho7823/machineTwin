import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs-machines"
SYSTEM_PROMPT_PATH = BASE_DIR / "config" / "systemprompt.md"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "stepfun/step-3.7-flash:free")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.kilo.ai/api/gateway/")
DATABASE_URL = os.getenv("DATABASE_URL", "")
SYSTEM_PROMPT_VERSION = os.getenv("SYSTEM_PROMPT_VERSION", os.getenv("PROMPT_VERSION", "0.0.1"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

MACHINE_NAME = os.getenv("MACHINE_NAME", "Torre de Enfriamiento Industrial T-100")
