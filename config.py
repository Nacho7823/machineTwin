import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs-machines"
PROMPTS_DIR = BASE_DIR / "config" / "prompts"
LEGACY_SYSTEM_PROMPT_PATH = BASE_DIR / "config" / "systemprompt.md"


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _resolve_system_prompt() -> tuple[Path, str]:
    explicit_path = os.getenv("SYSTEM_PROMPT_PATH", "").strip()
    requested_version = os.getenv("SYSTEM_PROMPT_VERSION", os.getenv("PROMPT_VERSION", "0.0.1")).strip() or "0.0.1"
    if explicit_path:
        path = _resolve_path(explicit_path)
        if path.exists():
            inferred_version = path.stem.removeprefix("systemprompt-")
            return path, requested_version if requested_version else inferred_version
        raise FileNotFoundError(f"SYSTEM_PROMPT_PATH no existe: {path}")

    versioned_path = PROMPTS_DIR / f"systemprompt-{requested_version}.md"
    if versioned_path.exists():
        return versioned_path, requested_version

    return LEGACY_SYSTEM_PROMPT_PATH, requested_version


SYSTEM_PROMPT_PATH, SYSTEM_PROMPT_VERSION = _resolve_system_prompt()

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "1"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.95"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "16384"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "0"))
LLM_ENABLE_THINKING = os.getenv("LLM_ENABLE_THINKING", "true").strip().lower() in {"1", "true", "yes", "on"}
LLM_REASONING_BUDGET = int(os.getenv("LLM_REASONING_BUDGET", "16384"))
DATABASE_URL = os.getenv("DATABASE_URL", "")
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))

MACHINE_NAME = os.getenv("MACHINE_NAME", "Torre de Enfriamiento Industrial T-100")
