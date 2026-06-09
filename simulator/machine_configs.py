MACHINE_CONFIGS = {
    "cooling_tower": {
        "id": "T-100",
        "name": "Torre de Enfriamiento Industrial T-100",
        "type": "Enfriamiento Industrial",
        "description": "Torre de enfriamiento para disipación de calor en procesos industriales",
        "variables": {
            "temperature": {"label": "Temperatura", "unit": "°C", "mean": 42.0, "std": 2.0, "optimal_min": 35, "optimal_max": 50, "min": 20, "max": 60},
            "vibration": {"label": "Vibración", "unit": "mm/s", "mean": 2.0, "std": 0.3, "optimal_min": 0.5, "optimal_max": 3.0, "min": 0, "max": 5},
            "pressure": {"label": "Presión", "unit": "bar", "mean": 2.1, "std": 0.1, "optimal_min": 1.8, "optimal_max": 2.5, "min": 1.5, "max": 3.0},
            "flow_rate": {"label": "Caudal", "unit": "L/min", "mean": 150.0, "std": 5.0, "optimal_min": 120, "optimal_max": 180, "min": 100, "max": 200},
            "power_consumption": {"label": "Consumo", "unit": "kW", "mean": 45.0, "std": 2.0, "optimal_min": 35, "optimal_max": 50, "min": 30, "max": 60},
            "efficiency": {"label": "Eficiencia", "unit": "%", "mean": 92.0, "std": 1.5, "optimal_min": 85, "optimal_max": 98, "min": 80, "max": 100},
        },
    },
    "electric_motor": {
        "id": "M-200",
        "name": "Motor Eléctrico Industrial M-200",
        "type": "Motor Eléctrico",
        "description": "Motor trifásico de inducción para impulsión de bombas y compresores",
        "variables": {
            "temperature": {"label": "Temperatura", "unit": "°C", "mean": 65.0, "std": 3.0, "optimal_min": 40, "optimal_max": 80, "min": 20, "max": 120},
            "vibration": {"label": "Vibración", "unit": "mm/s", "mean": 1.5, "std": 0.3, "optimal_min": 0.3, "optimal_max": 2.5, "min": 0, "max": 4},
            "current": {"label": "Corriente", "unit": "A", "mean": 32.0, "std": 2.0, "optimal_min": 25, "optimal_max": 40, "min": 15, "max": 50},
            "rpm": {"label": "RPM", "unit": "RPM", "mean": 1450.0, "std": 20.0, "optimal_min": 1400, "optimal_max": 1500, "min": 1200, "max": 1600},
            "power_consumption": {"label": "Consumo", "unit": "kW", "mean": 22.0, "std": 1.5, "optimal_min": 18, "optimal_max": 28, "min": 10, "max": 35},
            "efficiency": {"label": "Eficiencia", "unit": "%", "mean": 89.0, "std": 2.0, "optimal_min": 82, "optimal_max": 95, "min": 70, "max": 100},
        },
    },
    "compressor": {
        "id": "C-300",
        "name": "Compresor de Tornillo C-300",
        "type": "Compresor Industrial",
        "description": "Compresor de tornillo para suministro de aire comprimido",
        "variables": {
            "temperature": {"label": "Temperatura", "unit": "°C", "mean": 78.0, "std": 3.0, "optimal_min": 60, "optimal_max": 90, "min": 30, "max": 120},
            "vibration": {"label": "Vibración", "unit": "mm/s", "mean": 2.5, "std": 0.4, "optimal_min": 0.5, "optimal_max": 3.5, "min": 0, "max": 6},
            "pressure": {"label": "Presión", "unit": "bar", "mean": 7.0, "std": 0.3, "optimal_min": 6.0, "optimal_max": 8.0, "min": 4.0, "max": 10.0},
            "flow_rate": {"label": "Caudal", "unit": "m³/min", "mean": 12.0, "std": 0.8, "optimal_min": 10, "optimal_max": 15, "min": 5, "max": 20},
            "power_consumption": {"label": "Consumo", "unit": "kW", "mean": 37.0, "std": 2.5, "optimal_min": 30, "optimal_max": 45, "min": 20, "max": 55},
            "efficiency": {"label": "Eficiencia", "unit": "%", "mean": 85.0, "std": 2.0, "optimal_min": 78, "optimal_max": 92, "min": 65, "max": 100},
        },
    },
}


def get_machine_list():
    return [
        {"id": k, "name": v["name"], "type": v["type"], "description": v["description"]}
        for k, v in MACHINE_CONFIGS.items()
    ]


def get_machine_config(machine_type: str):
    return MACHINE_CONFIGS.get(machine_type)
