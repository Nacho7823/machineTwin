import logging
from config import LOGS_DIR

# Configurar el sistema de logs para que guarde en un archivo
logging.basicConfig(
    filename=LOGS_DIR / "app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    encoding='utf-8', # Añadir codificación UTF-8 explícita
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
