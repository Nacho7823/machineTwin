import io
import json
import contextlib

import pandas as pd
from log import get_logger, log_trace_event
from langchain_core.tools import tool
from pathlib import Path
from utils import read_csv_with_fallback, read_text_with_fallback
from rag.rag import DocumentRAG
from simulator.machine_configs import MACHINE_CONFIGS
from limits import classify_machine_limits
logger = get_logger(__name__)

DEFAULT_TREND_WINDOW = 50
MIN_TREND_WINDOW = 2
MAX_TREND_WINDOW = 200
DEFAULT_RAG_RESULTS = 6
MAX_RAG_RESULTS = 9
VARIABLE_ALIASES = {
    "temperatura": "temperature",
    "temp": "temperature",
    "vibracion": "vibration",
    "vibración": "vibration",
    "presion": "pressure",
    "presión": "pressure",
    "caudal": "flow_rate",
    "flujo": "flow_rate",
    "consumo": "power_consumption",
    "consumo de potencia": "power_consumption",
    "potencia": "power_consumption",
    "eficiencia": "efficiency",
    "corriente": "current",
}


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


def _normalizar_variable(variable: str) -> tuple[str, str | None]:
    raw = str(variable or "").strip()
    normalized = VARIABLE_ALIASES.get(raw.lower(), raw)
    if raw and normalized != raw:
        return normalized, f"Variable solicitada: '{raw}'. Se interpreto como '{normalized}'."
    return normalized, None


def _discover_machine_data(data_dir: Path) -> list[dict]:
    machines = []
    if not data_dir.exists():
        return machines
    for machine_dir in sorted(data_dir.iterdir()):
        if not machine_dir.is_dir():
            continue
        current_path = machine_dir / "machine_current.json"
        history_path = machine_dir / "operation_history.csv"
        events_path = machine_dir / "event_history.csv"
        if not any(p.exists() for p in (current_path, history_path, events_path)):
            continue
        current = {}
        if current_path.exists():
            try:
                current = json.loads(read_text_with_fallback(current_path))
            except Exception:
                pass
        machines.append({
            "name": machine_dir.name,
            "current": current,
            "history_path": history_path,
            "events_path": events_path,
        })
    return machines


def _machine_name(machine: dict) -> str:
    return machine.get("current", {}).get("machine_name", machine.get("name", "desconocida"))


def _format_estado_actual(machine: dict) -> list[str]:
    current = machine.get("current", {})
    if not current:
        return [f"{_machine_name(machine)}: sin datos actuales."]
    lines = [
        f"Maquina: {current.get('machine_name', machine['name'])}",
        f"ID: {current.get('machine_id', 'sin id')}",
        f"Tipo: {current.get('machine_type', 'sin tipo')}",
        f"Estado operativo: {current.get('status', 'sin estado')}",
        "Variables actuales:",
    ]
    variables = current.get("current_variables", {})
    if not variables:
        lines.append("- No hay variables actuales registradas.")
    else:
        for name, data in variables.items():
            value = data.get("value", "sin dato")
            unit = data.get("unit", "")
            lines.append(f"- {name}: {value} {unit}")
    return lines


def _trend_for_series(series: pd.Series, variable: str) -> str:
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
    return "\n".join([
        f"Variable analizada: {variable}",
        f"Cantidad de muestras: {len(series)}",
        f"Valor inicial: {round(initial, 3)}",
        f"Valor final: {round(final, 3)}",
        f"Variacion absoluta: {round(absolute_change, 3)}",
        f"Variacion porcentual: {round(percent_change, 2)}%",
        f"Tendencia: {trend}",
    ])


def _format_limit_entry(variable_name: str, entry: dict) -> str:
    value = entry.get("value", "sin dato")
    unit = entry.get("unit", "")
    optimal = f'{entry.get("optimal_min")}..{entry.get("optimal_max")}'
    operational = f'{entry.get("operational_min")}..{entry.get("operational_max")}'
    label = entry.get("label", variable_name)
    return (
        f"- {label} ({variable_name}): valor={value} {unit}; "
        f"estado={entry.get('state')}; optimo={optimal} {unit}; operativo={operational} {unit}"
    )


