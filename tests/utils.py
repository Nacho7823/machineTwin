import json
import os
import re
from datetime import datetime, timedelta

from simulator.machine_configs import MACHINE_CONFIGS


def _machine_key_from_current(machine_current: dict) -> str:
    machine_id = machine_current.get("machine_id", "")
    if "T-100" in machine_id:
        return "cooling_tower"
    if "C-300" in machine_id:
        return "compressor"
    if "M-200" in machine_id:
        return "electric_motor"
    return machine_id.lower().replace("-", "_") or "unknown"


def _default_machine_current(machine_key: str, machine_config: dict) -> dict:
    return {
        "machine_id": machine_config["id"],
        "machine_name": machine_config["name"],
        "machine_type": machine_config["type"],
        "current_variables": {
            variable: {
                "value": spec["mean"],
                "unit": spec["unit"],
            }
            for variable, spec in machine_config["variables"].items()
        },
        "status": "operational",
    }


def _default_operation_history(machine_config: dict) -> str:
    variables = list(machine_config["variables"].keys())
    rows = [",".join(["timestamp", *variables])]
    start = datetime(2026, 6, 27, 7, 0, 0)
    for i in range(3):
        timestamp = (start + timedelta(minutes=10 * i)).strftime("%Y-%m-%d %H:%M:%S")
        values = [str(machine_config["variables"][variable]["mean"]) for variable in variables]
        rows.append(",".join([timestamp, *values]))
    return "\n".join(rows)


def _empty_event_history() -> str:
    return "event_id,timestamp,event_type,description,severity,resolved,technician"


def _default_machine_archives() -> dict:
    return {
        machine_key: {
            "machine_current.json": _default_machine_current(machine_key, machine_config),
            "operation_history.csv": _default_operation_history(machine_config),
            "event_history.csv": _empty_event_history(),
        }
        for machine_key, machine_config in MACHINE_CONFIGS.items()
    }


def load_folder(folder_path):
    folder_path = os.path.abspath(folder_path)
    with open(os.path.join(folder_path, "test.json"), "r") as f:
        test_config = json.load(f)

    archives = test_config["archives"]
    user_query = test_config.get("user_queries", test_config.get("user_query", ""))
    expected_output = test_config.get("expected_output", "")
    data_folder = folder_path
    if test_config.get("source_case"):
        data_folder = os.path.join(os.path.dirname(folder_path), test_config["source_case"])

    data = {}
    with open(os.path.join(data_folder, "sim_data/event_history.csv"), "r") as f:
        data["event_history.csv"] = f.read().strip()
    with open(os.path.join(data_folder, "sim_data/machine_current.json"), "r") as f:
        data["machine_current.json"] = json.load(f)
    with open(os.path.join(data_folder, "sim_data/operation_history.csv"), "r") as f:
        data["operation_history.csv"] = f.read().strip()

    if test_config.get("include_configured_machines"):
        machines = _default_machine_archives()
        fixture_machine_key = _machine_key_from_current(data["machine_current.json"])
        machines[fixture_machine_key] = data
        data = {"__machines__": machines}

    return {
        "rag_archives": archives,
        "sim_archives": data,
        "expected_output": expected_output,
        "expected_tools": test_config.get("expected_tools", []),
        "judge_metrics": test_config.get("judge_metrics", []),
        "minimum_score": test_config.get("minimum_score", 0.7),
    }, user_query


def parse_trace(trace: list[dict]) -> dict:
    input_query = ""
    actual_output = ""
    retrieval_outputs: list[str] = []
    tools_used: list[str] = []

    for event in trace:
        evt = event.get("event")

        if evt == "llm_request":
            for msg in reversed(event.get("messages", [])):
                if msg.get("type") == "human":
                    input_query = msg["content"]
                    break

        elif evt in ("llm_response", "empty_response_fallback"):
            resp = event.get("response", {})
            content = resp.get("content", "")
            if content:
                actual_output = content

        elif evt == "rag_retrieval":
            for chunk in event.get("rag_chunks", []):
                preview = chunk.get("preview", "")
                if preview:
                    retrieval_outputs.append(preview)

        elif evt == "tool_call":
            tool_name = event.get("tool")
            if tool_name:
                tools_used.append(tool_name)
            output = event.get("output", "")
            if output and not any(term in output for term in ["No se encontraron", "No hay datos", "No hay eventos", "Error"]):
                retrieval_outputs.append(output)

    retrieval_context = []
    for raw in retrieval_outputs:
        parts = re.split(r"\[\d+\]\s*\(.*?\):\s*", raw)
        for part in parts:
            chunk = part.strip()
            if chunk:
                retrieval_context.append(chunk)

    return {
        "input": input_query,
        "actual_output": actual_output,
        "retrieval_context": retrieval_context,
        "tools_used": tools_used,
    }
