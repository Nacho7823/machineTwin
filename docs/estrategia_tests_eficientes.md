# Estrategia eficiente de tests automaticos

## Objetivo

Mantener cobertura funcional sobre los 19 casos de `tests/files/*` reduciendo consumo de cuota LLM y duracion total. La prioridad es gastar menos llamadas del modelo; la segunda prioridad es reducir tiempo de corrida.

## Metricas usadas

La evaluacion LLM-as-a-judge usa tres metricas:

- `faithfulness`
- `answer_relevance`
- `context_precision`

La suite descarta metricas que resultaron costosas o poco estables para esta entrega.

## Estrategia aplicada

Se separan dos niveles de evaluacion:

1. Checks deterministas para todos los casos:
   - respuesta no vacia;
   - respuesta sin error de proveedor;
   - tools esperadas usadas.

2. LLM-as-a-judge solo cuando aporta valor:
   - `TEST_PROFILE=semantic_rag` ejecuta los 19 casos y juzga casos semanticos y RAG/documentacion representativos;
   - `TEST_PROFILE=exhaustive` ejecuta los 19 casos con las tres metricas.

## Casos con LLM-as-a-judge en semantic_rag

| Caso | Metricas |
|---|---|
| `current_status` | `faithfulness`, `answer_relevance` |
| `documented_operation` | `faithfulness`, `answer_relevance`, `context_precision` |
| `high_vibration_advice` | `faithfulness`, `answer_relevance`, `context_precision` |
| `maintenance_recommendation` | `faithfulness`, `answer_relevance`, `context_precision` |
| `operational_problem_summary` | `answer_relevance` |
| `out_of_limits` | `faithfulness`, `answer_relevance` |
| `rag_source_request` | `faithfulness`, `answer_relevance`, `context_precision` |
| `recent_events` | `faithfulness`, `answer_relevance` |
| `stop_criteria` | `faithfulness`, `answer_relevance`, `context_precision` |
| `verify_failure_actions` | `faithfulness`, `answer_relevance`, `context_precision` |

Los demas casos se evaluan por checks deterministas en la corrida semantica + RAG.

## Modos de ejecucion

Corrida funcional sin juez:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=functional .venv/bin/python -m tests
```

Corrida recomendada:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=semantic_rag JUDGE_METRIC_TIMEOUT_SECONDS=0 .venv/bin/python -m tests
```

Corrida exhaustiva:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=exhaustive JUDGE_METRIC_TIMEOUT_SECONDS=0 .venv/bin/python -m tests
```

Segundo juez configurable:

```bash
SECOND_JUDGE_LLM_MODEL=otro/modelo SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=semantic_rag .venv/bin/python -m tests
```

## Recomendacion

Usar `TEST_PROFILE=semantic_rag` para comparar versiones del prompt y modelos. Reservar `TEST_PROFILE=exhaustive` para una corrida final si hay cuota suficiente.
