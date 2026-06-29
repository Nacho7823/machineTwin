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
DEFAULT_SYSTEM_PROMPT_VERSION = "0.0.2"


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    value = _env(name)
    return float(value) if value else default


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    return int(value) if value else default


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _resolve_system_prompt() -> tuple[Path, str]:
    explicit_path = _env("SYSTEM_PROMPT_PATH")
    requested_version = _env("SYSTEM_PROMPT_VERSION", DEFAULT_SYSTEM_PROMPT_VERSION) or DEFAULT_SYSTEM_PROMPT_VERSION
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


LLM_API_KEY = _env("LLM_API_KEY")
LLM_MODEL = _env("LLM_MODEL")
LLM_BASE_URL = _env("LLM_BASE_URL")
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.2)
LLM_TOP_P = _env_float("LLM_TOP_P", 1.0)
LLM_MAX_TOKENS = _env_int("LLM_MAX_TOKENS", 4096)
LLM_TIMEOUT = _env_float("LLM_TIMEOUT", 120)
LLM_MAX_RETRIES = _env_int("LLM_MAX_RETRIES", 0)
LLM_ENABLE_THINKING = _env_bool("LLM_ENABLE_THINKING", False)
LLM_REASONING_BUDGET = _env_int("LLM_REASONING_BUDGET", 0)
DATABASE_URL = _env("DATABASE_URL")
WEB_HOST = _env("WEB_HOST", "0.0.0.0")
WEB_PORT = _env_int("WEB_PORT", 8000)
