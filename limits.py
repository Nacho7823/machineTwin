from simulator.machine_configs import MACHINE_CONFIGS


def classify_machine_limits(machine_key: str, current: dict) -> dict[str, dict]:
    config = MACHINE_CONFIGS.get(machine_key, {})
    configured_variables = config.get("variables", {})
    current_variables = current.get("current_variables", {}) if current else {}
    result = {}

    for variable_name, variable_config in configured_variables.items():
        measured = current_variables.get(variable_name, {})
        raw_value = measured.get("value")
        unit = measured.get("unit", variable_config.get("unit", ""))
        entry = {
            "label": variable_config.get("label", variable_name),
            "value": raw_value,
            "unit": unit,
            "optimal_min": variable_config.get("optimal_min"),
            "optimal_max": variable_config.get("optimal_max"),
            "operational_min": variable_config.get("min"),
            "operational_max": variable_config.get("max"),
            "state": "sin_datos",
        }

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            result[variable_name] = entry
            continue

        min_value = variable_config.get("min")
        max_value = variable_config.get("max")
        optimal_min = variable_config.get("optimal_min")
        optimal_max = variable_config.get("optimal_max")

        if min_value is not None and max_value is not None and not (min_value <= value <= max_value):
            entry["state"] = "fuera_rango_operativo"
        elif optimal_min is not None and optimal_max is not None and not (optimal_min <= value <= optimal_max):
            entry["state"] = "fuera_rango_optimo"
        else:
            entry["state"] = "normal"
        result[variable_name] = entry

    for variable_name, measured in current_variables.items():
        if variable_name in result:
            continue
        result[variable_name] = {
            "label": variable_name,
            "value": measured.get("value"),
            "unit": measured.get("unit", ""),
            "optimal_min": None,
            "optimal_max": None,
            "operational_min": None,
            "operational_max": None,
            "state": "sin_datos",
        }

    return result
