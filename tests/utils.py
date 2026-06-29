import json
import os
import re


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
