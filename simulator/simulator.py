import asyncio
import json
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd
from sklearn import base
from machine_configs import MACHINE_CONFIGS, get_machine_config

try:
    from utils import read_csv_with_fallback, read_text_with_fallback
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from utils import read_csv_with_fallback, read_text_with_fallback


class MachineSimulator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.mode = "normal"
        self.interval = 3
        self.machine_type = "cooling_tower"
        self.variables = {}
        self._task: Optional[asyncio.Task] = None
        self._start_time: Optional[datetime] = None
        self._data_points_generated = 0
        self._events_generated = 0
        self._degradation_step = 0
        self._failure_counter = 0
        self._live_data: list = []
        self._max_live_points = 50
        self._set_machine("cooling_tower")
        self.failure_config = {
            "enabled": True,
            "base_probability": 0.08,  # 8% por ciclo
            "severity_weights": {
            "low": 0.6,
            "medium": 0.3,
            "high": 0.1
            }
        }
    def _random_severity(self):
        severities = list(self.failure_config["severity_weights"].keys())
        weights = list(self.failure_config["severity_weights"].values())
        return random.choices(severities, weights=weights, k=1)[0]


    def _random_variable(self):
        return random.choice(list(self.variables.keys()))


    def _failure_probability(self):
        base = self.failure_config["base_probability"]

        mode_factor = {
            "normal": 1.0,
            "degradation": 2.0,
            "alert": 3.0,
            "failure": 5.0,
            "maintenance": 0.1
            }
        return min(1.0, base * mode_factor.get(self.mode, 1.0))


    def _maybe_inject_random_failure(self):
            if not self.failure_config["enabled"]:
                return

            if not self.variables:
                return

            if random.random() > self._failure_probability():
                return

            var = self._random_variable()
            severity = self._random_severity()

            self.inject_anomaly(var, severity)

    def _set_machine(self, machine_type: str):
        config = get_machine_config(machine_type)
        if config:
            self.machine_type = machine_type
            self.variables = config["variables"]
            self._degradation_step = 0
            self._failure_counter = 0

    def get_machines(self):
        return [
            {"id": k, "name": v["name"], "type": v["type"], "description": v["description"]}
            for k, v in MACHINE_CONFIGS.items()
        ]

    def switch_machine(self, machine_type: str):
        was_running = self.running
        if was_running:
            self.stop()
        self._set_machine(machine_type)
        self._live_data = []
        csv_file = self.data_dir / "operation_history.csv"
        if csv_file.exists():
            csv_file.unlink()
        if was_running:
            self.start(self.interval)

    def start(self, interval: int = 3):
        if self.running:
            return
        self.running = True
        self.interval = interval
        self._start_time = datetime.now()
        self._task = asyncio.create_task(self._run())

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def set_mode(self, mode: str):
        valid = ["normal", "degradation", "alert", "failure", "maintenance"]
        if mode in valid:
            self.mode = mode
            self._degradation_step = 0
            self._failure_counter = 0

    def inject_anomaly(self, variable: str, severity: str = "medium"):
        if variable not in self.variables:
            return False
        var = self.variables[variable]
        multiplier = {"low": 1.05, "medium": 1.15, "high": 1.3}[severity]
        new_value = var["mean"] * multiplier
        self._update_current_value(variable, new_value)
        data_point = self._generate_data_point()
        self._append_data_point(data_point)
        self._inject_event(f"Anomalía inyectada en {variable} (severidad: {severity})", "alert")
        return True

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "mode": self.mode,
            "machine_type": self.machine_type,
            "interval_seconds": self.interval,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
            "data_points_generated": self._data_points_generated,
            "events_generated": self._events_generated,
            "live_data": self._live_data[-self._max_live_points:],
        }

    def get_config(self) -> dict:
        config = get_machine_config(self.machine_type)
        return {
            "machine_type": self.machine_type,
            "machine_id": config["id"],
            "machine_name": config["name"],
            "machine_type_label": config["type"],
            "description": config["description"],
            "variables": {
                k: {
                    "label": v["label"],
                    "unit": v["unit"],
                    "min": v["min"],
                    "max": v["max"],
                    "optimal_min": v["optimal_min"],
                    "optimal_max": v["optimal_max"],
                }
                for k, v in config["variables"].items()
            },
        }

    def get_live_data(self) -> list:
        return self._live_data[-self._max_live_points:]

    def get_simulator_data(self) -> dict:
        json_file = self.data_dir / "machine_current.json"
        csv_file = self.data_dir / "operation_history.csv"
        events_file = self.data_dir / "event_history.csv"

        current = {}
        if json_file.exists():
            current = json.loads(read_text_with_fallback(json_file))

        history = []
        if csv_file.exists():
            df = read_csv_with_fallback(csv_file)
            history = df.tail(100).to_dict("records")

        events = []
        if events_file.exists():
            df = read_csv_with_fallback(events_file)
            events = df.tail(20).to_dict("records")

        return {
            "machine_type": self.machine_type,
            "current": current,
            "history": history,
            "events": events,
        }

    async def _run(self):
        while self.running:
            data_point = self._generate_data_point()

            # 👇 NUEVO: fallas aleatorias
            self._maybe_inject_random_failure()

            self._append_data_point(data_point)
            self._update_current_json(data_point)

            self._data_points_generated += 1

            live_point = {"timestamp": data_point["timestamp"]}
            for k in self.variables:
                if k in data_point:
                    live_point[k] = data_point[k]

            self._live_data.append(live_point)

            if len(self._live_data) > self._max_live_points:
                self._live_data = self._live_data[-self._max_live_points:]

            await asyncio.sleep(self.interval)

    def _get_normal_value(self, var_name: str) -> float:
        var = self.variables[var_name]
        return round(float(np.clip(np.random.normal(var["mean"], var["std"]), var["min"], var["max"])), 2)

    def _get_degradation_value(self, var_name: str) -> float:
        var = self.variables[var_name]
        factor = self._degradation_step * 0.02

        if var_name == "vibration":
            base = var["mean"] + factor * 2.0
        elif var_name == "temperature":
            base = var["mean"] + factor * 1.5
        elif var_name == "efficiency":
            base = var["mean"] - factor * 0.5
        elif var_name == "power_consumption":
            base = var["mean"] + factor * 0.8
        else:
            base = var["mean"]

        noise = np.random.normal(0, var["std"] * 0.5)
        return round(float(np.clip(base + noise, var["min"], var["max"])), 2)

    def _get_alert_value(self, var_name: str) -> float:
        var = self.variables[var_name]
        target = var["optimal_max"] * 0.95 + var["optimal_max"] * 0.05 * random.random()
        noise = np.random.normal(0, var["std"] * 0.3)
        return round(float(np.clip(target + noise, var["min"], var["max"])), 2)

    def _get_failure_value(self, var_name: str) -> float:
        var = self.variables[var_name]
        return round(float(np.random.uniform(var["optimal_max"] * 1.2, var["max"])), 2)

    def _generate_data_point(self) -> dict:
        data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        if self.mode == "normal":
            for var_name in self.variables:
                data[var_name] = self._get_normal_value(var_name)

        elif self.mode == "degradation":
            self._degradation_step += 1
            for var_name in self.variables:
                data[var_name] = self._get_degradation_value(var_name)
            if self._degradation_step % 50 == 0:
                self._inject_event(f"Degradación progresiva detectada (paso {self._degradation_step})", "warning")

        elif self.mode == "alert":
            for var_name in self.variables:
                if var_name in ["vibration", "temperature", "pressure"]:
                    data[var_name] = self._get_alert_value(var_name)
                else:
                    data[var_name] = self._get_normal_value(var_name)

        elif self.mode == "failure":
            self._failure_counter += 1
            for var_name in self.variables:
                if var_name in ["vibration", "temperature"]:
                    data[var_name] = self._get_failure_value(var_name)
                else:
                    data[var_name] = self._get_normal_value(var_name)
            if self._failure_counter == 1:
                self._inject_event("FALLO DETECTADO: Valores fuera de rango", "critical")

        elif self.mode == "maintenance":
            for var_name in self.variables:
                data[var_name] = 0.0
            if self._failure_counter == 0:
                self._inject_event("Mantenimiento en curso", "info")
                self._failure_counter = 1

        return data

    def _append_data_point(self, data_point: dict):
        csv_file = self.data_dir / "operation_history.csv"
        df = pd.DataFrame([data_point])
        if csv_file.exists():
            df.to_csv(csv_file, mode="a", header=False, index=False)
        else:
            df.to_csv(csv_file, index=False)

    def _update_current_json(self, data_point: dict):
        json_file = self.data_dir / "machine_current.json"
        if json_file.exists():
            machine_data = json.loads(read_text_with_fallback(json_file))
        else:
            machine_data = {}

        machine_data["machine_id"] = get_machine_config(self.machine_type)["id"]
        machine_data["machine_name"] = get_machine_config(self.machine_type)["name"]
        machine_data["machine_type"] = get_machine_config(self.machine_type)["type"]

        if "current_variables" not in machine_data:
            machine_data["current_variables"] = {}

        for var_name, value in data_point.items():
            if var_name == "timestamp":
                continue
            if var_name in machine_data["current_variables"]:
                machine_data["current_variables"][var_name]["value"] = value
            else:
                cfg = self.variables.get(var_name, {})
                machine_data["current_variables"][var_name] = {
                    "value": value,
                    "unit": cfg.get("unit", ""),
                }

        if self.mode == "failure":
            machine_data["status"] = "critical"
        elif self.mode == "alert":
            machine_data["status"] = "alert"
        elif self.mode == "maintenance":
            machine_data["status"] = "maintenance"
        else:
            machine_data["status"] = "operational"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(machine_data, f, indent=2, ensure_ascii=False)

    def _update_current_value(self, var_name: str, value: float):
        json_file = self.data_dir / "machine_current.json"
        if json_file.exists():
            machine_data = json.loads(read_text_with_fallback(json_file))
        else:
            machine_data = {"current_variables": {}}

        if "current_variables" not in machine_data:
            machine_data["current_variables"] = {}

        cfg = self.variables.get(var_name, {})
        machine_data["current_variables"][var_name] = {
            "value": round(value, 2),
            "unit": cfg.get("unit", ""),
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(machine_data, f, indent=2, ensure_ascii=False)

    def _inject_event(self, description: str, severity: str):
        csv_file = self.data_dir / "event_history.csv"
        event = {
            "event_id": f"EVT-SIM-{self._events_generated + 1:04d}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": severity if severity in ["maintenance", "failure", "alert", "inspection", "repair"] else "alert",
            "description": description,
            "severity": severity,
            "resolved": False,
            "technician": "Simulador",
        }
        df = pd.DataFrame([event])
        if csv_file.exists():
            df.to_csv(csv_file, mode="a", header=False, index=False)
        else:
            df.to_csv(csv_file, index=False)
        self._events_generated += 1

async def main(interval: int):
    sim1 = MachineSimulator(Path("data/cooling_tower"))
    sim2 = MachineSimulator(Path("data/electric_motor"))
    sim3 = MachineSimulator(Path("data/compressor"))

    sim1._set_machine("cooling_tower")
    sim2._set_machine("electric_motor")
    sim3._set_machine("compressor")

    sim1.running = True
    sim2.running = True
    sim3.running = True

    sim1.interval = interval
    sim2.interval = interval
    sim3.interval = interval

    print(
        f"Iniciando {sim1.machine_type} "
        f"(datos: {sim1.data_dir.absolute()})"
    )

    print(
        f"Iniciando {sim2.machine_type} "
        f"(datos: {sim2.data_dir.absolute()})"
    )

    print(
        f"Iniciando {sim3.machine_type} "
        f"(datos: {sim3.data_dir.absolute()})"
    )

    await asyncio.gather(
        sim1._run(),
        sim2._run(),
        sim3._run(),
    )


if __name__ == "__main__":
    import sys

    interval = 3

    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(
                "El intervalo debe ser un número entero. "
                "Usando el valor predeterminado de 3 segundos."
            )

    try:
        asyncio.run(main(interval))
    except KeyboardInterrupt:
        print("\nSimuladores detenidos por el usuario.")
