from log import get_logger
from langchain_core.tools import tool
from config import DOCS_DIR
from rag import DocumentRAG

# Configurar logger
logger = get_logger(__name__)

# Inicializar RAG
rag = DocumentRAG(DOCS_DIR)


@tool
def consultar_documentacion(query: str) -> str:
    """Consulta la documentación técnica de la máquina (especificaciones, manuales, guías del TP2) para obtener información relevante sobre funcionamiento, componentes, anomalías o mantenimiento."""
    logger.info(f"Se ejecuto la herramienta 'consultar_documentacion' con query: '{query}'")
    try:
        resultado = rag.query(query)
        logger.info(f"Herramienta 'consultar_documentacion' devolvio un resultado exitoso (longitud: {len(resultado)}).")
        return resultado
    except Exception as e:
        logger.error(f"Error al ejecutar la herramienta 'consultar_documentacion': {e}")
        raise e
