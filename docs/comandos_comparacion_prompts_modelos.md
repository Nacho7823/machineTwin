# Comandos para comparar modelos y versiones de system prompt

Este documento deja preparados los comandos para ejecutar la suite completa de 20 casos con `JUDGE_MODE=all`, es decir, usando las cuatro metricas de LLM-as-judge en todos los tests:

- `faithfulness`
- `answer_relevance`
- `context_precision`
- `context_recall`

La comparacion propuesta cruza dos modelos contra dos versiones del system prompt:

- Modelo principal: `nvidia/nemotron-3-super-120b-a12b`
- Modelo alternativo: `meta/llama-3.3-70b-instruct`
- Prompt baseline: `0.0.1`
- Prompt experimental: `0.0.2`

Los comandos no incluyen `LLM_API_KEY`; usan la key configurada localmente en `.env`.

## Preparacion previa

Ejecutar una vez antes de las cuatro corridas:

```bash
docker compose up -d postgres
.venv/bin/python -m db migrate
mkdir -p logs/test-runs
set -o pipefail
```

## 1. Nemotron Super + system prompt 0.0.1

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.1 \
  SYSTEM_PROMPT_PATH= \
  JUDGE_MODE=all \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=nvidia/nemotron-3-super-120b-a12b \
  LLM_TEMPERATURE=1 \
  LLM_TOP_P=0.95 \
  LLM_MAX_TOKENS=16384 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=true \
  LLM_REASONING_BUDGET=16384 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/nemotron-super_prompt-0.0.1_all.log
```

## 2. Nemotron Super + system prompt 0.0.2

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.2 \
  SYSTEM_PROMPT_PATH= \
  JUDGE_MODE=all \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=nvidia/nemotron-3-super-120b-a12b \
  LLM_TEMPERATURE=1 \
  LLM_TOP_P=0.95 \
  LLM_MAX_TOKENS=16384 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=true \
  LLM_REASONING_BUDGET=16384 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/nemotron-super_prompt-0.0.2_all.log
```

## 3. Llama 3.3 70B + system prompt 0.0.1

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.1 \
  SYSTEM_PROMPT_PATH= \
  JUDGE_MODE=all \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=meta/llama-3.3-70b-instruct \
  LLM_TEMPERATURE=0.2 \
  LLM_TOP_P=0.7 \
  LLM_MAX_TOKENS=1024 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=false \
  LLM_REASONING_BUDGET=0 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/llama-3.3-70b_prompt-0.0.1_all.log
```

## 4. Llama 3.3 70B + system prompt 0.0.2

```bash
time env \
  SYSTEM_PROMPT_VERSION=0.0.2 \
  SYSTEM_PROMPT_PATH= \
  JUDGE_MODE=all \
  JUDGE_METRIC_TIMEOUT_SECONDS=0 \
  LLM_MODEL=meta/llama-3.3-70b-instruct \
  LLM_TEMPERATURE=0.2 \
  LLM_TOP_P=0.7 \
  LLM_MAX_TOKENS=1024 \
  LLM_TIMEOUT=180 \
  LLM_MAX_RETRIES=0 \
  LLM_ENABLE_THINKING=false \
  LLM_REASONING_BUDGET=0 \
  .venv/bin/python -m tests 2>&1 | tee logs/test-runs/llama-3.3-70b_prompt-0.0.2_all.log
```

## Notas de interpretacion

- Cada corrida genera un reporte JSON nuevo en `tests/reports/`.
- El reporte guarda `agent_model`, `judge_model`, `judge_mode`, `System Prompt version` y `prompt_hash`, por lo que se puede identificar que combinacion produjo cada resultado.
- Con `JUDGE_MODE=all`, todos los casos intentan calcular las cuatro metricas, incluso si algunas metricas son menos naturales para casos puramente operativos.
- `JUDGE_METRIC_TIMEOUT_SECONDS=0` desactiva el timeout externo del runner. Si una corrida queda demasiado lenta, se puede repetir con un limite, por ejemplo `JUDGE_METRIC_TIMEOUT_SECONDS=180`.
- `LLM_TIMEOUT=180` controla el timeout por llamada al proveedor. Si el proveedor tarda mas que eso por request, la llamada puede fallar aunque el runner no tenga timeout externo.
