import json
import os
import re


def load_folder(folder_path):
    with open(os.path.join(folder_path, "test.json"), "r") as f:
        test_config = json.load(f)

    archives = test_config["archives"]
    user_query = test_config["user_query"]
    expected_output = test_config.get("expected_output", "")

    data = {}
    with open(os.path.join(folder_path, "sim_data/event_history.csv"), "r") as f:
        data["event_history.csv"] = f.read().strip()
    with open(os.path.join(folder_path, "sim_data/machine_current.json"), "r") as f:
        data["machine_current.json"] = json.load(f)
    with open(os.path.join(folder_path, "sim_data/operation_history.csv"), "r") as f:
        data["operation_history.csv"] = f.read().strip()

    return {
        "rag_archives": archives,
        "sim_archives": data,
        "expected_output": expected_output,
    }, user_query


def parse_trace(trace: list[dict]) -> dict:
    input_query = ""
    actual_output = ""
    retrieval_outputs: list[str] = []

    for event in trace:
        evt = event.get("event")

        if evt == "llm_request":
            for msg in reversed(event.get("messages", [])):
                if msg.get("type") == "human":
                    input_query = msg["content"]
                    break

        elif evt == "llm_response":
            resp = event.get("response", {})
            content = resp.get("content", "")
            if content:
                actual_output = content

        elif evt == "tool_call" and event.get("tool") == "consultar_documentacion":
            output = event.get("output", "")
            if output and "No se encontraron" not in output:
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
    }
