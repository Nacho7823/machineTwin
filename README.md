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

La aplicacion usa LangChain con un proveedor compatible con OpenAI. La configuracion por defecto usa Kilo AI:

```env
LLM_BASE_URL=https://api.kilo.ai/api/gateway/
LLM_MODEL=stepfun/step-3.7-flash:free
LLM_API_KEY=
PROMPT_VERSION=entrega3-v1
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

En esta configuracion `LLM_API_KEY` puede quedar vacio.

Para cambiar a otro proveedor compatible con OpenAI, editar `.env` y ajustar:

- `LLM_BASE_URL`: URL base del proveedor.
- `LLM_MODEL`: modelo a utilizar.
- `LLM_API_KEY`: API key del proveedor, si corresponde.
- `PROMPT_VERSION`: version funcional del system prompt usada en trazas y reportes.
- `WEB_HOST` y `WEB_PORT`: host y puerto del backend web.

Para persistir memoria conversacional y trazas en PostgreSQL, configurar:

```env
POSTGRES_DB=machinetwin
POSTGRES_USER=machinetwin
POSTGRES_PASSWORD=machinetwin
POSTGRES_PORT=5432
DATABASE_URL=postgresql://machinetwin:machinetwin@localhost:5432/machinetwin
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

Las trazas incluyen metadata de auditoria: `conversation_id`, `trace_id`, modelo LLM, `prompt_version`, hash del prompt, latencias de LLM/tools, estado final de cada paso y, cuando se consulta documentacion, metadata de chunks RAG recuperados.

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

Se usa LLM-as-a-judge. el modelo esta definido en benchmarks.py.
Se debe cambiar el modelo para obtener resultados no sesgados. Tambien se puede configurar un segundo juez:

```bash
SECOND_JUDGE_LLM_MODEL=otro/modelo python -m tests
```

Cada corrida guarda un reporte JSON en `tests/reports/` con metricas por caso, promedios y porcentaje de aprobacion. El reporte incluye modelo del agente, juez principal, segundo juez opcional, `prompt_version` y hash del prompt para comparar corridas.
