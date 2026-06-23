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

DEFAULT_TREND_WINDOW = 50
MIN_TREND_WINDOW = 2
MAX_TREND_WINDOW = 200


def _leer_estado_actual() -> dict | None:
    current_path = DATA_DIR / "machine_current.json"
    if not current_path.exists():
        return None
    text = read_text_with_fallback(current_path)
    return json.loads(text)


def _leer_json(path):
    return json.loads(read_text_with_fallback(path))


def _discover_machine_data() -> list[dict]:
    machines = []
    if not DATA_DIR.exists():
        return machines

    for machine_dir in sorted(DATA_DIR.iterdir()):
        if not machine_dir.is_dir():
            continue
        current_path = machine_dir / "machine_current.json"
        history_path = machine_dir / "operation_history.csv"
        events_path = machine_dir / "event_history.csv"
        if not any(path.exists() for path in (current_path, history_path, events_path)):
            continue
        current = _leer_json(current_path) if current_path.exists() else {}
        machines.append(
            {
                "key": machine_dir.name,
                "dir": machine_dir,
                "current_path": current_path,
                "history_path": history_path,
                "events_path": events_path,
                "current": current,
            }
        )

    if machines:
        return machines

    current_path = DATA_DIR / "machine_current.json"
    history_path = DATA_DIR / "operation_history.csv"
    events_path = DATA_DIR / "event_history.csv"
    if any(path.exists() for path in (current_path, history_path, events_path)):
        current = _leer_json(current_path) if current_path.exists() else {}
        machines.append(
            {
                "key": "legacy",
                "dir": DATA_DIR,
                "current_path": current_path,
                "history_path": history_path,
                "events_path": events_path,
                "current": current,
            }
        )

    return machines


def _machine_name(machine: dict) -> str:
    current = machine.get("current", {})
    return current.get("machine_name") or machine.get("key", "maquina")


def _machine_id(machine: dict) -> str:
    current = machine.get("current", {})
    return current.get("machine_id", machine.get("key", "sin id"))


def _config_por_maquina(machine: dict) -> dict | None:
    current = machine.get("current", {})
    config = _config_por_estado(current) if current else None
    if config:
        return config
    return MACHINE_CONFIGS.get(machine.get("key", ""))


def _format_estado_actual(machine: dict) -> list[str]:
    current = machine.get("current", {})
    lines = [
        f"Maquina: {_machine_name(machine)}",
        f"ID: {_machine_id(machine)}",
        f"Tipo: {current.get('machine_type', 'sin tipo')}",
        f"Estado operativo: {current.get('status', 'sin estado')}",
        "Variables actuales:",
    ]

    variables = current.get("current_variables", {})
    if not variables:
        lines.append("- No hay variables actuales registradas.")
        return lines

    for name, data in variables.items():
        value = data.get("value", "sin dato")
        unit = data.get("unit", "")
        lines.append(f"- {name}: {value} {unit}".rstrip())
    return lines


def _trend_for_series(series, variable: str) -> str:
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


def _normalizar_ventana_tendencia(value: int) -> tuple[int, str | None]:
    try:
        requested = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TREND_WINDOW, f"Ventana invalida. Se uso la ventana por defecto de {DEFAULT_TREND_WINDOW} muestras."

    if requested < MIN_TREND_WINDOW:
        return MIN_TREND_WINDOW, f"Ventana solicitada: {requested}. Se uso el minimo permitido de {MIN_TREND_WINDOW} muestras."
    if requested > MAX_TREND_WINDOW:
        return MAX_TREND_WINDOW, f"Ventana solicitada: {requested}. Se uso el maximo permitido de {MAX_TREND_WINDOW} muestras."
    return requested, None



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
    """Obtiene el estado operativo actual de las maquinas y sus variables medidas."""
    logger.info("Se ejecuto la herramienta 'obtener_estado_actual'")
    machines = [machine for machine in _discover_machine_data() if machine.get("current")]
    if not machines:
        return "No hay datos actuales disponibles."

    sections = ["\n".join(_format_estado_actual(machine)) for machine in machines]
    return "\n\n".join(sections)


