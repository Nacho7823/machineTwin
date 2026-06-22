from fileinput import filename
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
        for p in DATA_DIR.rglob("*"):
            if p.is_file():
                files.append(
                    f"- {p.relative_to(DATA_DIR)} ({p.stat().st_size} bytes)")
    if not files:
        return "No se encontraron archivos en la carpeta de datos."
    return "\n".join(files)


@tool
def leer_archivo_datos(filename: str) -> str:
    """Lee y devuelve el contenido completo de un archivo específico de la carpeta de datos por su nombre."""
    logger.info(f"Se ejecuto la herramienta 'leer_archivo_datos' para el archivo: '{filename}'")
    
    file_path = (DATA_DIR / filename).resolve()

    if not str(file_path).startswith(str(DATA_DIR.resolve())):
        return "Ruta inválida."

    if not file_path.exists():
        return f"El archivo '{filename}' no existe."
    return file_path.read_text(encoding='utf-8')
            

@tool
def ejecutar_codigo(code: str) -> str:
    """Ejecuta código Python para realizar análisis y estadísticas sobre los datos.

Variables YA CARGADAS y disponibles en el scope:

- machines (dict):
    machines["cooling_tower"]["current"] -> dict con estado actual
    machines["cooling_tower"]["history"] -> pd.DataFrame con historial

    machines["electric_motor"]["current"] -> dict con estado actual
    machines["electric_motor"]["history"] -> pd.DataFrame con historial

    machines["compressor"]["current"] -> dict con estado actual
    machines["compressor"]["history"] -> pd.DataFrame con historial

- pd: pandas ya importado.

Ejemplos:

    print(machines.keys())

    print(
        machines["compressor"]["history"]["temperature"].mean()
    )

    for machine, data in machines.items():
        print(machine, len(data["history"]))

Escribe SOLO el código analítico. Usa print() para mostrar resultados.
"""
    logger.info(
        f"Se ejecuto la herramienta 'ejecutar_codigo' con el siguiente codigo: {code}"
    )

    try:
        machines = {}

        if DATA_DIR.exists():
            for machine_dir in DATA_DIR.iterdir():

                if not machine_dir.is_dir():
                    continue

                current_file = machine_dir / "machine_current.json"
                history_file = machine_dir / "operation_history.csv"

                machine_current = {}
                machine_history = pd.DataFrame()

                if current_file.exists():
                    try:
                        machine_current = json.loads(
                            current_file.read_text(encoding="utf-8")
                        )
                    except UnicodeDecodeError:
                        machine_current = json.loads(
                            current_file.read_text(encoding="latin-1")
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error leyendo {current_file}: {e}"
                        )

                if history_file.exists():
                    try:
                        machine_history = pd.read_csv(history_file)
                    except Exception as e:
                        logger.warning(
                            f"Error leyendo {history_file}: {e}"
                        )

                machines[machine_dir.name] = {
                    "current": machine_current,
                    "history": machine_history,
                }

        stdout_capture = io.StringIO()

        local_vars = {
            "machines": machines,
            "pd": pd,
        }

        with contextlib.redirect_stdout(stdout_capture):
            exec(
                code,
                {"__builtins__": __builtins__},
                local_vars,
            )

        output = stdout_capture.getvalue().strip()

        if not output:
            return "Codigo ejecutado exitosamente sin salida."

        return output

    except Exception as e:
        logger.error(
            f"Error al ejecutar la herramienta 'ejecutar_codigo': {e}"
        )
        return (
            f"Error al ejecutar el codigo: "
            f"{type(e).__name__}: {e}"
        )