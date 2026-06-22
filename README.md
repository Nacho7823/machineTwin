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
```

En esta configuracion `LLM_API_KEY` puede quedar vacio.

Para cambiar a otro proveedor compatible con OpenAI, editar `.env` y ajustar:

- `LLM_BASE_URL`: URL base del proveedor.
- `LLM_MODEL`: modelo a utilizar.
- `LLM_API_KEY`: API key del proveedor, si corresponde.

## Ejecucion del simulador

El simulador debe correr en una terminal separada desde la raiz del proyecto:

```bash
python simulator/main.py 2
```

El argumento `2` indica el intervalo de actualizacion en segundos. Mientras el simulador esta activo, actualiza los archivos de la carpeta `data/`.

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

## Uso en terminal

Tambien se puede usar el agente desde la terminal:

```bash
python main.py
```

Para que las consultas tengan datos actuales, mantener el simulador corriendo en otra terminal.

## Datos generados

El simulador y la aplicacion generan archivos locales para consultar estado, historiales, eventos y trazas:

- `data/machine_current.json`: estado actual de la maquina y variables medidas.
- `data/operation_history.csv`: historial de operacion de las variables.
- `data/event_history.csv`: historial de eventos, alertas, fallas y mantenimientos.
- `logs/app.log`: logs generales de la aplicacion.
- `logs/traces.jsonl`: trazas de ejecucion del agente y sus pasos.

Los documentos tecnicos usados por el RAG estan en `docs-machines/`.

## Tools disponibles

El agente expone estas tools publicas:

- `consultar_documentacion`: consulta la documentacion tecnica con RAG.
- `obtener_estado_actual`: devuelve el estado operativo actual y las variables medidas.
- `consultar_eventos_recientes`: lista eventos recientes desde `data/event_history.csv`.
- `detectar_fuera_de_limites`: detecta variables fuera de rangos optimos u operativos.
- `analizar_tendencia`: analiza la tendencia reciente de una variable.
- `listar_archivos_datos`: lista archivos disponibles en `data/`.
- `leer_archivo_datos`: lee un archivo especifico de `data/`.

## Observabilidad

La aplicacion registra informacion de ejecucion en `logs/app.log`. Las trazas del agente se guardan en `logs/traces.jsonl`, en formato JSON Lines, para revisar interacciones, pasos y uso de tools.

Estos archivos ayudan a evaluar el comportamiento durante las pruebas manuales y a diagnosticar errores de configuracion, datos faltantes o fallas de ejecucion.

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
