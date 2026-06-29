# MachineTwin

MachineTwin es un gemelo digital para maquinas industriales. El proyecto incluye un simulador que genera datos operativos, un agente con tools para consultar documentacion y datos, una interfaz web y una interfaz de terminal.

## Instalacion

Crear y activar un entorno virtual desde la raiz del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para preparar el frontend se necesita Node.js y npm:

```bash
cd frontend
npm install
npm run build
cd ..
```

## Configuracion de variables de entorno

Copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

La aplicacion usa LangChain con un proveedor compatible con OpenAI. La configuracion actual usa NVIDIA NIM:

```env
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=nvidia/nemotron-3-super-120b-a12b
LLM_API_KEY=
LLM_TEMPERATURE=1
LLM_TOP_P=0.95
LLM_MAX_TOKENS=16384
LLM_TIMEOUT=120
LLM_MAX_RETRIES=0
LLM_ENABLE_THINKING=true
LLM_REASONING_BUDGET=16384
SYSTEM_PROMPT_VERSION=0.0.1
SYSTEM_PROMPT_PATH=
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

En esta configuracion `LLM_API_KEY` debe contener una API key valida de NVIDIA. La configuracion anterior de Kilo AI puede conservarse comentada en `.env` para volver atras rapidamente.

Modelo alternativo probado para comparaciones mas livianas:

```env
LLM_MODEL=meta/llama-3.3-70b-instruct
LLM_TEMPERATURE=0.2
LLM_TOP_P=0.7
LLM_MAX_TOKENS=1024
LLM_TIMEOUT=120
LLM_MAX_RETRIES=0
LLM_ENABLE_THINKING=false
LLM_REASONING_BUDGET=0
```

Para cambiar a otro proveedor compatible con OpenAI, editar `.env` y ajustar:

- `LLM_BASE_URL`: URL base del proveedor.
- `LLM_MODEL`: modelo a utilizar.
- `LLM_API_KEY`: API key del proveedor, si corresponde.
- `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_TOKENS`: parametros de generacion.
- `LLM_TIMEOUT`, `LLM_MAX_RETRIES`: control de espera y reintentos del cliente.
- `LLM_ENABLE_THINKING`, `LLM_REASONING_BUDGET`: parametros especificos para modelos NVIDIA con razonamiento.
- `SYSTEM_PROMPT_VERSION`: version funcional del system prompt usada en trazas y reportes.
- `SYSTEM_PROMPT_PATH`: ruta explicita opcional del system prompt. Si se define, tiene prioridad sobre `SYSTEM_PROMPT_VERSION`.
- `WEB_HOST` y `WEB_PORT`: host y puerto del backend web.

El prompt activo se resuelve en este orden:

1. Si `SYSTEM_PROMPT_PATH` esta definido, se usa ese archivo.
2. Si no, se busca `config/prompts/systemprompt-{SYSTEM_PROMPT_VERSION}.md`.
3. Si no existe esa version, se usa el fallback historico `config/systemprompt.md`.

Las copias historicas versionadas se guardan en `config/prompts/`, por ejemplo `config/prompts/systemprompt-0.0.1.md`. Para crear una nueva version, agregar un archivo como `config/prompts/systemprompt-0.0.2.md` y configurar `SYSTEM_PROMPT_VERSION=0.0.2`.

Para persistir memoria conversacional y trazas en PostgreSQL, configurar:

```env
POSTGRES_DB=machinetwin
POSTGRES_USER=machinetwin
POSTGRES_PASSWORD=machinetwin
POSTGRES_PORT=5433
DATABASE_URL=postgresql://machinetwin:machinetwin@localhost:5433/machinetwin
```

Si `DATABASE_URL` no esta definido, la aplicacion usa memoria en proceso para desarrollo local.

## Base de datos PostgreSQL

La entrega final usa PostgreSQL como persistencia principal para conversaciones, mensajes y trazas. Para levantar una base local portable con Docker:

```bash
docker compose up -d postgres
```

Con `.env` configurado, aplicar las migraciones antes de iniciar la app:

```bash
python -m db migrate
```

Para revisar el estado de migraciones:

```bash
python -m db status
```

Para borrar las tablas de desarrollo y volver a migrar desde cero:

```bash
python -m db reset --yes
python -m db migrate
```

La aplicacion no crea el esquema automaticamente al iniciar: si falta una tabla, muestra un error indicando que se debe ejecutar `python -m db migrate`. Esto evita que el esquema de entrega dependa de efectos laterales ocultos.

## Ejecucion del simulador

El simulador debe correr en una terminal separada desde la raiz del proyecto:

```bash
python simulator/main.py 2
```

El argumento `2` indica el intervalo de actualizacion en segundos. Mientras el simulador esta activo, crea una subcarpeta por cada maquina definida en `simulator/machine_configs.py` y actualiza sus archivos dentro de `data/`.

## Ejecucion de la aplicacion web

La aplicacion web debe correr en otra terminal, separada del simulador.

Primero compilar el frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Luego iniciar el backend web desde la raiz del proyecto:

```bash
python main.py web
```

La app web queda disponible en:

```text
http://localhost:8000
```

La interfaz incluye dos vistas:

- `Chat`: conversacion principal con el agente.
- `Trazas`: inspeccion de conversaciones persistidas, mensajes, eventos y tools ejecutadas.

## Uso en terminal

Tambien se puede usar el agente desde la terminal:

```bash
python main.py
```

Para que las consultas tengan datos actuales, mantener el simulador corriendo en otra terminal.

## Datos generados

El simulador y la aplicacion generan archivos locales para consultar estado, historiales, eventos y trazas. Cada maquina escribe sus datos en `data/<machine_key>/`:

- `data/cooling_tower/machine_current.json`: estado actual de la maquina y variables medidas.
- `data/cooling_tower/operation_history.csv`: historial de operacion de las variables.
- `data/cooling_tower/event_history.csv`: historial de eventos, alertas, fallas y mantenimientos.
- `data/electric_motor/...`: archivos equivalentes para el motor.
- `data/compressor/...`: archivos equivalentes para el compresor.
- `logs/app.log`: logs generales de la aplicacion.
- `logs/traces.jsonl`: trazas de ejecucion del agente y sus pasos.

Si se agregan nuevas maquinas en `MACHINE_CONFIGS`, el simulador genera automaticamente una subcarpeta con esa key. Las tools tambien mantienen compatibilidad basica con archivos legacy directamente en `data/`.

Los documentos tecnicos usados por el RAG estan en `docs-machines/`.

## Tools disponibles

El agente expone estas tools publicas:

- `consultar_documentacion`: consulta la documentacion tecnica con RAG.
- `obtener_estado_actual`: devuelve el estado operativo actual y las variables medidas de todas las maquinas detectadas.
- `consultar_eventos_recientes`: lista eventos recientes combinados desde las maquinas detectadas.
- `detectar_fuera_de_limites`: detecta variables fuera de rangos optimos u operativos por maquina.
- `analizar_tendencia`: analiza la tendencia reciente de una variable por maquina cuando existe en su historial. Usa 50 muestras por defecto y acepta una ventana solicitada hasta un maximo de 200 muestras.
- `listar_archivos_datos`: lista archivos disponibles en `data/`.
- `leer_archivo_datos`: lee un archivo especifico de `data/`.

## Observabilidad

La aplicacion registra informacion de ejecucion en `logs/app.log`. Las trazas del agente se guardan en `logs/traces.jsonl`, en formato JSON Lines, para revisar interacciones, pasos y uso de tools.

Si hay PostgreSQL configurado, las conversaciones, mensajes y trazas tambien se guardan en base de datos y pueden consultarse desde la vista `Trazas` o desde los endpoints:

- `GET /api/conversations`
- `POST /api/conversations`
- `GET /api/conversations/{conversation_id}`
- `DELETE /api/conversations/{conversation_id}`
- `GET /api/traces`
- `GET /api/traces/{conversation_id}`

`POST /api/clear` limpia la memoria persistida de la conversacion activa cuando recibe `conversation_id`.

Estos registros ayudan a evaluar el comportamiento durante las pruebas manuales y a diagnosticar errores de configuracion, datos faltantes o fallas de ejecucion.

Las trazas incluyen metadata de auditoria: `conversation_id`, `trace_id`, modelo LLM, `System Prompt version`, hash del prompt, latencias de LLM/tools, estado final de cada paso y, cuando se consulta documentacion, metadata de chunks RAG recuperados.

## Evidencia de entrega

Para recolectar evidencia reproducible de la entrega final con la app web corriendo:

```bash
python scripts/collect_evidence.py --base-url http://localhost:8000
```

El script guarda salidas de Docker, estado de migraciones y respuestas de endpoints en `docs/evidencia_entrega3/<fecha>/`.

## Casos de prueba

La guia de evaluacion manual esta en:

```text
docs/casos_prueba.md
```

Usar esos casos con el simulador corriendo y, segun corresponda, con la aplicacion web o la interfaz de terminal.

## Estructura del proyecto

- `main.py`: punto de entrada del agente, modo terminal y modo web.
- `uiWeb.py`: backend de la interfaz web.
- `uiTerminal.py`: interfaz de terminal.
- `tools.py`: tools del agente para RAG, estado, eventos, analisis y archivos.
- `llm.py`: configuracion del cliente LLM.
- `config.py`: configuracion general de rutas y variables de entorno.
- `log.py`: configuracion de logs.
- `utils.py`: utilidades compartidas.
- `frontend/`: interfaz web del chatbot.
- `simulator/`: simulador de maquinas y configuraciones.
- `rag/`: implementacion del RAG.
- `docs-machines/`: documentacion tecnica de maquinas usada por el RAG.
- `docs/casos_prueba.md`: casos de prueba manuales para la Entrega 2.
- `data/`: archivos generados por el simulador.
- `logs/`: logs y trazas generadas por la aplicacion.


## Tests
En la carpeta tests hay un benchmark, este usa los datos de las carpetas en tests/files/*  

para correr los tests:
```bash
python -m tests
```

La corrida por defecto mantiene compatibilidad con `JUDGE_MODE=selected`: ejecuta los 20 casos, aplica checks deterministas a todos y solo usa LLM-as-a-judge en los casos/metricas declarados con `judge_metrics` dentro de cada `tests/files/*/test.json`.

Para controlar mejor costo y duracion, se recomienda usar `TEST_PROFILE`:

- `functional`: ejecuta los 20 casos con checks deterministas, sin LLM-as-a-judge.
- `semantic`: ejecuta los 20 casos y usa juez solo en casos representativos con metricas utiles por caso. Es el perfil recomendado para comparar modelos y versiones de prompt.
- `rag_full`: ejecuta solo casos RAG/documentacion y calcula las cuatro metricas.
- `exhaustive`: ejecuta los 20 casos con las cuatro metricas. Es costoso y queda como corrida experimental.

Ejemplo recomendado:

```bash
TEST_PROFILE=semantic python -m tests
```

Para correr sin LLM-as-a-judge usando el modo legacy:

```bash
JUDGE_MODE=off python -m tests
```

Para correr una evaluacion exhaustiva con las cuatro metricas en todos los casos:

```bash
TEST_PROFILE=exhaustive python -m tests
```

La evaluacion exhaustiva puede consumir muchas llamadas al modelo y agotar limites gratuitos. `TEST_PROFILE`, cuando esta definido, tiene prioridad sobre `JUDGE_MODE`. El modelo juez usa la misma configuracion que el agente por defecto. Tambien se puede configurar un segundo juez:

```bash
SECOND_JUDGE_LLM_MODEL=otro/modelo python -m tests
```

Cada corrida guarda un reporte JSON en `tests/reports/` con metricas por caso, promedios y porcentaje de aprobacion. El reporte incluye modelo del agente, juez principal, segundo juez opcional, `test_profile`, `System Prompt version` y hash del prompt para comparar corridas.
