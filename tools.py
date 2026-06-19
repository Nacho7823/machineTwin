from log import get_logger
from langchain_core.tools import tool
from config import DATA_DIR
from rag.nativeRAG import query

logger = get_logger(__name__)



@tool
def consultar_documentacion(q: str) -> str:
    """Consulta la documentación del sistema utilizando RAG para responder preguntas o buscar información."""
    logger.info(f"Se ejecuto la herramienta 'consultar_documentacion' con query: '{q}'")
    try:
        resultados = query(q)
        if not resultados:
            return "No se encontraron documentos relevantes."
        contexto_partes = [
            f'[{i+1}] ({r["metadata"]["titulo"]}): {r["document"]}'
            for i, r in enumerate(resultados)
        ]
        resultado = '\n\n'.join(contexto_partes)
        logger.info(f"Herramienta 'consultar_documentacion' devolvio un resultado exitoso (longitud: {len(resultado)}).")
        return resultado
    except Exception as e:
        logger.error(f"Error al ejecutar la herramienta 'consultar_documentacion': {e}")
        raise e


@tool
def listar_archivos_datos() -> str:
    """Lista los nombres y tamaños de los archivos disponibles en la carpeta de datos."""
    logger.info("Se ejecuto la herramienta 'listar_archivos_datos'")
    files = []
    if DATA_DIR.exists():
        for p in DATA_DIR.iterdir():
            if p.is_file():
                files.append(f"- {p.name} ({p.stat().st_size} bytes)")
                
    if not files:
        return "No se encontraron archivos en la carpeta de datos."
    return "\n".join(files)


@tool
def leer_archivo_datos(filename: str) -> str:
    """Lee y devuelve el contenido completo de un archivo específico de la carpeta de datos por su nombre."""
    logger.info(f"Se ejecuto la herramienta 'leer_archivo_datos' para el archivo: '{filename}'")
    
    file_path = (DATA_DIR / filename).resolve()
    if not file_path.exists():
        logger.warning(f"El archivo {filename} no existe en {DATA_DIR}.")
        return f"El archivo '{filename}' no existe en la carpeta de datos."
        
    return file_path.read_text(encoding='utf-8')
            

