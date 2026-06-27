import logging
import json
from datetime import datetime, timezone
import config

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


def log_trace_event(payload: dict):
    try:
        config.LOGS_DIR.mkdir(exist_ok=True)
        event = dict(payload)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with (config.LOGS_DIR / "traces.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logging.getLogger(__name__).warning(f"No se pudo escribir la traza estructurada: {e}")
