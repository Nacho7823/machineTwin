# Comandos para comparar modelos y versiones de system prompt

Este documento deja preparados los comandos para comparar dos modelos contra dos versiones del system prompt sin ejecutar el modo mas costoso en todos los casos.

La estrategia recomendada usa `TEST_PROFILE=semantic`:

- Ejecuta los 19 casos automatizados.
- Mantiene checks deterministas en todos los casos: respuesta no vacia, errores de agente y tools esperadas.
- Usa LLM-as-a-judge solo en casos representativos.
- Usa solo las metricas que aportan valor por tipo de caso.

Esto permite comparar resultados entre modelos y prompts con mucho menos consumo que `TEST_PROFILE=exhaustive`, que calcula las tres metricas en los 19 casos.

## Perfiles disponibles

- `TEST_PROFILE=functional`: 19 casos sin LLM-as-a-judge. Sirve como smoke test rapido de tools, flujo y respuestas no vacias.
- `TEST_PROFILE=semantic`: 19 casos con juez selectivo. Es el perfil recomendado para la comparacion principal.
- `TEST_PROFILE=rag_full`: solo casos RAG/documentacion con las tres metricas.
- `TEST_PROFILE=exhaustive`: 19 casos con las tres metricas. Es una corrida pesada y experimental.

Cuando `TEST_PROFILE` esta definido, tiene prioridad sobre `JUDGE_MODE`. El reporte JSON guarda `test_profile`, `agent_model`, `judge_model`, `System Prompt version` y `prompt_hash`.

## Casos juzgados en semantic

En `TEST_PROFILE=semantic`, los 19 casos se ejecutan, pero solo estos usan juez:

- `current_status`: `faithfulness`, `answer_relevance`
- `documented_operation`: `faithfulness`, `answer_relevance`, `context_precision`
- `high_vibration_advice`: `faithfulness`, `answer_relevance`, `context_precision`
- `maintenance_recommendation`: `faithfulness`, `answer_relevance`, `context_precision`
- `operational_problem_summary`: `answer_relevance`
- `out_of_limits`: `faithfulness`, `answer_relevance`
- `rag_source_request`: `faithfulness`, `answer_relevance`, `context_precision`
- `recent_events`: `faithfulness`, `answer_relevance`

Los demas casos quedan evaluados por checks deterministas. Esto cubre seguridad de dominio, memoria conversacional, uso de tools, respuestas no vacias y flujo funcional sin gastar llamadas adicionales del juez.

## Casos incluidos en rag_full

`TEST_PROFILE=rag_full` ejecuta solo estos casos, todos con las tres metricas:

- `documented_operation`
- `maintenance_recommendation`
- `rag_source_request`
- `stop_criteria`
- `verify_failure_actions`

## Preparacion previa

Ejecutar una vez antes de las cuatro corridas:

```bash
docker compose up -d postgres
.venv/bin/python -m db migrate
mkdir -p logs/test-runs
set -o pipefail
```

Los comandos no incluyen `LLM_API_KEY`; usan la key configurada localmente en `.env`.

## 1. Nemotron Super + system prompt 0.0.1

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.1 \
  SYSTEM_PROMPT_PATH= \
  TEST_PROFILE=semantic \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=nvidia/nemotron-3-super-120b-a12b \
  LLM_TEMPERATURE=1 \
  LLM_TOP_P=0.95 \
  LLM_MAX_TOKENS=16384 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=true \
  LLM_REASONING_BUDGET=16384 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/nemotron-super_prompt-0.0.1_semantic.log
```

## 2. Nemotron Super + system prompt 0.0.2

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.2 \
  SYSTEM_PROMPT_PATH= \
  TEST_PROFILE=semantic \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=nvidia/nemotron-3-super-120b-a12b \
  LLM_TEMPERATURE=1 \
  LLM_TOP_P=0.95 \
  LLM_MAX_TOKENS=16384 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=true \
  LLM_REASONING_BUDGET=16384 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/nemotron-super_prompt-0.0.2_semantic.log
```

## 3. Llama 3.3 70B + system prompt 0.0.1

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.1 \
  SYSTEM_PROMPT_PATH= \
  TEST_PROFILE=semantic \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=meta/llama-3.3-70b-instruct \
  LLM_TEMPERATURE=0.2 \
  LLM_TOP_P=0.7 \
  LLM_MAX_TOKENS=1024 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=false \
  LLM_REASONING_BUDGET=0 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/llama-3.3-70b_prompt-0.0.1_semantic.log
```

## 4. Llama 3.3 70B + system prompt 0.0.2

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.2 \
  SYSTEM_PROMPT_PATH= \
  TEST_PROFILE=semantic \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=meta/llama-3.3-70b-instruct \
  LLM_TEMPERATURE=0.2 \
  LLM_TOP_P=0.7 \
  LLM_MAX_TOKENS=1024 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=false \
  LLM_REASONING_BUDGET=0 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/llama-3.3-70b_prompt-0.0.2_semantic.log
```

## Corridas complementarias opcionales

Para revisar rapidamente que los 19 casos siguen funcionando sin gastar juez:

```bash
TEST_PROFILE=functional .venv/bin/python -m tests
```

Para profundizar solo los casos de documentacion/RAG con las tres metricas:

```bash
TEST_PROFILE=rag_full .venv/bin/python -m tests
```

Para repetir la suite completa con las tres metricas en todos los casos:

```bash
TEST_PROFILE=exhaustive .venv/bin/python -m tests
```

## Notas de interpretacion

- `semantic` es el perfil principal para comparar prompts y modelos: todos los casos se ejecutan, pero no todos consumen juez.
- Los casos sin juez se evaluan con checks deterministas: respuesta no vacia, ausencia de errores de agente y uso de tools esperadas.
- `rag_full` sirve para mirar con mas detalle si el agente esta recuperando y usando bien la documentacion tecnica.
- `JUDGE_METRIC_TIMEOUT_SECONDS=0` desactiva el timeout externo del runner. El timeout por llamada al proveedor queda controlado por `LLM_TIMEOUT`.
- Cada corrida genera un reporte JSON nuevo en `tests/reports/`.
