# Estrategia eficiente de tests automaticos

## Objetivo

Mantener cobertura funcional sobre los 20 casos de `tests/files/*` reduciendo el consumo de cuota LLM y el tiempo total de corrida. La prioridad es gastar menos llamadas del modelo; la segunda prioridad es reducir duracion.

## Diagnostico

La suite completa anterior ejecutaba hasta 4 metricas LLM-as-a-judge por caso:

- `faithfulness`
- `answer_relevance`
- `context_precision`
- `context_recall`

Con 20 casos eso podia implicar hasta 80 llamadas de juez, ademas de las llamadas del agente. En la corrida real con el modelo gratuito, la evaluacion agoto cuota a mitad de suite con `429 Rate limit exceeded`.

## Estrategia aplicada

Se mantiene la ejecucion de los 20 casos, pero se separan dos niveles:

1. Checks deterministas para todos los casos:
   - respuesta no vacia;
   - respuesta sin error de proveedor;
   - tools esperadas usadas.

2. LLM-as-a-judge solo en casos seleccionados:
   - cada `test.json` puede declarar `judge_metrics`;
   - si no declara metricas, no usa juez LLM;
   - `JUDGE_MODE=all` permite volver a la evaluacion exhaustiva.

Con la seleccion actual se ejecutan 20 metricas LLM-as-a-judge, no 80. Es una reduccion aproximada del 75% en llamadas de juez.

## Casos con LLM-as-a-judge

| Caso | Metricas |
|---|---|
| `alert_details` | `faithfulness`, `answer_relevance` |
| `conversational_memory` | `answer_relevance` |
| `current_status` | `faithfulness`, `answer_relevance` |
| `documented_operation` | `faithfulness`, `answer_relevance`, `context_precision` |
| `fail_on_temperature` | `faithfulness`, `answer_relevance` |
| `high_but_normal_temperature` | `faithfulness`, `answer_relevance` |
| `maintenance_recommendation` | `faithfulness`, `answer_relevance`, `context_precision` |
| `operational_problem_summary` | `answer_relevance` |
| `out_of_limits` | `faithfulness`, `answer_relevance` |
| `recent_events` | `faithfulness`, `answer_relevance` |

## Casos evaluados solo con checks deterministas

Estos casos siguen siendo importantes, pero no necesitan juez semantico en cada corrida normal:

- `adversarial`
- `ask_inexistent_machine`
- `followup_events_after_status`
- `high_vibration_advice`
- `missing_variable_trend`
- `rag_source_request`
- `stop_criteria`
- `temperature_trend`
- `tool_free_domain_guard`
- `verify_failure_actions`

La razon es que su valor principal se verifica por uso/no uso de tools, respuesta valida y ausencia de error. Se pueden auditar manualmente o correr con `JUDGE_MODE=all` antes del informe final.

## Modos de ejecucion

Corrida recomendada:

```bash
python -m tests
```

Corrida sin juez LLM:

```bash
JUDGE_MODE=off python -m tests
```

Corrida exhaustiva:

```bash
JUDGE_MODE=all python -m tests
```

Segundo juez configurable:

```bash
SECOND_JUDGE_LLM_MODEL=otro/modelo python -m tests
```

Timeout opcional por metrica, solo para diagnostico:

```bash
JUDGE_METRIC_TIMEOUT_SECONDS=120 python -m tests
```

Por defecto no hay timeout externo (`0`) para permitir corridas diagnosticas completas.

## Recomendacion

Usar `JUDGE_MODE=selected` para desarrollo normal y reservar `JUDGE_MODE=all` para una corrida final con un modelo/proveedor con cuota suficiente. Si la cuota gratuita es limitada, `JUDGE_MODE=selected` ofrece el mejor balance entre cobertura y costo.
