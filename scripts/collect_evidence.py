from __future__ import annotations

import argparse
import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "docs" / "evidencia_entrega3"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _run(command: list[str], cwd: Path = BASE_DIR) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read().decode("utf-8")
            return {
                "url": url,
                "status": response.status,
                "json": json.loads(body),
            }
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "error": e.read().decode("utf-8", errors="replace")}
    except Exception as e:
        return {"url": url, "status": None, "error": f"{type(e).__name__}: {e}"}


def _write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def collect(base_url: str, output_dir: Path) -> Path:
    run_dir = output_dir / _timestamp()
    run_dir.mkdir(parents=True, exist_ok=True)

    _write_json(run_dir / "docker_compose_ps.json", _run(["docker", "compose", "ps"]))
    _write_json(run_dir / "docker_compose_config.json", _run(["docker", "compose", "config"]))
    _write_json(run_dir / "db_status.json", _run([".venv/bin/python", "-m", "db", "status"]))

    conversations = _get_json(f"{base_url.rstrip('/')}/api/conversations")
    _write_json(run_dir / "api_conversations.json", conversations)

    traces = _get_json(f"{base_url.rstrip('/')}/api/traces?limit=20")
    _write_json(run_dir / "api_traces.json", traces)

    conversation_id = None
    for conversation in conversations.get("json", {}).get("conversations", []):
        if conversation.get("conversation_id"):
            conversation_id = conversation["conversation_id"]
            break

    if conversation_id:
        detail = _get_json(f"{base_url.rstrip('/')}/api/traces/{conversation_id}")
        _write_json(run_dir / f"api_trace_detail_{conversation_id}.json", detail)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "conversation_id": conversation_id,
        "files": sorted(path.name for path in run_dir.iterdir() if path.is_file()),
    }
    _write_json(run_dir / "manifest.json", manifest)
    print(f"Evidencia guardada en: {run_dir}")
    return run_dir


def main():
    parser = argparse.ArgumentParser(description="Recolecta evidencia tecnica para Entrega 3.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="URL base del backend web.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directorio donde guardar evidencia.")
    args = parser.parse_args()

    collect(base_url=args.base_url, output_dir=Path(args.output_dir))


if __name__ == "__main__":
    main()