def _rag_chunk_metadata(result: dict) -> dict:
    metadata = result.get("metadata", {})
    return {
        "doc_id": metadata.get("doc_id"),
        "title": metadata.get("titulo"),
        "source_path": metadata.get("source_path"),
        "chunk_index": metadata.get("chunk_index"),
        "distance": result.get("distance"),
        "preview": str(result.get("document", ""))[:240],
    }


def _mentions_specific_machine(query: str) -> bool:
    normalized = str(query or "").lower()
    for machine_key, machine_config in MACHINE_CONFIGS.items():
        identifiers = [
            machine_key,
            machine_config.get("id", ""),
            machine_config.get("name", ""),
            machine_config.get("type", ""),
        ]
        if any(identifier and identifier.lower() in normalized for identifier in identifiers):
            return True
    return False


def _dedupe_rag_results(results: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for result in results:
        metadata = result.get("metadata", {})
        key = (
            metadata.get("source_path"),
            metadata.get("chunk_index"),
            str(result.get("document", ""))[:80],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)
    return deduped


def _document_name(result: dict) -> str:
    metadata = result.get("metadata", {})
    return metadata.get("source_path") or metadata.get("titulo") or metadata.get("doc_id") or "documento"


class TwinTools:
    def __init__(self, data_dir: Path, docs_dir: Path):
        self.data_dir = Path(data_dir)
        self.docs_dir = Path(docs_dir)
        self.rag = DocumentRAG(self.docs_dir)

    def get_tools(self) -> dict[str, any]:
        @tool
        def consultar_documentacion(q: str) -> str:
            """Consulta la documentación del sistema utilizando RAG para responder preguntas o buscar información."""
            logger.info(f"Se ejecuto la herramienta 'consultar_documentacion' con query: '{q}'")
            try:
                resultados = self.rag.query(q, k=DEFAULT_RAG_RESULTS)
                if resultados and not _mentions_specific_machine(q):
                    seen_documents = {_document_name(result) for result in resultados}
                    for machine_config in MACHINE_CONFIGS.values():
                        per_machine_query = f"{q} {machine_config['name']} {machine_config['id']}"
                        for candidate in self.rag.query(per_machine_query, k=2):
                            document_name = _document_name(candidate)
                            if document_name not in seen_documents:
                                resultados.append(candidate)
                                seen_documents.add(document_name)
                                break
                    resultados = _dedupe_rag_results(resultados)[:MAX_RAG_RESULTS]
                if not resultados:
                    log_trace_event({
                        "event": "rag_retrieval",
                        "query": q,
                        "rag_chunks": [],
                    })
                    return "No se encontraron documentos relevantes."
                rag_chunks = [_rag_chunk_metadata(r) for r in resultados]
                log_trace_event({
                    "event": "rag_retrieval",
                    "query": q,
                    "rag_chunks": rag_chunks,
                    "rag_chunk_count": len(rag_chunks),
                })
                contexto_partes = [
                    f'[{i+1}] ({r["metadata"]["titulo"]}): {r["document"]}'
                    for i, r in enumerate(resultados)
                ]
                documentos = []
                for result in resultados:
                    document_name = _document_name(result)
                    if document_name not in documentos:
                        documentos.append(document_name)
                contexto_partes.append("Documentos consultados: " + ", ".join(documentos) + ".")
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
            machines = [machine for machine in _discover_machine_data(self.data_dir) if machine.get("current")]
            if not machines:
                return "No hay datos actuales disponibles."

            sections = ["\n".join(_format_estado_actual(machine)) for machine in machines]
            return "\n\n".join(sections)

        @tool
        def consultar_eventos_recientes(limit: int = 10) -> str:
            """Consulta los eventos, alertas, fallas o mantenimientos mas recientes de las maquinas."""
            logger.info(f"Se ejecuto la herramienta 'consultar_eventos_recientes' con limit={limit}")
            event_frames = []
            machines_seen = []
            machines_with_events = set()
            for machine in _discover_machine_data(self.data_dir):
                machine_name = _machine_name(machine)
                machines_seen.append(machine_name)
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
                df["machine_name"] = machine_name
                machines_with_events.add(machine_name)
                event_frames.append(df)

            if not event_frames:
                if machines_seen:
                    return "No hay eventos registrados para las maquinas disponibles: " + ", ".join(machines_seen) + "."
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
            machines_without_events = [name for name in machines_seen if name not in machines_with_events]
            if machines_without_events:
                lines.append("Maquinas sin eventos recientes: " + ", ".join(machines_without_events) + ".")

            return "\n".join(lines)

        @tool
        def detectar_fuera_de_limites() -> str:
            """Compara las variables actuales contra rangos optimos y operativos configurados por maquina."""
            logger.info("Se ejecuto la herramienta 'detectar_fuera_de_limites'")
            machines = _discover_machine_data(self.data_dir)
            if not machines:
                return "No hay datos actuales disponibles para evaluar limites."

            sections = []
            for machine in machines:
                current = machine.get("current", {})
                machine_key = machine.get("name", "")
                if not current:
                    sections.append(f"Maquina: {_machine_name(machine)}\n- sin_datos: no hay estado actual.")
                    continue
                if machine_key not in MACHINE_CONFIGS:
                    sections.append(f"Maquina: {_machine_name(machine)}\n- sin_datos: no hay configuracion de rangos para '{machine_key}'.")
                    continue

                classified = classify_machine_limits(machine_key, current)
                lines = [f"Maquina: {_machine_name(machine)}", f"Clave: {machine_key}"]
                for variable_name, entry in classified.items():
                    lines.append(_format_limit_entry(variable_name, entry))
                sections.append("\n".join(lines))

            return "\n\n".join(sections)

        @tool
        def analizar_tendencia(variable: str, ventana: int = DEFAULT_TREND_WINDOW) -> str:
            """Analiza la tendencia reciente de una variable usando el historial de operacion."""
            logger.info(f"Se ejecuto la herramienta 'analizar_tendencia' con variable={variable}, ventana={ventana}")
            machines = _discover_machine_data(self.data_dir)
            if not machines:
                return "No hay historial de operacion disponible."

            sections = []
            missing_variables = []
            ventana, window_note = _normalizar_ventana_tendencia(ventana)
            variable, variable_note = _normalizar_variable(variable)
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
                notes = [note for note in (window_note, variable_note) if note]
                body = "\n\n".join(sections)
                if notes:
                    return "\n".join(notes) + "\n\n" + body
                return body
            if missing_variables:
                return f"La variable '{variable}' no existe en los historiales revisados. Variables disponibles por maquina: " + "; ".join(missing_variables) + "."
            return "No hay historial de operacion disponible."

        @tool
        def listar_archivos_datos() -> str:
            """Lista los nombres y tamaños de los archivos disponibles en la carpeta de datos."""
            logger.info("Se ejecuto la herramienta 'listar_archivos_datos'")
            files = []
            if self.data_dir.exists():
                for p in self.data_dir.rglob("*"):
                    if p.is_file():
                        files.append(
                            f"- {p.relative_to(self.data_dir)} ({p.stat().st_size} bytes)")
            if not files:
                return "No se encontraron archivos en la carpeta de datos."
            return "\n".join(files)

        @tool
        def leer_archivo_datos(filename: str) -> str:
            """Lee y devuelve el contenido completo de un archivo específico de la carpeta de datos por su nombre."""
            logger.info(f"Se ejecuto la herramienta 'leer_archivo_datos' para el archivo: '{filename}'")
            
            file_path = (self.data_dir / filename).resolve()

            if not str(file_path).startswith(str(self.data_dir.resolve())):
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

                if self.data_dir.exists():
                    for machine_dir in self.data_dir.iterdir():

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

        return {
            "consultar_documentacion": consultar_documentacion,
            "obtener_estado_actual": obtener_estado_actual,
            "consultar_eventos_recientes": consultar_eventos_recientes,
            "detectar_fuera_de_limites": detectar_fuera_de_limites,
            "analizar_tendencia": analizar_tendencia,
            "listar_archivos_datos": listar_archivos_datos,
            "leer_archivo_datos": leer_archivo_datos,
            "ejecutar_codigo": ejecutar_codigo,
        }
