import logging
import json
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import config

_trace_recorder = None
_trace_context: ContextVar[dict] = ContextVar("trace_context", default={})

# Configurar el sistema de logs para que guarde en un archivo
logging.basicConfig(
    filename=config.LOGS_DIR / "app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    encoding='utf-8', # Añadir codificación UTF-8 explícita
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def set_trace_recorder(callback):
    global _trace_recorder
    _trace_recorder = callback


@contextmanager
def trace_context(**values):
    current = dict(_trace_context.get())
    current.update({key: value for key, value in values.items() if value is not None})
    token = _trace_context.set(current)
    try:
        yield
    finally:
        _trace_context.reset(token)


def log_trace_event(payload: dict):
    try:
        config.LOGS_DIR.mkdir(exist_ok=True)
        event = dict(payload)
        for key, value in _trace_context.get().items():
            event.setdefault(key, value)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with (config.LOGS_DIR / "traces.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        if _trace_recorder:
            _trace_recorder(event)
    except Exception as e:
        logging.getLogger(__name__).warning(f"No se pudo escribir la traza estructurada: {e}")
