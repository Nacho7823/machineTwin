from limits import classify_machine_limits


def test_classify_machine_limits_marks_normal_optimal_values():
    current = {
        "current_variables": {
            "temperature": {"value": 42.0, "unit": "°C"},
            "vibration": {"value": 2.0, "unit": "mm/s"},
        }
    }

    result = classify_machine_limits("cooling_tower", current)

    assert result["temperature"]["state"] == "normal"
    assert result["vibration"]["state"] == "normal"


def test_classify_machine_limits_distinguishes_optimal_and_operational_ranges():
    current = {
        "current_variables": {
            "temperature": {"value": 55.0, "unit": "°C"},
            "pressure": {"value": 3.4, "unit": "bar"},
            "flow_rate": {"value": None, "unit": "L/min"},
        }
    }

    result = classify_machine_limits("cooling_tower", current)

    assert result["temperature"]["state"] == "fuera_rango_optimo"
    assert result["pressure"]["state"] == "fuera_rango_operativo"
    assert result["flow_rate"]["state"] == "sin_datos"


def test_classify_machine_limits_reports_missing_variables():
    current = {"current_variables": {"temperature": {"value": 42.0, "unit": "°C"}}}

    result = classify_machine_limits("cooling_tower", current)

    assert result["temperature"]["state"] == "normal"
    assert result["efficiency"]["state"] == "sin_datos"
