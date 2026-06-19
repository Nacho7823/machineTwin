import io
import json
import contextlib

import pandas as pd
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
            

@tool
def ejecutar_codigo(code: str) -> str:
    """Ejecuta codigo python para hacer estadisticas sobre los datos.

Variables YA CARGADAS y disponibles en el scope (NO es necesario cargar archivos ni incrustar datos):
  - machine_current (dict): Estado actual de la maquina. Estructura:
      machine_current["machine_id"], machine_current["machine_name"], machine_current["status"]
      machine_current["current_variables"]["temperature"]["value"]  (y .unit)
      machine_current["current_variables"]["vibration"]["value"]
      machine_current["current_variables"]["pressure"]["value"]
      machine_current["current_variables"]["flow_rate"]["value"]
      machine_current["current_variables"]["power_consumption"]["value"]
      machine_current["current_variables"]["efficiency"]["value"]
  - machine_history (pd.DataFrame): Historial de operaciones. Columnas: timestamp, temperature, vibration, pressure, flow_rate, power_consumption, efficiency.
  - pd: pandas ya importado.

Escribe SOLO el codigo analitico. Usa print() para mostrar resultados."""
    logger.info(f"Se ejecuto la herramienta 'ejecutar_codigo' con el siguiente codigo: {code}")

    try:
        # Cargar datos actuales
        current_path = DATA_DIR / "machine_current.json"
        machine_current = {}
        if current_path.exists():
            machine_current = json.loads(current_path.read_text(encoding="utf-8"))

        # Cargar historial
        history_path = DATA_DIR / "operation_history.csv"
        machine_history = pd.DataFrame()
        if history_path.exists():
            machine_history = pd.read_csv(history_path)

        # Ejecutar codigo con las variables disponibles y capturar stdout
        stdout_capture = io.StringIO()
        local_vars = {
            "machine_current": machine_current,
            "machine_history": machine_history,
            "pd": pd,
        }

        with contextlib.redirect_stdout(stdout_capture):
            exec(code, {"__builtins__": __builtins__}, local_vars)

        output = stdout_capture.getvalue().strip()
        if not output:
            return "Codigo ejecutado exitosamente sin salida."
        return output

    except Exception as e:
        logger.error(f"Error al ejecutar la herramienta 'ejecutar_codigo': {e}")
        return f"Error al ejecutar el codigo: {type(e).__name__}: {e}"
