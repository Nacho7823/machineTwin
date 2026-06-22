from fileinput import filename
import io
import json
import contextlib

import pandas as pd
from log import get_logger
from langchain_core.tools import tool
from config import DATA_DIR
from utils import read_csv_with_fallback, read_text_with_fallback
from rag.nativeRAG import query
from simulator.machine_configs import MACHINE_CONFIGS

logger = get_logger(__name__)


def _leer_estado_actual() -> dict | None:
    current_path = DATA_DIR / "machine_current.json"
    if not current_path.exists():
        return None
    text = read_text_with_fallback(current_path)
    return json.loads(text)


def _config_por_estado(machine_current: dict) -> dict | None:
    machine_id = machine_current.get("machine_id")
    for config in MACHINE_CONFIGS.values():
        if config.get("id") == machine_id:
            return config
    return None


def _limitar_entero(value: int, minimo: int, maximo: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = minimo
    return max(minimo, min(value, maximo))



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
def obtener_estado_actual() -> str:
    """Obtiene el estado operativo actual de la maquina y sus variables medidas."""
    logger.info("Se ejecuto la herramienta 'obtener_estado_actual'")
    machine_current = _leer_estado_actual()
    if not machine_current:
        return "No hay datos actuales disponibles."

    lines = [
        f"Maquina: {machine_current.get('machine_name', 'sin nombre')}",
        f"ID: {machine_current.get('machine_id', 'sin id')}",
        f"Tipo: {machine_current.get('machine_type', 'sin tipo')}",
        f"Estado operativo: {machine_current.get('status', 'sin estado')}",
        "Variables actuales:",
    ]

    variables = machine_current.get("current_variables", {})
    if not variables:
        lines.append("- No hay variables actuales registradas.")
        return "\n".join(lines)

    for name, data in variables.items():
        value = data.get("value", "sin dato")
        unit = data.get("unit", "")
        lines.append(f"- {name}: {value} {unit}".rstrip())

    return "\n".join(lines)


@tool
def consultar_eventos_recientes(limit: int = 10) -> str:
    """Consulta los eventos, alertas, fallas o mantenimientos mas recientes de la maquina."""
    logger.info(f"Se ejecuto la herramienta 'consultar_eventos_recientes' con limit={limit}")
    events_path = DATA_DIR / "event_history.csv"
    if not events_path.exists():
        return "No hay eventos registrados."

    try:
        df = read_csv_with_fallback(events_path)
    except Exception as e:
        return f"No se pudieron leer los eventos: {type(e).__name__}: {e}"

    if df.empty:
        return "No hay eventos registrados."

    limit = _limitar_entero(limit, 1, 50)
    rows = df.tail(limit).iloc[::-1]
    lines = [f"Eventos recientes (ultimos {len(rows)}):"]
    for _, row in rows.iterrows():
        event_id = row.get("event_id", "sin id")
        timestamp = row.get("timestamp", "sin fecha")
        event_type = row.get("event_type", "sin tipo")
        severity = row.get("severity", "sin severidad")
        description = row.get("description", "sin descripcion")
        resolved = row.get("resolved", "sin dato")
        lines.append(
            f"- {timestamp} | {event_id} | tipo={event_type} | severidad={severity} | "
            f"resuelto={resolved} | {description}"
        )

    return "\n".join(lines)


@tool
def detectar_fuera_de_limites() -> str:
    """Detecta variables actuales fuera de rango optimo u operativo segun la configuracion de la maquina."""
    logger.info("Se ejecuto la herramienta 'detectar_fuera_de_limites'")
    machine_current = _leer_estado_actual()
    if not machine_current:
        return "No hay datos actuales disponibles para analizar limites."

    config = _config_por_estado(machine_current)
    if not config:
        return f"No se encontro configuracion para la maquina {machine_current.get('machine_id', 'sin id')}."

    current_variables = machine_current.get("current_variables", {})
    config_variables = config.get("variables", {})
    lines = [
        f"Analisis de limites para {machine_current.get('machine_name', config.get('name', 'maquina'))}:"
    ]

    for name, cfg in config_variables.items():
        data = current_variables.get(name)
        if not data or data.get("value") is None:
            lines.append(
                f"- {name}: sin datos | optimo=[{cfg['optimal_min']}, {cfg['optimal_max']}] "
                f"| operativo=[{cfg['min']}, {cfg['max']}] | estado=sin_datos"
            )
            continue

        value = float(data.get("value"))
        unit = data.get("unit", cfg.get("unit", ""))
        if value < cfg["min"] or value > cfg["max"]:
            status = "fuera_rango_operativo"
        elif value < cfg["optimal_min"] or value > cfg["optimal_max"]:
            status = "fuera_rango_optimo"
        else:
            status = "normal"

        lines.append(
            f"- {name}: {value} {unit} | optimo=[{cfg['optimal_min']}, {cfg['optimal_max']}] "
            f"| operativo=[{cfg['min']}, {cfg['max']}] | estado={status}"
        )

    return "\n".join(lines)


@tool
def analizar_tendencia(variable: str, ventana: int = 20) -> str:
    """Analiza la tendencia reciente de una variable usando el historial de operacion."""
    logger.info(f"Se ejecuto la herramienta 'analizar_tendencia' con variable={variable}, ventana={ventana}")
    history_path = DATA_DIR / "operation_history.csv"
    if not history_path.exists():
        return "No hay historial de operacion disponible."

    try:
        df = read_csv_with_fallback(history_path)
    except Exception as e:
        return f"No se pudo leer el historial de operacion: {type(e).__name__}: {e}"

    if df.empty:
        return "No hay historial de operacion disponible."
    if variable not in df.columns:
        variables = [c for c in df.columns if c != "timestamp"]
        return f"La variable '{variable}' no existe en el historial. Variables disponibles: {', '.join(variables)}."

    series = pd.to_numeric(df[variable], errors="coerce").dropna()
    ventana = _limitar_entero(ventana, 2, 200)
    series = series.tail(ventana)
    if len(series) < 2:
        return f"No hay datos suficientes para analizar la tendencia de '{variable}'."

    initial = float(series.iloc[0])
    final = float(series.iloc[-1])
    absolute_change = final - initial
    percent_change = 0.0 if initial == 0 else (absolute_change / initial) * 100

    if percent_change > 1:
        trend = "sube"
    elif percent_change < -1:
        trend = "baja"
    else:
        trend = "estable"

    return "\n".join(
        [
            f"Variable analizada: {variable}",
            f"Cantidad de muestras: {len(series)}",
            f"Valor inicial: {round(initial, 3)}",
            f"Valor final: {round(final, 3)}",
            f"Variacion absoluta: {round(absolute_change, 3)}",
            f"Variacion porcentual: {round(percent_change, 2)}%",
            f"Tendencia: {trend}",
        ]
    )


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

    return read_text_with_fallback(file_path)
            

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
                        machine_current = json.loads(read_text_with_fallback(current_file))
                    except Exception as e:
                        logger.warning(
                            f"Error leyendo {current_file}: {e}"
                        )

                if history_file.exists():
                    try:
                        machine_history = read_csv_with_fallback(history_file)
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