@tool
def consultar_eventos_recientes(limit: int = 10) -> str:
    """Consulta los eventos, alertas, fallas o mantenimientos mas recientes de las maquinas."""
    logger.info(f"Se ejecuto la herramienta 'consultar_eventos_recientes' con limit={limit}")
    event_frames = []
    for machine in _discover_machine_data():
        events_path = machine["events_path"]
        if not events_path.exists():
            continue
        try:
            df = read_csv_with_fallback(events_path)
        except Exception as e:
            return f"No se pudieron leer los eventos de {_machine_name(machine)}: {type(e).__name__}: {e}"
        if df.empty:
            continue
        df = df.copy()
        df["machine_name"] = _machine_name(machine)
        event_frames.append(df)

    if not event_frames:
        return "No hay eventos registrados."

    df = pd.concat(event_frames, ignore_index=True)
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp")
    limit = _limitar_entero(limit, 1, 50)
    rows = df.tail(limit).iloc[::-1]
    lines = [f"Eventos recientes (ultimos {len(rows)}):"]
    for _, row in rows.iterrows():
        machine_name = row.get("machine_name", "sin maquina")
        event_id = row.get("event_id", "sin id")
        timestamp = row.get("timestamp", "sin fecha")
        event_type = row.get("event_type", "sin tipo")
        severity = row.get("severity", "sin severidad")
        description = row.get("description", "sin descripcion")
        lines.append(
            f"- {timestamp} | maquina={machine_name} | {event_id} | tipo={event_type} | severidad={severity} | "
            f"{description}"
        )

    return "\n".join(lines)


@tool
def detectar_fuera_de_limites() -> str:
    """Detecta variables actuales fuera de rango optimo u operativo segun la configuracion de las maquinas."""
    logger.info("Se ejecuto la herramienta 'detectar_fuera_de_limites'")
    machines = [machine for machine in _discover_machine_data() if machine.get("current")]
    if not machines:
        return "No hay datos actuales disponibles para analizar limites."

    sections = []
    for machine in machines:
        current = machine.get("current", {})
        config = _config_por_maquina(machine)
        if not config:
            sections.append(f"No se encontro configuracion para la maquina {_machine_id(machine)}.")
            continue

        current_variables = current.get("current_variables", {})
        config_variables = config.get("variables", {})
        lines = [f"Analisis de limites para {_machine_name(machine)}:"]

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
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


@tool
def analizar_tendencia(variable: str, ventana: int = DEFAULT_TREND_WINDOW) -> str:
    """Analiza la tendencia reciente de una variable. Usa 50 muestras por defecto y hasta 200."""
    logger.info(f"Se ejecuto la herramienta 'analizar_tendencia' con variable={variable}, ventana={ventana}")
    machines = _discover_machine_data()
    if not machines:
        return "No hay historial de operacion disponible."

    sections = []
    missing_variables = []
    ventana, window_note = _normalizar_ventana_tendencia(ventana)
    for machine in machines:
        history_path = machine["history_path"]
        if not history_path.exists():
            continue
        try:
            df = read_csv_with_fallback(history_path)
        except Exception as e:
            return f"No se pudo leer el historial de operacion de {_machine_name(machine)}: {type(e).__name__}: {e}"

        if df.empty:
            continue
        if variable not in df.columns:
            variables = [c for c in df.columns if c != "timestamp"]
            missing_variables.append(f"{_machine_name(machine)}: {', '.join(variables)}")
            continue

        series = pd.to_numeric(df[variable], errors="coerce").dropna().tail(ventana)
        if len(series) < 2:
            sections.append(f"{_machine_name(machine)}: No hay datos suficientes para analizar la tendencia de '{variable}'.")
            continue
        sections.append(f"Maquina: {_machine_name(machine)}\n{_trend_for_series(series, variable)}")

    if sections:
        if window_note:
            return window_note + "\n\n" + "\n\n".join(sections)
        return "\n\n".join(sections)
    if missing_variables:
        return f"La variable '{variable}' no existe en los historiales revisados. Variables disponibles por maquina: " + "; ".join(missing_variables) + "."
    return "No hay historial de operacion disponible."


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
