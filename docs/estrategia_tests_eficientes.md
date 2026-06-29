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
   - `TEST_PROFILE=semantic` ejecuta los 19 casos y juzga solo casos representativos;
   - `TEST_PROFILE=rag_full` ejecuta solo casos RAG/documentacion con las tres metricas;
   - `TEST_PROFILE=exhaustive` ejecuta los 19 casos con las tres metricas.

## Casos con LLM-as-a-judge en semantic

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

Los demas casos se evaluan por checks deterministas en la corrida semantica.

## Modos de ejecucion

Corrida funcional sin juez:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=functional .venv/bin/python -m tests
```

Corrida recomendada:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=semantic JUDGE_METRIC_TIMEOUT_SECONDS=0 .venv/bin/python -m tests
```

Corrida RAG/documentacion completa:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=rag_full JUDGE_METRIC_TIMEOUT_SECONDS=0 .venv/bin/python -m tests
```

Corrida exhaustiva:

```bash
SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=exhaustive JUDGE_METRIC_TIMEOUT_SECONDS=0 .venv/bin/python -m tests
```

Segundo juez configurable:

```bash
SECOND_JUDGE_LLM_MODEL=otro/modelo SYSTEM_PROMPT_VERSION=0.0.2 TEST_PROFILE=semantic .venv/bin/python -m tests
```

## Recomendacion

Usar `TEST_PROFILE=semantic` para comparar versiones del prompt y modelos. Reservar `TEST_PROFILE=rag_full` para diagnosticar calidad de recuperacion documental y `TEST_PROFILE=exhaustive` para una corrida final si hay cuota suficiente.
