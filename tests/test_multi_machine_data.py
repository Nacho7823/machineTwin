import importlib
import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


def _write_current(machine_dir: Path, machine_id: str, name: str, machine_type: str, temperature: float):
    machine_dir.mkdir(parents=True, exist_ok=True)
    (machine_dir / "machine_current.json").write_text(
        json.dumps(
            {
                "machine_id": machine_id,
                "machine_name": name,
                "machine_type": machine_type,
                "status": "operational",
                "current_variables": {
                    "temperature": {"value": temperature, "unit": "°C"},
                    "vibration": {"value": 2.0, "unit": "mm/s"},
                },
            }
        ),
        encoding="utf-8",
    )


def _write_history(machine_dir: Path, temperature_a: float, temperature_b: float):
    (machine_dir / "operation_history.csv").write_text(
        "timestamp,temperature,vibration\n"
        f"2026-01-01 00:00:00,{temperature_a},1.0\n"
        f"2026-01-01 00:00:01,{temperature_b},2.0\n",
        encoding="utf-8",
    )


def _write_history_values(machine_dir: Path, temperatures: list[float]):
    start = datetime(2026, 1, 1)
    rows = ["timestamp,temperature,vibration"]
    for index, temperature in enumerate(temperatures):
        timestamp = start + timedelta(minutes=index)
        rows.append(f"{timestamp:%Y-%m-%d %H:%M:%S},{temperature},1.0")
    (machine_dir / "operation_history.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _write_events(machine_dir: Path, event_id: str, description: str):
    (machine_dir / "event_history.csv").write_text(
        "event_id,timestamp,event_type,description,severity,resolved,technician\n"
        f"{event_id},2026-01-01 00:00:00,alert,{description},medium,False,Simulador\n",
        encoding="utf-8",
    )


class MultiMachineToolTests(unittest.TestCase):
    _tools_module = None

    def _load_tools_with_temp_data(self, data_dir: Path):
        if self.__class__._tools_module is None:
            import pandas  # noqa: F401

            fake_rag = types.SimpleNamespace(query=lambda _q: [])
            with patch.dict(sys.modules, {"rag.nativeRAG": fake_rag}):
                self.__class__._tools_module = importlib.import_module("tools")
        tools = self.__class__._tools_module
        tools.DATA_DIR = data_dir
        return tools

    def test_obtener_estado_actual_discovers_all_machine_subdirectories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_current(data_dir / "cooling_tower", "T-100", "Torre T-100", "Enfriamiento", 42)
            _write_current(data_dir / "electric_motor", "M-200", "Motor M-200", "Motor", 65)
            _write_current(data_dir / "compressor", "C-300", "Compresor C-300", "Compresor", 78)

            tools = self._load_tools_with_temp_data(data_dir)
            output = tools.obtener_estado_actual.invoke({})

            self.assertIn("Torre T-100", output)
            self.assertIn("Motor M-200", output)
            self.assertIn("Compresor C-300", output)

    def test_tools_keep_legacy_single_machine_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_current(data_dir, "T-100", "Torre legacy", "Enfriamiento", 42)

            tools = self._load_tools_with_temp_data(data_dir)
            output = tools.obtener_estado_actual.invoke({})

            self.assertIn("Torre legacy", output)

    def test_tendencia_and_events_are_reported_per_machine(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_current(data_dir / "cooling_tower", "T-100", "Torre T-100", "Enfriamiento", 42)
            _write_history(data_dir / "cooling_tower", 40, 44)
            _write_events(data_dir / "cooling_tower", "EVT-1", "Evento torre")
            _write_current(data_dir / "compressor", "C-300", "Compresor C-300", "Compresor", 78)
            _write_history(data_dir / "compressor", 80, 76)
            _write_events(data_dir / "compressor", "EVT-2", "Evento compresor")

            tools = self._load_tools_with_temp_data(data_dir)
            tendencia = tools.analizar_tendencia.invoke({"variable": "temperature", "ventana": 20})
            eventos = tools.consultar_eventos_recientes.invoke({"limit": 10})

            self.assertIn("Torre T-100", tendencia)
            self.assertIn("Compresor C-300", tendencia)
            self.assertIn("Tendencia: sube", tendencia)
            self.assertIn("Tendencia: baja", tendencia)
            self.assertIn("Torre T-100", eventos)
            self.assertIn("Evento torre", eventos)
            self.assertIn("Compresor C-300", eventos)
            self.assertIn("Evento compresor", eventos)
            self.assertNotIn("resuelto", eventos)
            self.assertNotIn("resolved", eventos)

    def test_tendencia_uses_50_samples_by_default_and_caps_requested_window(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_current(data_dir / "cooling_tower", "T-100", "Torre T-100", "Enfriamiento", 42)
            _write_history_values(data_dir / "cooling_tower", list(range(250)))

            tools = self._load_tools_with_temp_data(data_dir)
            default_window = tools.analizar_tendencia.invoke({"variable": "temperature"})
            capped_window = tools.analizar_tendencia.invoke({"variable": "temperature", "ventana": 500})

            self.assertIn("Cantidad de muestras: 50", default_window)
            self.assertIn("Cantidad de muestras: 200", capped_window)
            self.assertIn("maximo permitido de 200 muestras", capped_window)

    def test_limites_are_reported_per_machine_and_empty_data_is_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            _write_current(data_dir / "cooling_tower", "T-100", "Torre T-100", "Enfriamiento", 70)
            _write_current(data_dir / "electric_motor", "M-200", "Motor M-200", "Motor", 65)

            tools = self._load_tools_with_temp_data(data_dir)
            output = tools.detectar_fuera_de_limites.invoke({})

            self.assertIn("Torre T-100", output)
            self.assertIn("fuera_rango_operativo", output)
            self.assertIn("Motor M-200", output)

        with tempfile.TemporaryDirectory() as tmpdir:
            tools = self._load_tools_with_temp_data(Path(tmpdir))

            self.assertIn("No hay datos actuales", tools.obtener_estado_actual.invoke({}))


class MultiMachineSimulatorEntrypointTests(unittest.TestCase):
    def test_entrypoint_creates_one_simulator_per_configured_machine(self):
        simulator_main = importlib.import_module("simulator.main")

        with tempfile.TemporaryDirectory() as tmpdir:
            simulators = simulator_main.create_simulators(Path(tmpdir))

        machine_types = {sim.machine_type for sim in simulators}
        self.assertEqual(machine_types, {"cooling_tower", "electric_motor", "compressor"})


if __name__ == "__main__":
    unittest.main()
