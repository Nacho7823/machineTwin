import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "machines.json"

def _load_configs() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

MACHINE_CONFIGS = _load_configs()


def get_machine_list():
    return [
        {"id": k, "name": v["name"], "type": v["type"], "description": v["description"]}
        for k, v in MACHINE_CONFIGS.items()
    ]


def get_machine_config(machine_type: str):
    return MACHINE_CONFIGS.get(machine_type)